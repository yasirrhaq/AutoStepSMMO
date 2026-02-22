# CAPTCHA Auto-Solve - Quick Reference

## 🚀 Quick Start

### Option 1: Manual Solving (Default - Recommended)
```json
{
  "auto_solve_captcha": false
}
```
Bot stops when CAPTCHA appears and shows you the URL to solve it manually.

### Option 2: Automatic Solving (Testing Only)
```bash
# Install dependencies
python install_captcha_deps.py

# Install Tesseract binary (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Enable in config.json
{
  "auto_solve_captcha": true
}

# Test it
python test_captcha.py
```

## 📊 How It Works

```
1. Bot detects CAPTCHA → "Please press on: Ghost"
2. Downloads 4 CAPTCHA images
3. Uses OCR to read text from each image
4. Finds the "Ghost" image
5. Submits answer automatically
6. Continues travel actions
```

## 📁 New Files Added

| File | Purpose |
|------|---------|
| `CAPTCHA_SETUP.md` | Full installation & usage guide |
| `test_captcha.py` | Test CAPTCHA solver |
| `install_captcha_deps.py` | Install Python dependencies |
| `captcha_images/` | Saved images (created when OCR fails) |

## ⚙️ Config Options

```json
{
  "auto_solve_captcha": false,        // Enable automatic solving
  "captcha_random_fallback": false    // Try random if OCR fails (not recommended)
}
```

## 🎯 Success Rate

| Image Type | Success Rate |
|------------|--------------|
| Clear text (e.g., "Ghost") | ~90% |
| Simple icons with labels | ~70% |
| Stylized/decorative text | ~40% |
| Pure images (no text) | ~0% |

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "PIL not available" | `pip install Pillow` |
| "pytesseract not available" | `pip install pytesseract` |
| "tesseract is not recognized" | Install Tesseract binary + add to PATH |
| OCR returns wrong answer | Check `captcha_images/` folder |
| Still fails | Set `auto_solve_captcha: false` |

## 🔍 Debugging

When OCR fails, images are saved to `captcha_images/`:
```
captcha_images/
├── uid_0_hash_$2y$10$1oq.png  
├── uid_1_hash_$2y$10$Mgc.png  
├── uid_2_hash_$2y$10$y_c.png  
└── uid_3_hash_$2y$10$ufN.png  
```

Open these to see what OCR tried to read.

## ⚠️ Legal & Ethical Use

**ONLY use this for:**
- ✅ Testing your own game's bot detection
- ✅ Development/QA on test accounts
- ✅ Learning about CAPTCHA mechanisms

**NEVER use this for:**
- ❌ Production accounts
- ❌ Violating terms of service
- ❌ Unfair gameplay advantages
- ❌ Automated farming

## 📞 Support

If automatic solving doesn't work:
1. Check logs in `simplemmo_bot.log`
2. Look at saved images in `captcha_images/`
3. Verify Tesseract is installed: `tesseract --version`
4. Test OCR manually: `pytesseract.image_to_string(image)`

**When in doubt, disable it and solve manually!**
