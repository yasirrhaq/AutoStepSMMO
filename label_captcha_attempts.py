#!/usr/bin/env python3
"""
CAPTCHA Labeling Tool

Simple GUI to label your saved CAPTCHA attempts.
Mark which button was correct for each attempt.

Requirements:
    pip install pillow tkinter

Usage:
    python label_captcha_attempts.py
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox

class CaptchaLabeler:
    def __init__(self, captcha_dir="captcha_learning"):
        self.captcha_dir = Path(captcha_dir)
        self.labels_file = self.captcha_dir / "labels.json"
        
        # Load existing labels or create new
        if self.labels_file.exists():
            with open(self.labels_file, 'r') as f:
                self.labels = json.load(f)
        else:
            self.labels = {}
        
        # Get all attempt folders
        self.attempts = sorted([
            d.name for d in self.captcha_dir.iterdir()
            if d.is_dir() and d.name.startswith("attempt_")
        ])
        
        # Filter out already labeled
        self.unlabeled = [a for a in self.attempts if a not in self.labels]
        
        self.current_idx = 0
        
        print(f"Total attempts: {len(self.attempts)}")
        print(f"Already labeled: {len(self.labels)}")
        print(f"To label: {len(self.unlabeled)}")
        
        if not self.unlabeled:
            print("\n✅ All attempts are already labeled!")
            print(f"Labels saved in: {self.labels_file}")
            print("\nRun training: python train_captcha_model.py")
            return
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("CAPTCHA Labeling Tool")
        self.root.geometry("900x700")
        
        self.create_widgets()
        self.load_attempt()
        
        # Keyboard shortcuts
        self.root.bind('1', lambda e: self.select_button(1))
        self.root.bind('2', lambda e: self.select_button(2))
        self.root.bind('3', lambda e: self.select_button(3))
        self.root.bind('4', lambda e: self.select_button(4))
        self.root.bind('s', lambda e: self.skip())
        self.root.bind('<Right>', lambda e: self.skip())
        
        self.root.mainloop()
    
    def create_widgets(self):
        """Create GUI widgets"""
        
        # Progress bar
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill='x')
        
        self.progress_label = ttk.Label(
            progress_frame,
            text=f"Progress: 0 / {len(self.unlabeled)}",
            font=('Arial', 12, 'bold')
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            maximum=len(self.unlabeled),
            value=0,
            mode='determinate'
        )
        self.progress_bar.pack(fill='x', pady=5)
        
        # Question
        question_frame = ttk.Frame(self.root, padding="10")
        question_frame.pack()
        
        ttk.Label(question_frame, text="Question:", font=('Arial', 10)).pack()
        self.question_label = ttk.Label(
            question_frame,
            text="",
            font=('Arial', 16, 'bold'),
            foreground='blue'
        )
        self.question_label.pack(pady=10)
        
        # Instructions
        ttk.Label(
            question_frame,
            text="Which button shows the correct item?",
            font=('Arial', 12)
        ).pack()
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack()
        
        self.image_labels = []
        self.button_buttons = []
        
        for i in range(4):
            col = i % 2
            row = i // 2
            
            frame = ttk.Frame(buttons_frame, relief='solid', borderwidth=2)
            frame.grid(row=row, column=col, padx=10, pady=10)
            
            # Image
            img_label = ttk.Label(frame)
            img_label.pack()
            self.image_labels.append(img_label)
            
            # Button
            btn = ttk.Button(
                frame,
                text=f"Button {i+1}",
                command=lambda idx=i+1: self.select_button(idx)
            )
            btn.pack(pady=5)
            self.button_buttons.append(btn)
        
        # Control buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack()
        
        ttk.Button(
            control_frame,
            text="Skip (S)",
            command=self.skip
        ).pack(side='left', padx=5)
        
        ttk.Label(
            control_frame,
            text="Keyboard: 1, 2, 3, 4 = Select button | S = Skip",
            font=('Arial', 10),
            foreground='gray'
        ).pack(side='left', padx=20)
    
    def load_attempt(self):
        """Load current attempt"""
        if self.current_idx >= len(self.unlabeled):
            self.finish()
            return
        
        attempt_name = self.unlabeled[self.current_idx]
        attempt_path = self.captcha_dir / attempt_name
        
        # Load metadata
        metadata_file = attempt_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                question = metadata.get('question', 'Unknown')
        else:
            question = "Unknown"
        
        self.question_label.config(text=question)
        self.current_question = question
        
        # Load button images
        for i in range(4):
            img_path = attempt_path / f"button_{i+1}.png"
            if img_path.exists():
                img = Image.open(img_path)
                # Resize to fit
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.image_labels[i].config(image=photo)
                self.image_labels[i].image = photo  # Keep reference
            else:
                self.image_labels[i].config(text="Image not found")
        
        # Update progress
        self.progress_label.config(
            text=f"Progress: {self.current_idx + 1} / {len(self.unlabeled)}"
        )
        self.progress_bar['value'] = self.current_idx + 1
    
    def select_button(self, button_idx):
        """Mark button as correct"""
        attempt_name = self.unlabeled[self.current_idx]
        
        # Save label
        self.labels[attempt_name] = {
            "question": self.current_question,
            "correct_button": button_idx
        }
        
        # Save to file
        with open(self.labels_file, 'w') as f:
            json.dump(self.labels, f, indent=2)
        
        # Next attempt
        self.current_idx += 1
        self.load_attempt()
    
    def skip(self):
        """Skip this attempt"""
        self.current_idx += 1
        self.load_attempt()
    
    def finish(self):
        """All done"""
        messagebox.showinfo(
            "Complete!",
            f"Labeled {len(self.labels)} attempts!\n\n"
            f"Labels saved to:\n{self.labels_file}\n\n"
            "Run training:\n  python train_captcha_model.py"
        )
        self.root.quit()


if __name__ == "__main__":
    print("="*60)
    print("🏷️  CAPTCHA Labeling Tool")
    print("="*60)
    
    if not os.path.exists("captcha_learning"):
        print("\n❌ No captcha_learning folder found!")
        print("The bot will create this folder when it encounters wrong CAPTCHAs.")
        print("\nRun the bot first to collect some failed attempts.")
        exit(1)
    
    labeler = CaptchaLabeler("captcha_learning")
