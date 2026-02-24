#!/usr/bin/env python3
"""
CAPTCHA AI Model Training Script

This script fine-tunes the CLIP model using your saved wrong attempts.

STEPS:
1. Label your saved attempts (mark which button was correct)
2. Run this script to train the model
3. Bot will automatically use the improved model

Requirements:
    pip install torch transformers pillow
"""

import json
import os
from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
from tqdm import tqdm
import numpy as np

class CaptchaDataset(Dataset):
    """Dataset for CAPTCHA training — 4-way ranking per attempt.
    
    Each sample is one complete CAPTCHA attempt: 4 button images + question.
    The label is the 0-based index of the correct button (0-3).
    This matches how CLIP is actually used at inference time.
    """
    
    def __init__(self, captcha_learning_dir: str, processor):
        self.captcha_dir = Path(captcha_learning_dir)
        self.processor = processor
        self.samples = []
        
        # Scan both successes/ and failures/ for labeled attempts
        for subdir in ['successes', 'failures']:
            dir_path = self.captcha_dir / subdir
            if not dir_path.exists():
                continue
            
            for attempt_folder in dir_path.iterdir():
                if not attempt_folder.is_dir():
                    continue
                
                metadata_file = attempt_folder / 'metadata.json'
                if not metadata_file.exists():
                    continue
                
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except Exception:
                    continue
                
                correct_button = metadata.get('correct_answer')  # 1-based
                if correct_button is None:
                    continue  # Skip unlabeled
                
                question = metadata.get('question', '')
                
                # Load all 4 button images for this attempt
                images = []
                for btn_idx in range(1, 5):
                    img_path = attempt_folder / f'button_{btn_idx}.png'
                    if img_path.exists():
                        images.append(str(img_path))
                
                if len(images) == 4:  # Only keep complete attempts
                    self.samples.append({
                        'image_paths': images,        # list of 4 paths
                        'question':    question,
                        'correct_idx': correct_button - 1,  # 0-based
                    })
        
        print(f"Loaded {len(self.samples)} complete labeled attempts (4-way ranking)")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load all 4 images
        images = [Image.open(p).convert('RGB') for p in sample['image_paths']]
        
        # Process all 4 images with the question text at once.
        # We repeat the same text 4 times so CLIP produces a [4 x 4] similarity
        # matrix; we extract the [4 x 1] first column (same text for all images).
        texts = [f"a {sample['question'].lower()}"] * 4
        inputs = self.processor(
            text=texts,
            images=images,
            return_tensors='pt',
            padding='max_length',
            truncation=True,
            max_length=77,
        )
        
        return {
            'pixel_values':   inputs['pixel_values'],          # [4, C, H, W]
            'input_ids':      inputs['input_ids'],             # [4, seq_len]
            'attention_mask': inputs['attention_mask'],        # [4, seq_len]
            'correct_idx':    torch.tensor(sample['correct_idx'], dtype=torch.long),
        }


def train_model(
    captcha_learning_dir="captcha_learning",
    output_dir="models/clip-captcha-finetuned",
    epochs=10,
    batch_size=4,
    learning_rate=1e-5
):
    """Train the CLIP model on labeled CAPTCHA data"""
    
    print("="*60)
    print("🤖 CAPTCHA Model Training")
    print("="*60)
    
    # Check that at least one labeled attempt exists
    captcha_path = Path(captcha_learning_dir)
    has_data = False
    for subdir in ['successes', 'failures']:
        d = captcha_path / subdir
        if d.exists() and any(d.iterdir()):
            has_data = True
            break
    
    if not has_data:
        print(f"\n❌ No captcha learning data found in: {captcha_learning_dir}")
        print("The bot needs to run first so it can collect CAPTCHA attempts.")
        return False
    
    # Load processor and model
    print("\n📦 Loading CLIP model...")
    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    
    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️  Using device: {device}")
    model = model.to(device)
    
    # Create dataset
    print("\n📂 Loading training data...")
    dataset = CaptchaDataset(captcha_learning_dir, processor)
    
    if len(dataset) == 0:
        print("❌ No training data found!")
        return False
    
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Setup optimizer — 4-way ranking cross-entropy loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_fn = torch.nn.CrossEntropyLoss()
    
    # Training loop
    print(f"\n🎯 Training for {epochs} epochs (4-way ranking)...")
    print("="*60)
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch in progress_bar:
            optimizer.zero_grad()
            
            # batch['pixel_values']: [B, 4, C, H, W]  (B attempts, 4 buttons each)
            # batch['input_ids']:     [B, 4, seq_len]
            B = batch['pixel_values'].shape[0]
            
            # Flatten to [B*4, ...] for the CLIP forward pass
            pixel_values  = batch['pixel_values'].view(B * 4, *batch['pixel_values'].shape[2:]).to(device)
            input_ids     = batch['input_ids'].view(B * 4, -1).to(device)
            attention_mask= batch['attention_mask'].view(B * 4, -1).to(device)
            correct_idx   = batch['correct_idx'].to(device)  # [B]
            
            # Forward pass produces similarity matrix [B*4, B*4]
            outputs = model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True,
            )
            
            # logits_per_image shape: [B*4, B*4]
            # For each attempt i, we want logits for buttons 4i..4i+3 vs the
            # single repeated text for that attempt (columns 4i..4i+3 are all
            # identical since we repeated the same text 4 times).
            # Average the 4 text columns -> [B*4, 1] -> reshape -> [B, 4]
            logits_full = outputs.logits_per_image  # [B*4, B*4]
            # Each group of 4 rows belongs to one attempt; average text columns
            logits_4d = logits_full.view(B, 4, B, 4)          # [B, 4_imgs, B, 4_texts]
            # For attempt i, use the i-th text group (same text repeated 4x)
            attempt_logits = torch.stack([
                logits_4d[i, :, i, :].mean(dim=-1)  # [4]
                for i in range(B)
            ])  # [B, 4]
            
            # Cross-entropy over 4 buttons
            loss = loss_fn(attempt_logits, correct_idx)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Stats
            total_loss += loss.item()
            predictions = attempt_logits.argmax(dim=1)
            correct += (predictions == correct_idx).sum().item()
            total += B
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{correct/total*100:.1f}%'
            })
        
        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total * 100
        
        print(f"\nEpoch {epoch+1}: Loss={avg_loss:.4f}, Accuracy={accuracy:.2f}%")
    
    # Save model
    print(f"\n💾 Saving fine-tuned model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    processor.save_pretrained(output_dir)
    
    print("\n✅ Training complete!")
    print(f"\n📝 Model saved to: {output_dir}")
    print("\nThe bot will automatically use this improved model.")
    
    return True


if __name__ == "__main__":
    import sys
    
    # Train model
    success = train_model(
        captcha_learning_dir="captcha_learning",
        output_dir="models/clip-captcha-finetuned",
        epochs=10,  # Increase for better results (may take longer)
        batch_size=4,  # Reduce if you get out-of-memory errors
        learning_rate=1e-5
    )
    
    if success:
        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("="*60)
        print("\nYour bot will now use the improved AI model.")
        print("Test it by running: python quick_test.py")
    else:
        print("\n❌ Training failed. Check error messages above.")
        sys.exit(1)
