# 🤖 CAPTCHA Learning System Guide

## ❓ How It Works

### **Current System: Data Collection Only**

The bot currently **collects data but does NOT train the AI model**. Here's what happens:

1. **Bot encounters CAPTCHA** → Uses AI (CLIP model) to select answer
2. **If answer is wrong** → Saves the attempt to `captcha_learning/`
3. **Next time** → Uses the SAME pre-trained CLIP model (no learning)

### **Why No Automatic Learning?**

The CLIP AI model is **pre-trained and frozen** - it cannot be updated on-the-fly. Real machine learning requires:
- Hundreds/thousands of examples
- GPU for training
- Labeled dataset (correct answers marked)
- Time to retrain the model

---

## 📂 What Gets Saved

When the bot selects a wrong answer, it saves:

```
captcha_learning/
├── attempt_20260223_041233/
│   ├── button_1.png          # Image of choice 1
│   ├── button_2.png          # Image of choice 2  
│   ├── button_3.png          # Image of choice 3
│   ├── button_4.png          # Image of choice 4
│   └── metadata.json         # Info about the attempt
└── wrong_attempts.jsonl      # Log of all attempts
```

### **metadata.json Example:**
```json
{
  "timestamp": "2026-02-23 04:12:33",
  "question": "Select the: Cherry",
  "selected_button": 2,
  "button_count": 4,
  "attempt_folder": "attempt_20260223_041233"
}
```

### **wrong_attempts.jsonl Example:**
```json
{"timestamp": "2026-02-23 04:12:33", "question": "Cherry", "selected": 2, "folder": "attempt_20260223_041233"}
{"timestamp": "2026-02-23 04:15:48", "question": "Strawberry", "selected": 3, "folder": "attempt_20260223_041548"}
```

---

## 🎯 How to Actually Use This Data

### **Option 1: Manual Review (Simple)**

1. Open `captcha_learning/` folder
2. Look at each attempt folder
3. Check which button was correct
4. Manually note patterns (e.g., "Cherry always button 3")

**Use Case:** If you notice the bot always picks wrong for specific items, you can:
- Create a lookup table
- Add to bot: `if "cherry" in question: select_button(3)`

---

### **Option 2: Fine-Tune CLIP Model (Advanced)**

If you want the AI to actually learn:

#### **Requirements:**
- Python with PyTorch
- GPU (CUDA) recommended
- 100+ labeled examples
- Time (hours/days for training)

#### **Steps:**

**1. Label Your Data**
Create `labels.json`:
```json
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
```

**2. Create Training Script**
```python
# train_captcha_model.py (you need to create this)
import torch
from transformers import CLIPModel, CLIPProcessor
from PIL import Image
import json

# Load labeled data
with open("captcha_learning/labels.json") as f:
    labels = json.load(f)

# Load CLIP model
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Fine-tune model on your data
# ... (complex training code here)

# Save improved model
model.save_pretrained("models/clip-captcha-finetuned")
```

**3. Update Bot to Use New Model**
In `simplemmo_bot.py`, change:
```python
# OLD:
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

# NEW:
model = CLIPModel.from_pretrained("models/clip-captcha-finetuned")
```

---

### **Option 3: Pattern Analysis (Data Science)**

Analyze `wrong_attempts.jsonl` to find patterns:

```python
# analyze_captcha.py
import json
import pandas as pd

# Load all attempts
attempts = []
with open("captcha_learning/wrong_attempts.jsonl") as f:
    for line in f:
        attempts.append(json.loads(line))

df = pd.DataFrame(attempts)

# Find most common mistakes
print("Most failed items:")
print(df["question"].value_counts())

# Check if certain buttons are always wrong
print("\nButton selection distribution:")
print(df["selected"].value_counts())
```

This tells you:
- Which items the bot struggles with
- If there's a bias (e.g., always picks button 2)

---

### **Option 4: Create Answer Database (Practical)**

If you manually solve 50+ CAPTCHAs, create:

```python
# captcha_answers.py
CAPTCHA_ANSWERS = {
    "cherry": 3,
    "strawberry": 1,
    "apple": 2,
    "chest piece": 4,
    # ... more items
}
```

Then update bot:
```python
# In _solve_captcha():
item_name = self._extract_required_item().lower()
if item_name in CAPTCHA_ANSWERS:
    correct_button = CAPTCHA_ANSWERS[item_name]
    return self._click_button(correct_button)
else:
    # Fall back to AI
    return self._ai_solve_captcha()
```

---

## 📊 Check if Bot is "Learning"

### **Current Behavior:**
```
Attempt 1: Wrong answer → Saves data
Attempt 2: Wrong answer → Saves data
Attempt 3: Wrong answer → Saves data  
... (no improvement because model isn't trained)
```

The bot **collects data for future training** but doesn't improve automatically.

### **To Actually Improve:**
1. Label the saved data (mark correct answers)
2. Train a new model OR create answer database
3. Update bot to use improved model/database

---

## 🚀 Quick Win: Simple Answer Database

**Most practical approach for 90% of users:**

1. Run bot, collect 20-30 wrong attempts
2. Manually review images, note correct answers
3. Create `captcha_answers.json`:
```json
{
  "cherry": 3,
  "strawberry": 1,
  "apple": 2
}
```

4. I can add code to bot to read this file first before using AI

Would you like me to:
- **Create the answer database feature?** (simple lookup before AI)
- **Create a labeling tool?** (GUI to mark correct answers)
- **Create analysis scripts?** (find patterns in failures)

---

## 💡 Summary

**What you have now:**
- ✅ Data collection system (saves wrong attempts)
- ✅ Organized folder structure
- ✅ Metadata for each attempt

**What you DON'T have yet:**
- ❌ Automatic model improvement
- ❌ Learning from past mistakes
- ❌ Performance improvement over time

**To get actual learning:**
- **Easy**: Create answer database from collected data
- **Medium**: Analyze patterns, fix systematic errors
- **Hard**: Fine-tune AI model with GPU training

Let me know which approach you want, and I'll help implement it!
