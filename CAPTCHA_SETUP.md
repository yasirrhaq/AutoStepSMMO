# CAPTCHA Auto-Solve Setup Guide

## ⚠️ IMPORTANT WARNING

**This feature is for DEVELOPER TESTING ONLY.** 

- Only use on test accounts
- May violate game terms of service if used on production accounts
- Could result in account bans
- Intended for developers testing their own bot detection systems

## 📋 Prerequisites

To enable automatic CAPTCHA solving, you need:

### 1. **Pillow (PIL)** - Image Processing
```bash
pip install Pillow
```

### 2. **Tesseract OCR** - Text Recognition

#### Windows:
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location (usually `C:\Program Files\Tesseract-OCR\`)
3. Add to PATH or set in code

#### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Mac
brew install tesseract
```

### 3. **pytesseract** - Python wrapper
```bash
pip install pytesseract
```

#### Configure Tesseract path (Windows):
If Tesseract is not in PATH, add this to your code:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## 🔧 Configuration

Edit `config.json`:

```json
{
  "auto_solve_captcha": true,
  "captcha_random_fallback": false
}
```

### Options:

- **`auto_solve_captcha`**: 
  - `true` = Automatically attempt to solve CAPTCHAs
  - `false` = Stop and show manual instructions (default)

- **`captcha_random_fallback`**: 
  - `true` = If OCR fails, try random selection (not recommended)
  - `false` = Fail if OCR can't solve it (default)

## 🎯 How It Works

1. **Detection**: Bot detects CAPTCHA challenge in API response
2. **Parsing**: Extracts required item name (e.g., "Ghost")
3. **Download**: Fetches all 4 CAPTCHA images
4. **OCR**: Uses Tesseract to read text from each image
5. **Match**: Finds image matching required item
6. **Submit**: Sends answer and continues

## 📸 Image Saving

If OCR fails to identify the correct image, all CAPTCHA images are saved to:
```
captcha_images/
  uid_0_hash_$2y$10$....png
  uid_1_hash_$2y$10$....png
  uid_2_hash_$2y$10$....png
  uid_3_hash_$2y$10$....png
```

You can manually inspect these to see why OCR failed.

## 🧪 Testing

Test the CAPTCHA solver:

```bash
python test_captcha.py
```

This will:
- Trigger a CAPTCHA on purpose (by making many requests)
- Attempt to solve it automatically
- Show you the process

## 📊 Success Rate

OCR success depends on:
- **Image quality**: Clear text = better results
- **Font style**: Simple fonts work best
- **Image size**: Larger images are easier to read
- **Text language**: English works best

Expected success rate: **70-90%** for simple text images

## 🔍 Troubleshooting

### "PIL not available"
```bash
pip install Pillow
```

### "pytesseract not available"
```bash
pip install pytesseract
# AND install Tesseract binary (see Prerequisites)
```

### "tesseract is not recognized"
Tesseract isn't in PATH. Either:
1. Add `C:\Program Files\Tesseract-OCR\` to Windows PATH
2. Set path in code (see above)

### OCR Returns Wrong Answer
- Check saved images in `captcha_images/`
- Image might be too small or unclear
- Text might be stylized/decorative
- Consider improving image preprocessing

### Still Fails
Set `"auto_solve_captcha": false` and solve manually:
1. Bot will stop when CAPTCHA appears
2. Visit the URL shown
3. Complete verification manually
4. Restart bot

## 🛡️ Ethical Use

This tool is **ONLY** for:
- ✅ Testing your own bot detection systems
- ✅ Development and QA purposes
- ✅ Understanding CAPTCHA mechanics

**NOT** for:
- ❌ Bypassing anti-bot measures on production accounts
- ❌ Violating game terms of service
- ❌ Unfair gameplay advantages
- ❌ Automated farming/botting

## 📝 Legal Notice

You are responsible for how you use this tool. The author:
- Provides this for educational/testing purposes only
- Does not condone violating terms of service
- Is not liable for account bans or consequences
- Recommends only using on test accounts you own

**When in doubt, disable it and solve CAPTCHAs manually.**
