"""
auto_label_captcha.py
---------------------
Scans captcha_learning/failures/ for entries with no correct_answer and uses
base CLIP (openai/clip-vit-base-patch32) to predict which button is correct.

Usage:
    python auto_label_captcha.py            # label all unlabeled failures
    python auto_label_captcha.py --dry-run  # print predictions without writing
    python auto_label_captcha.py --review   # show prediction confidence for every failure

The script is safe to run repeatedly — it skips entries that are already labeled.
After labeling, re-run train_captcha_model.py to incorporate the new labels.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from io import BytesIO

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Auto-label CAPTCHA failures with base CLIP")
parser.add_argument("--dry-run", action="store_true",
                    help="Print predictions but do NOT write to metadata.json")
parser.add_argument("--review", action="store_true",
                    help="Show confidence scores for all failures (including already labeled)")
parser.add_argument("--failures-dir", default="captcha_learning/failures",
                    help="Path to failures directory (default: captcha_learning/failures)")
args = parser.parse_args()

FAILURES_DIR = Path(args.failures_dir)

if not FAILURES_DIR.exists():
    print(f"Failures directory not found: {FAILURES_DIR}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Load CLIP once (base model only)
# ---------------------------------------------------------------------------

print("Loading base CLIP model (openai/clip-vit-base-patch32)...")
try:
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    MODEL_ID = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(MODEL_ID)
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    model.eval()
    print("CLIP model loaded.\n")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with:  pip install transformers torch Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLIP scoring helper
# ---------------------------------------------------------------------------

def score_buttons(question: str, button_images: list) -> list:
    """
    Score each PIL image against the question text.

    Returns a list of (button_index_1based, confidence_pct) sorted by confidence
    descending.
    """
    text_variations = [
        question,
        question.lower(),
        question.title(),
        f"a {question}",
        f"an {question}",
        f"the {question}",
        f"{question} item",
        f"{question} object",
        f"picture of {question}",
        f"image of {question}",
        f"a photo of {question}",
    ]

    with torch.no_grad():
        inputs = processor(
            text=text_variations,
            images=button_images,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        outputs = model(**inputs)
        logits = outputs.logits_per_image          # shape: [num_images, num_texts]
        # softmax(dim=0): for each text, which image wins? → correct ranking direction
        probs = logits.softmax(dim=0)              # [num_images, num_texts]
        avg_probs = probs.mean(dim=1)              # [num_images] — average win-rate

    scores = []
    for img_idx in range(len(button_images)):
        scores.append((img_idx + 1, float(avg_probs[img_idx]) * 100))   # 1-based button index

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

failure_dirs = sorted(
    [d for d in FAILURES_DIR.iterdir() if d.is_dir()],
    key=lambda d: d.name,
)

total        = 0
already_done = 0
no_images    = 0
labeled_now  = 0
errors       = 0

print(f"Scanning {len(failure_dirs)} failure folder(s) in {FAILURES_DIR}\n")
print("=" * 60)

for failure_dir in failure_dirs:
    metadata_path = failure_dir / "metadata.json"
    if not metadata_path.exists():
        continue

    total += 1

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    question       = metadata.get("question", "")
    correct_answer = metadata.get("correct_answer")

    if not args.review and correct_answer is not None:
        already_done += 1
        continue

    # Collect button images
    button_pil_images = []
    for btn_num in range(1, 5):
        img_path = failure_dir / f"button_{btn_num}.png"
        if img_path.exists():
            try:
                button_pil_images.append(Image.open(img_path).convert("RGB"))
            except Exception as e:
                print(f"  [WARN] {failure_dir.name}: error loading {img_path.name}: {e}")

    if len(button_pil_images) == 0:
        print(f"  [SKIP] {failure_dir.name}: no button images found")
        no_images += 1
        continue

    # Score with CLIP
    try:
        scores = score_buttons(question, button_pil_images)
    except Exception as e:
        print(f"  [ERROR] {failure_dir.name}: CLIP scoring failed: {e}")
        errors += 1
        continue

    best_button, best_conf   = scores[0]
    second_conf              = scores[1][1] if len(scores) > 1 else 0
    margin                   = best_conf - second_conf

    # Confidence guard: random baseline for 4 images = 25%.
    # Only label if we beat random by ≥10 pp AND win margin ≥5 pp.
    n_images       = len(button_pil_images)
    random_base    = 100.0 / n_images
    min_conf       = random_base + 10.0
    min_margin     = 5.0
    conf_ok        = best_conf >= min_conf and margin >= min_margin

    label_str = (
        f"  Q: '{question}'  →  pred btn {best_button} "
        f"(conf {best_conf:.1f}%, margin {margin:.1f}%)"
        + ("" if conf_ok else "  ⚠️ UNCERTAIN — skipped")
    )

    if args.review:
        existing = f"  [existing: btn {correct_answer}]" if correct_answer is not None else "  [unlabeled]"
        print(f"{failure_dir.name}{existing}")
        print(label_str)
        for btn, conf in scores:
            print(f"      btn {btn}: {conf:.1f}%")
        print()
        continue

    print(f"{failure_dir.name}")
    print(label_str)

    if not conf_ok:
        print(f"  → Skipped (CLIP not confident enough)\n")
        continue

    if not args.dry_run:
        metadata["correct_answer"]  = best_button
        metadata["auto_labeled"]    = True
        metadata["auto_label_conf"] = round(best_conf, 2)
        metadata["auto_label_tool"] = "base-clip"
        metadata["labeled_at"]      = __import__("datetime").datetime.now().isoformat()

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        labeled_now += 1
        print(f"  → Saved correct_answer={best_button}\n")
    else:
        print(f"  → [dry-run] would set correct_answer={best_button}\n")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("=" * 60)
print(f"Total failure folders : {total}")
print(f"Already labeled       : {already_done}")
print(f"Skipped (no images)   : {no_images}")
print(f"Errors                : {errors}")
if args.dry_run:
    print(f"Would label           : {len(failure_dirs) - already_done - no_images - errors}")
elif not args.review:
    print(f"Newly labeled         : {labeled_now}")
print("=" * 60)

if not args.dry_run and not args.review and labeled_now > 0:
    print(f"\n✅ Done! {labeled_now} failure(s) labeled.")
    print("Run  python train_captcha_model.py  to retrain with new labels.")
