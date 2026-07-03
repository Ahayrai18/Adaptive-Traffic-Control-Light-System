import os
import random
import shutil
from pathlib import Path

random.seed(42)

BASE_DIR = r"C:\Users\Kiki Salikil\Downloads\capstone-cuda"

images_dir = os.path.join(BASE_DIR, "train", "images")
labels_dir = os.path.join(BASE_DIR, "train", "labels")

train_img_dir = os.path.join(BASE_DIR, "dataset", "train", "images")
train_lbl_dir = os.path.join(BASE_DIR, "dataset", "train", "labels")

val_img_dir = os.path.join(BASE_DIR, "dataset", "valid", "images")
val_lbl_dir = os.path.join(BASE_DIR, "dataset", "valid", "labels")

os.makedirs(train_img_dir, exist_ok=True)
os.makedirs(train_lbl_dir, exist_ok=True)
os.makedirs(val_img_dir, exist_ok=True)
os.makedirs(val_lbl_dir, exist_ok=True)

images = []

for file in os.listdir(images_dir):
    if file.endswith((".jpg", ".jpeg", ".png")):
        images.append(file)

random.shuffle(images)

split_index = int(len(images) * 0.8)

train_files = images[:split_index]
val_files = images[split_index:]

for img_file in train_files:
    label_file = Path(img_file).stem + ".txt"

    shutil.copy(
        os.path.join(images_dir, img_file),
        os.path.join(train_img_dir, img_file)
    )

    shutil.copy(
        os.path.join(labels_dir, label_file),
        os.path.join(train_lbl_dir, label_file)
    )

for img_file in val_files:
    label_file = Path(img_file).stem + ".txt"

    shutil.copy(
        os.path.join(images_dir, img_file),
        os.path.join(val_img_dir, img_file)
    )

    shutil.copy(
        os.path.join(labels_dir, label_file),
        os.path.join(val_lbl_dir, label_file)
    )

print(f"Train: {len(train_files)}")
print(f"Valid: {len(val_files)}")