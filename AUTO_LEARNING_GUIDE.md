# 🤖 Automatic CAPTCHA Learning System

## Overview

Your bot now has **fully automated CAPTCHA learning** with **zero manual intervention required**!

## How It Works

### 1. **Records All Attempts**
- Bot saves EVERY CAPTCHA attempt (both success and failures)
- Successes saved to: `captcha_learning/successes/`
- Failures saved to: `captcha_learning/failures/`

### 2. **Automatic Labeling**
When the bot succeeds on a CAPTCHA question it previously failed:
- **Automatically labels past failures** with the correct answer
- No manual work needed!

**Example:**
- Travel #10: Bot fails "Cherry" → Saved as failure
- Travel #50: Bot succeeds "Cherry" by clicking Button 3
- **System automatically labels** the failure from Travel #10 with "Button 3 is correct"

### 3. **Automatic Training**
When enough labels accumulated (20+ new labels):
- **Automatically triggers model training** in background
- Training runs without interrupting your bot
- Bot automatically detects and uses the improved model

### 4. **Continuous Improvement**
- More attempts = More labels = Better model
- System learns patterns over time
- **No manual labeling, training, or intervention needed**

## Current Learning Status

Check status anytime by running:
```bash
python auto_captcha_learner.py
```

Example output:
```
🤖 AUTO-LEARNING STATUS
============================================================
Total CAPTCHA attempts: 45
  ✅ Successes: 38
  ❌ Failures: 7
  🏷️  Auto-labeled: 5
  📚 Total labeled: 5
  ❓ Unlabeled: 2

Model trainings: 0
Labels until next training: 15
============================================================
```

## Auto-Training Triggers

Training automatically starts when:
- **20+ new labels** accumulated since last training
- **At least 1 hour** since last training (prevents too frequent training)

When triggered, you'll see:
```
============================================================
🎓 AUTO-TRAINING TRIGGERED
============================================================
New labels: 23
Total labels: 23
Training model in background...
✅ Background training started
============================================================
```

## Folder Structure

```
captcha_learning/
├── successes/              # Successful attempts
│   ├── success_20260223_150532/
│   │   ├── metadata.json   # Question + button clicked
│   │   ├── button_1.png
│   │   ├── button_2.png
│   │   ├── button_3.png
│   │   └── button_4.png
│   └── ...
├── failures/               # Failed attempts
│   ├── failed_20260223_140210/
│   │   ├── metadata.json
│   │   ├── button_1.png
│   │   ├── button_2.png
│   │   ├── button_3.png
│   │   └── button_4.png
│   └── ...
├── labels.json            # Auto-generated labels
└── learning_stats.json    # System statistics
```

## Benefits

### ✅ Zero Manual Work
- No need to label attempts manually
- No need to run training scripts
- No need to manage models

### ✅ Learns From Experience
- Bot improves from its own mistakes
- More gameplay = Better CAPTCHA solving
- Patterns recognized automatically

### ✅ Non-Intrusive
- Training runs in background
- Doesn't interrupt your bot
- Automatic model deployment

### ✅ Performance Tracking
- Built-in statistics
- Track success rate improvement
- Monitor training frequency

## Technical Details

### Auto-Labeling Logic
```python
# When bot succeeds on "Cherry" by clicking Button 3:
1. System checks all past failures for question "Cherry"
2. Labels those failures with: correct_button = 3
3. Saves labels to labels.json
4. Updates statistics
5. Checks if training should trigger
```

### Training Process
```python
# When 20+ new labels accumulated:
1. Triggers train_captcha_model.py in background
2. Loads all labeled attempts
3. Fine-tunes CLIP model on labeled data
4. Saves improved model to models/clip-captcha-finetuned/
5. Bot automatically uses improved model on next load
```

### Model Loading Priority
```python
# Bot checks in this order:
1. models/clip-captcha-finetuned/  (if exists, uses this)
2. openai/clip-vit-base-patch32    (fallback to base model)
```

