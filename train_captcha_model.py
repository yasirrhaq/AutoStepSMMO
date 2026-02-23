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
    
    def __init__(self, captcha_learning_dir: str, labels_file: str, processor):
        self.captcha_dir = Path(captcha_learning_dir)
        self.processor = processor
        
        # Load labels
        with open(labels_file, 'r') as f:
            self.labels = json.load(f)
        
        # Build dataset
        self.samples = []
        for attempt_folder, label_data in self.labels.items():
            folder_path = self.captcha_dir / attempt_folder
            if not folder_path.exists():
                continue
            
            correct_button = label_data['correct_button']
            question = label_data['question']
            
            # Load all button images
            for button_idx in range(1, 5):
                img_path = folder_path / f"button_{button_idx}.png"
                if img_path.exists():
                    # Label: 1 if this is correct button, 0 if wrong
                    is_correct = 1.0 if button_idx == correct_button else 0.0
                    
                    self.samples.append({
                        'image_path': str(img_path),
                        'question': question,
                        'label': is_correct,
                        'button_idx': button_idx
                    })
        
        print(f"Loaded {len(self.samples)} training samples from {len(self.labels)} attempts")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load image
        image = Image.open(sample['image_path']).convert('RGB')
        
        # Process image and text
        inputs = self.processor(
            text=[f"a {sample['question']}"],
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        return {
            'pixel_values': inputs['pixel_values'].squeeze(0),
            'input_ids': inputs['input_ids'].squeeze(0),
            'attention_mask': inputs['attention_mask'].squeeze(0),
            'label': torch.tensor(sample['label'], dtype=torch.float)
        }


def train_model(
    captcha_learning_dir="captcha_learning",
    labels_file="captcha_learning/labels.json",
    output_dir="models/clip-captcha-finetuned",
    epochs=10,
    batch_size=4,
    learning_rate=1e-5
):
    """Train the CLIP model on labeled CAPTCHA data"""
    
    print("="*60)
    print("🤖 CAPTCHA Model Training")
    print("="*60)
    
    # Check if labels file exists
    if not os.path.exists(labels_file):
        print(f"\n❌ Labels file not found: {labels_file}")
        print("\nYou need to create labels.json first!")
        print("Run: python label_captcha_attempts.py")
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
    dataset = CaptchaDataset(captcha_learning_dir, labels_file, processor)
    
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
            
            # Calculate similarity (logits)
            logits = outputs.logits_per_image.squeeze()
            
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
    
    # Check if labels file exists
    if not os.path.exists("captcha_learning/labels.json"):
        print("="*60)
        print("⚠️  No labels.json found!")
        print("="*60)
        print("\nBefore training, you need to label your saved attempts.")
        print("This tells the AI which button was correct for each CAPTCHA.\n")
        print("Run the labeling tool:")
        print("  python label_captcha_attempts.py\n")
        print("Or manually create captcha_learning/labels.json:")
        print("""
{
  "attempt_20260223_041233": {
    "question": "Cherry",
    "correct_button": 3
  },
  "attempt_20260223_041548": {
    "question": "Strawberry",
    "correct_button": 1
  }
}
""")
        sys.exit(1)
    
    # Train model
    success = train_model(
        captcha_learning_dir="captcha_learning",
        labels_file="captcha_learning/labels.json",
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
