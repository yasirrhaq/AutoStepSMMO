# CAPTCHA Smart Model Fallback Strategy

## Overview

The bot now supports **intelligent model switching** between the base CLIP model and your fine-tuned model based on their performance. This helps maximize your CAPTCHA solve rate by automatically falling back to the better-performing model when one starts failing.

## How It Works

The smart fallback system tracks consecutive failures for each model:

1. **Base Model** - The pre-trained OpenAI CLIP model (`openai/clip-vit-base-patch32`)
2. **Fine-tuned Model** - Your custom-trained model (`models/clip-captcha-finetuned`)

When a model fails consecutively (default: 5 times), the system automatically switches to the other model. On success, the failure counter resets.

```
Fine-tuned Model → ❌❌❌❌❌ (5 failures) → Switch to Base Model
Base Model       → ❌❌❌❌❌ (5 failures) → Switch to Fine-tuned Model
Either Model     → ✅ (success)          → Reset failure counter to 0
```

### Why This Works

- **Complementary Strengths**: Each model may excel at different types of images
- **Adaptive**: Automatically adjusts to which model performs better
- **Resilient**: If one model gets into a "bad pattern", switching helps break it
- **Learning Opportunity**: Tracks which types of CAPTCHAs each model struggles with

## Configuration

Add these settings to your `config.json`:

```json
{
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 5,
  "use_finetuned_captcha": false
}
```

### Available Strategies

#### 1. `smart_fallback` (RECOMMENDED)
Intelligently switches between models based on performance.

- **Best for**: Most users, especially those with a fine-tuned model
- **Behavior**: 
  - Starts with fine-tuned model (if available)
  - Switches to other model after N consecutive failures
  - Automatically finds which model works better

```json
{
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 5
}
```

#### 2. `base_only`
Always uses the base CLIP model.

- **Best for**: Testing, or if you don't have a fine-tuned model yet
- **Behavior**: Never uses the fine-tuned model

```json
{
  "captcha_model_strategy": "base_only"
}
```

#### 3. `finetuned_only`
Always uses your fine-tuned model.

- **Best for**: When your fine-tuned model performs significantly better
- **Behavior**: Never falls back to base model
- **Requires**: A trained model at `models/clip-captcha-finetuned`

```json
{
  "captcha_model_strategy": "finetuned_only"
}
```

### Failure Threshold

The `captcha_failure_threshold` determines how many consecutive failures trigger a model switch.

```json
{
  "captcha_failure_threshold": 5  // Default: 5 (range: 3-10 recommended)
}
```

**Recommended values:**
- `3` - Aggressive switching, responds quickly to failures
- `5` - **Default** - Balanced, gives each model a fair chance
- `7-10` - Conservative, more patient before switching

## Training Your Model

To create a fine-tuned model that works with smart fallback:

1. **Collect Data**: Run the bot with `auto_captcha_training: true` to collect labeled attempts
2. **Train Model**: Run `train_model.bat` or `python train_captcha_model.py`
3. **Enable Smart Fallback**: Set `captcha_model_strategy: "smart_fallback"` in config.json
4. **Monitor**: Watch the logs to see which model performs better

```bash
# Train your model
train_model.bat

# Or manually
python train_captcha_model.py
```

## Monitoring Performance

The bot logs which model is being used and tracks failures:

```
🎯 Using fine-tuned CAPTCHA model (failures: 0/5)
✓ CAPTCHA solved successfully!
✅ Fine-tuned model success - reset failure counter

❌ Fine-tuned model failed (3/5)
❌ Fine-tuned model failed (4/5)
❌ Fine-tuned model failed (5/5)
⚠️ Fine-tuned model failed 5x - switching to base model

🔵 Using base CLIP model (failures: 0/5)
✓ CAPTCHA solved successfully!
✅ Base model success - reset failure counter
```

## Best Practices

### 1. Start with Smart Fallback
```json
{
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 5
}
```

### 2. Check Your Logs
Monitor `simplemmo_bot.log` to see which model is performing better:
```bash
# Look for patterns like:
grep "model success\|model failed" simplemmo_bot.log | tail -20
```

### 3. Retrain Periodically
As you collect more labeled data, retrain your model:
```bash
# Every 50-100 new labeled attempts
train_model.bat
```

### 4. Adjust Threshold Based on Results
- If switching happens too frequently: **Increase** threshold (e.g., 7)
- If one model keeps failing: **Decrease** threshold (e.g., 3)

## Troubleshooting

### Model Not Switching
**Problem**: Bot keeps using the same failing model

**Solutions**:
1. Check config: `"captcha_model_strategy": "smart_fallback"`
2. Lower threshold: `"captcha_failure_threshold": 3`
3. Verify both models exist (base is auto-downloaded, fine-tuned needs training)

### Always Using Base Model
**Problem**: Fine-tuned model never gets used

**Solutions**:
1. Check if fine-tuned model exists: `models/clip-captcha-finetuned/`
2. Train a model: Run `train_model.bat`
3. Check strategy isn't set to `base_only`

### Both Models Failing
**Problem**: Neither model can solve CAPTCHAs

**Solutions**:
1. Check CAPTCHA images are loading properly (see `captcha_ai_debug/`)
2. Ensure sufficient training data (at least 20-30 labeled examples)
3. Review logs for errors during model loading
4. Try manual solving: `python solve_captcha_manually.py`

## Example Configurations

### Maximum Performance (Recommended)
```json
{
  "auto_solve_captcha": true,
  "auto_captcha_training": true,
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 5
}
```

### Conservative (Fewer Model Switches)
```json
{
  "auto_solve_captcha": true,
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 8
}
```

### Aggressive Learning
```json
{
  "auto_solve_captcha": true,
  "auto_captcha_training": true,
  "captcha_model_strategy": "smart_fallback",
  "captcha_failure_threshold": 3
}
```

### Testing Base Model Only
```json
{
  "auto_solve_captcha": true,
  "captcha_model_strategy": "base_only"
}
```

## Related Files

- `train_model.bat` - Train your fine-tuned model
- `CAPTCHA_SETUP.md` - Initial CAPTCHA solver setup
- `CAPTCHA_LEARNING_GUIDE.md` - How to train models
- `AUTO_LEARNING_GUIDE.md` - Automated model improvement
- `config.json` - Your configuration file

## Questions?

For more help with CAPTCHA solving, check:
- [CAPTCHA_SETUP.md](CAPTCHA_SETUP.md) - Setup guide
- [CAPTCHA_QUICKREF.md](CAPTCHA_QUICKREF.md) - Quick reference
- [AUTO_LEARNING_GUIDE.md](AUTO_LEARNING_GUIDE.md) - Auto-training system