## Monitoring Progress

### During Bot Runs
You'll see messages like:
```
🤖 Auto-labeled 3 past failure(s) for question: Cherry
```

### Check Statistics
```bash
cd SMMO
python auto_captcha_learner.py
```

### View Labels
```bash
# View auto-generated labels
cat captcha_learning/labels.json
```

Example `labels.json`:
```json
{
  "failed_20260223_140210": {
    "question": "Cherry",
    "correct_button": 3,
    "auto_labeled": true,
    "labeled_at": "2026-02-23T15:05:32"
  },
  "failed_20260223_141522": {
    "question": "Apple",
    "correct_button": 1,
    "auto_labeled": true,
    "labeled_at": "2026-02-23T15:18:45"
  }
}
```

## Expected Improvements

### Initial Phase (0-50 CAPTCHAs)
- Base model accuracy: ~70-80%
- Learning data collecting
- Few auto-labels

### Growth Phase (50-200 CAPTCHAs)
- First auto-training triggers
- Accuracy improves: ~80-90%
- More patterns recognized

### Mature Phase (200+ CAPTCHAs)
- Multiple trainings completed
- Accuracy: ~90-95%+
- Handles most items confidently

## Troubleshooting

### "No auto-labels yet"
**Cause:** Bot hasn't succeeded on any questions it previously failed

**Solution:** Keep running - as bot encounters same questions multiple times, auto-labeling will start

### "Training not triggering"
**Cause:** Need at least 20 new labels

**Solution:** 
- Check status: `python auto_captcha_learner.py`
- Wait for more auto-labels to accumulate
- Each success on a previously-failed question = 1+ new labels

### "Model not improving"
**Cause:** Training completed but model not loaded

**Solution:**
- Check if `models/clip-captcha-finetuned/` exists
- Restart bot to reload model
- Check logs for training errors

### Manual Check Learning Files
```bash
# Count attempts
ls captcha_learning/successes/ | wc -l
ls captcha_learning/failures/ | wc -l

# View statistics
cat captcha_learning/learning_stats.json

# View labels
cat captcha_learning/labels.json
```

## Comparison: Old vs New

### Old System (Manual)
❌ Bot only saves failures
❌ Must manually label each failure
❌ Must manually run training script
❌ Must manually manage model deployment
⏱️ Time required: ~30 minutes per training session

### New System (Automatic)
✅ Bot saves all attempts (success + failure)
✅ Auto-labels failures based on successes
✅ Auto-trains when threshold reached
✅ Auto-deploys improved model
⏱️ Time required: **Zero** - fully automatic

## FAQ

**Q: Do I need to do anything to enable auto-learning?**
A: No! It's already enabled and working. Just run your bot.

**Q: How long until I see improvements?**
A: Typically after 20-50 CAPTCHA attempts, first auto-training will trigger.

**Q: Will this slow down my bot?**
A: No - training runs in background and doesn't interrupt bot operations.

**Q: Can I check progress without stopping the bot?**
A: Yes - open a new terminal and run: `python auto_captcha_learner.py`

**Q: What if I want manual control?**
A: The old manual system is still available:
- Use `label_captcha_attempts.py` for GUI labeling
- Use `train_captcha_model.py` for manual training

**Q: How do I reset and start fresh?**
A: Delete the `captcha_learning/` folder. Bot will recreate it.

## Summary

🎯 **Goal:** AI that improves itself automatically

✅ **Achieved:** 
- Zero manual intervention
- Learning from experience
- Performance improvement over time
- Background training
- Automatic deployment

🚀 **Result:** Set it and forget it - your bot gets smarter over time!

---

## Need Help?

Run diagnostics:
```bash
python auto_captcha_learner.py
```

Or check the logs:
```bash
cat bot_session.log | grep -i "auto-learning"
cat bot_session.log | grep -i "training"
```
