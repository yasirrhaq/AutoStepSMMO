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
    """Dataset for CAPTCHA training"""
    
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
                
                metadata_file = attempt_folder / "metadata.json"
                if not metadata_file.exists():
                    continue
                
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except Exception:
                    continue
                
                correct_button = metadata.get("correct_answer")
                if correct_button is None:
                    continue  # Skip unlabeled failures
                
                question = metadata.get("question", "")
                
                # Load all button images for this attempt
                for button_idx in range(1, 5):
                    img_path = attempt_folder / f"button_{button_idx}.png"
                    if img_path.exists():
                        self.samples.append({
                            'image_path': str(img_path),
                            'question': question,
                            'label': 1.0 if button_idx == correct_button else 0.0,
                            'button_idx': button_idx
                        })
        
        labeled_attempts = len(self.samples) // 4 if self.samples else 0
        print(f"Loaded {len(self.samples)} training samples from ~{labeled_attempts} labeled attempts")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load image
        image = Image.open(sample['image_path']).convert('RGB')
        
        # Process image and text — max_length=77 is CLIP's token limit
        inputs = self.processor(
            text=[f"a {sample['question']}"],
            images=image,
            return_tensors="pt",
            padding='max_length',
            truncation=True,
            max_length=77
        )
        
        return {
            'pixel_values': inputs['pixel_values'].squeeze(0),
            'input_ids': inputs['input_ids'].squeeze(0),
            'attention_mask': inputs['attention_mask'].squeeze(0),
            'label': torch.tensor(sample['label'], dtype=torch.float)
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
    
    # Setup optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    
    # Training loop
    print(f"\n🎯 Training for {epochs} epochs...")
    print("="*60)
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch in progress_bar:
            optimizer.zero_grad()
            
            # Move batch to device
            pixel_values = batch['pixel_values'].to(device)
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            
            # Forward pass
            outputs = model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True
            )
            
            # logits_per_image is [B, B] (cross-similarity matrix).
            # Take the diagonal to get per-sample score: similarity(image_i, text_i).
            logits = outputs.logits_per_image.diagonal()
            
            # Calculate loss (we want correct=1, wrong=0)
            loss = loss_fn(logits, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Stats
            total_loss += loss.item()
            predictions = (torch.sigmoid(logits) > 0.5).float()
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
            
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
