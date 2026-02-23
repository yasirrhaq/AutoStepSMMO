#!/usr/bin/env python3
"""
Automatic CAPTCHA Learning System

Automatically learns from CAPTCHA attempts without manual labeling.
Uses successful attempts to retroactively label failed attempts.

How it works:
1. Bot saves ALL CAPTCHA attempts (both success and failures)
2. When bot succeeds on a question it previously failed, we know the correct answer
3. Auto-labels failures based on matching successful attempts
4. Automatically trains model when enough new labels accumulated
5. Bot automatically uses improved model

This creates a self-improving loop with zero manual intervention.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import subprocess
import sys


class AutoCaptchaLearner:
    def __init__(self, captcha_dir="captcha_learning"):
        self.captcha_dir = Path(captcha_dir)
        self.labels_file = self.captcha_dir / "labels.json"
        self.success_dir = self.captcha_dir / "successes"
        self.failed_dir = self.captcha_dir / "failures"
        
        # Create directories
        self.success_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create labels
        if self.labels_file.exists():
            with open(self.labels_file, 'r') as f:
                self.labels = json.load(f)
        else:
            self.labels = {}
        
        # Track when last training happened
        self.stats_file = self.captcha_dir / "learning_stats.json"
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                "total_attempts": 0,
                "total_successes": 0,
                "total_failures": 0,
                "auto_labeled": 0,
                "last_training": None,
                "training_count": 0,
                "labels_since_training": 0
            }
    
    def save_stats(self):
        """Save learning statistics"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def save_labels(self):
        """Save labels to file"""
        with open(self.labels_file, 'w') as f:
            json.dump(self.labels, f, indent=2)
    
    def record_attempt(self, question: str, button_clicked: int, success: bool, 
                      button_images: List[bytes]) -> str:
        """
        Record a CAPTCHA attempt (success or failure)
        
        Args:
            question: The CAPTCHA question (e.g., "Cherry")
            button_clicked: Which button was clicked (1-4)
            success: Whether the attempt succeeded
            button_images: List of 4 button images as bytes
            
        Returns:
            Path to saved attempt folder
        """
        # Update stats
        self.stats['total_attempts'] += 1
        if success:
            self.stats['total_successes'] += 1
        else:
            self.stats['total_failures'] += 1
        
        # Create attempt folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        status = "success" if success else "failed"
        attempt_name = f"{status}_{timestamp}"
        
        # Save to appropriate directory
        target_dir = self.success_dir if success else self.failed_dir
        attempt_path = target_dir / attempt_name
        attempt_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            "question": question,
            "button_clicked": button_clicked,
            "success": success,
            # correct_answer: auto-set for successes (selected button was correct),
            # None for failures (requires manual labeling or auto-label from a later success)
            "correct_answer": button_clicked if success else None,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat()
        }
        
        with open(attempt_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save button images
        from PIL import Image
        import io
        
        for i, img_bytes in enumerate(button_images):
            if img_bytes:
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    img.save(attempt_path / f"button_{i+1}.png")
                except Exception as e:
                    print(f"Warning: Could not save button {i+1} image: {e}")
        
        # If success, immediately try to auto-label past failures
        if success:
            self._auto_label_from_success(question, button_clicked)
        else:
            # Immediately auto-label this failure with base CLIP
            self._auto_label_with_clip(attempt_path, question)
        
        self.save_stats()
        
        return str(attempt_path)
    
    def _auto_label_with_clip(self, attempt_path: Path, question: str):
        """
        Use base CLIP to predict the correct button for a newly recorded failure.

        Loads button_1.png … button_4.png from attempt_path and scores them
        against the question text.  Writes correct_answer into metadata.json
        immediately so the failure is training-ready without waiting for a
        matching success attempt.
        """
        try:
            from PIL import Image as PILImage
            import torch
            from transformers import CLIPModel, CLIPProcessor
        except ImportError:
            return  # CLIP not installed — skip silently

        button_images = []
        for btn_num in range(1, 5):
            img_path = attempt_path / f"button_{btn_num}.png"
            if img_path.exists():
                try:
                    button_images.append(PILImage.open(img_path).convert("RGB"))
                except Exception:
                    pass

        if len(button_images) == 0:
            return

        try:
            model_id = "openai/clip-vit-base-patch32"
            # Reuse a cached instance if available on the class to avoid
            # re-loading 600 MB of weights on every failure.
            if not hasattr(AutoCaptchaLearner, "_clip_model"):
                AutoCaptchaLearner._clip_model     = CLIPModel.from_pretrained(model_id)
                AutoCaptchaLearner._clip_processor = CLIPProcessor.from_pretrained(model_id)
                AutoCaptchaLearner._clip_model.eval()

            clip_model = AutoCaptchaLearner._clip_model
            clip_proc  = AutoCaptchaLearner._clip_processor

            text_variations = [
                question, question.lower(), question.title(),
                f"a {question}", f"an {question}", f"the {question}",
                f"{question} item", f"{question} object",
                f"picture of {question}", f"image of {question}",
                f"a photo of {question}",
            ]

            with torch.no_grad():
                inputs = clip_proc(
                    text=text_variations,
                    images=button_images,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                )
                outputs = clip_model(**inputs)

                # logits_per_image shape: [num_images, num_texts]
                # We want: for each text prompt, which image wins? Then average.
                # softmax(dim=0) → across images for each text = correct ranking direction
                probs_per_text = outputs.logits_per_image.softmax(dim=0)  # [num_images, num_texts]
                # Average win-probability across all text variations for each image
                avg_probs = probs_per_text.mean(dim=1)  # [num_images]

            n_images = len(button_images)
            scores = [
                (idx + 1, float(avg_probs[idx]) * 100)
                for idx in range(n_images)
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            best_button, best_conf = scores[0]
            margin = best_conf - scores[1][1] if len(scores) > 1 else best_conf

            # Minimum confidence threshold — don't label if CLIP is barely above
            # random (random baseline = 100/n_images %).
            random_baseline = 100.0 / n_images
            min_conf  = random_baseline + 10.0   # must beat random by at least 10 pp
            min_margin = 5.0                      # must win by at least 5 pp over 2nd

            if best_conf < min_conf or margin < min_margin:
                print(
                    f"  🤖 CLIP skipped labeling '{question}': "
                    f"conf {best_conf:.1f}% (need >{min_conf:.0f}%), "
                    f"margin {margin:.1f}% (need >{min_margin:.0f}%) — too uncertain"
                )
                return

            # Update metadata.json with prediction
            metadata_path = attempt_path / "metadata.json"
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            metadata["correct_answer"]  = best_button
            metadata["auto_labeled"]    = True
            metadata["auto_label_conf"] = round(best_conf, 2)
            metadata["auto_label_tool"] = "base-clip-realtime"
            metadata["labeled_at"]      = datetime.now().isoformat()

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            self.stats["auto_labeled"] = self.stats.get("auto_labeled", 0) + 1
            self.stats["labels_since_training"] = self.stats.get("labels_since_training", 0) + 1

            print(
                f"  🤖 CLIP auto-labeled failure: '{question}' → "
                f"btn {best_button} (conf {best_conf:.1f}%, margin {margin:.1f}%)"
            )

            self._check_auto_training()

        except Exception as e:
            print(f"  ⚠️  CLIP auto-label failed: {e}")

    def _auto_label_from_success(self, question: str, correct_button: int):
        """
        Automatically label past failures based on a successful attempt.

        When the bot succeeds on a question it previously failed, we now know
        which button was correct, so we retroactively set correct_answer in each
        matching failure's metadata.json.
        """
        new_labels = 0

        if not self.failed_dir.exists():
            return

        for failed_attempt in self.failed_dir.iterdir():
            if not failed_attempt.is_dir():
                continue

            metadata_file = failed_attempt / "metadata.json"
            if not metadata_file.exists():
                continue

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Skip already labeled
            if metadata.get("correct_answer") is not None:
                continue

            # Check if question matches
            if metadata.get("question", "").lower().strip() == question.lower().strip():
                # Write correct_answer directly into the metadata file
                metadata["correct_answer"] = correct_button
                metadata["auto_labeled"] = True
                metadata["labeled_at"] = datetime.now().isoformat()

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                new_labels += 1

        if new_labels > 0:
            self.stats['auto_labeled'] += new_labels
            self.stats['labels_since_training'] += new_labels
            self.save_stats()

            print(f"Auto-labeled {new_labels} past failure(s) for question: {question}")

            # Check if we should trigger automatic training
            self._check_auto_training()
    
    def _check_auto_training(self):
        """
        Check if we should automatically trigger model training
        
        Triggers training when:
        - At least 20 new labels since last training
        - At least 1 hour since last training (prevent too frequent training)
        """
        MIN_LABELS_FOR_TRAINING = 20
        MIN_HOURS_BETWEEN_TRAINING = 1
        
        if self.stats['labels_since_training'] < MIN_LABELS_FOR_TRAINING:
            return
        
        # Check time since last training
        if self.stats['last_training']:
            try:
                last_training = datetime.fromisoformat(self.stats['last_training'])
                hours_since = (datetime.now() - last_training).total_seconds() / 3600
                if hours_since < MIN_HOURS_BETWEEN_TRAINING:
                    return
            except:
                pass
        
        print(f"\n{'='*60}")
        print(f"🎓 AUTO-TRAINING TRIGGERED")
        print(f"{'='*60}")
        print(f"New labels: {self.stats['labels_since_training']}")
        print(f"Total labels: {len(self.labels)}")
        print(f"Training model in background...")
        
        # Trigger training in background
        self._trigger_background_training()
    
    def _trigger_background_training(self):
        """
        Trigger model training in background without blocking bot
        """
        try:
            # Run training script in background
            training_script = Path(__file__).parent / "train_captcha_model.py"
            
            if not training_script.exists():
                print("⚠️  Training script not found, skipping auto-training")
                return
            
            # Get Python executable
            python_exe = sys.executable
            
            # Start training in background (non-blocking)
            if os.name == 'nt':  # Windows
                # Use START to run in background on Windows
                subprocess.Popen(
                    f'start /B "" "{python_exe}" "{training_script}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # Linux/Mac
                subprocess.Popen(
                    [python_exe, str(training_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # Update stats
            self.stats['last_training'] = datetime.now().isoformat()
            self.stats['training_count'] += 1
            self.stats['labels_since_training'] = 0
            self.save_stats()
            
            print("✅ Background training started")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"⚠️  Could not start background training: {e}")
    
    def get_learning_status(self) -> Dict:
        """
        Get current learning status

        Returns dict with statistics about the learning system.
        """
        success_count = len([d for d in self.success_dir.iterdir() if d.is_dir()]) if self.success_dir.exists() else 0
        failed_count = len([d for d in self.failed_dir.iterdir() if d.is_dir()]) if self.failed_dir.exists() else 0

        # Count labeled failures (correct_answer set in metadata.json)
        labeled_count = 0
        if self.failed_dir.exists():
            for d in self.failed_dir.iterdir():
                if not d.is_dir():
                    continue
                meta = d / "metadata.json"
                if meta.exists():
                    try:
                        with open(meta) as f:
                            m = json.load(f)
                        if m.get("correct_answer") is not None:
                            labeled_count += 1
                    except Exception:
                        pass

        unlabeled_count = failed_count - labeled_count
        
        return {
            "total_attempts": self.stats['total_attempts'],
            "successes": success_count,
            "failures": failed_count,
            "labeled": labeled_count,
            "unlabeled": unlabeled_count,
            "auto_labeled": self.stats.get('auto_labeled', 0),
            "trainings": self.stats.get('training_count', 0),
            "last_training": self.stats.get('last_training'),
            "labels_until_next_training": max(0, 20 - self.stats.get('labels_since_training', 0))
        }
    
    def print_status(self):
        """Print learning status"""
        status = self.get_learning_status()
        
        print(f"\n{'='*60}")
        print(f"🤖 AUTO-LEARNING STATUS")
        print(f"{'='*60}")
        print(f"Total CAPTCHA attempts: {status['total_attempts']}")
        print(f"  ✅ Successes: {status['successes']}")
        print(f"  ❌ Failures: {status['failures']}")
        print(f"  🏷️  Auto-labeled: {status['auto_labeled']}")
        print(f"  📚 Total labeled: {status['labeled']}")
        print(f"  ❓ Unlabeled: {status['unlabeled']}")
        print(f"\nModel trainings: {status['trainings']}")
        if status['last_training']:
            print(f"Last training: {status['last_training']}")
        print(f"Labels until next training: {status['labels_until_next_training']}")
        print(f"{'='*60}\n")


def test_auto_learning():
    """Test the auto-learning system"""
    learner = AutoCaptchaLearner()
    learner.print_status()


if __name__ == "__main__":
    print("="*60)
    print("🤖 Automatic CAPTCHA Learning System")
    print("="*60)
    print()
    print("This system automatically learns from CAPTCHA attempts.")
    print("No manual labeling required!")
    print()
    
    test_auto_learning()
