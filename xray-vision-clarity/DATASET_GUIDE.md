# Dataset Guide: Chest X-Ray Images for Pneumonia Detection

This guide provides detailed information about the chest X-ray dataset used for training the pneumonia detection model.

---

## Table of Contents

1. [Dataset Overview](#dataset-overview)
2. [Dataset Statistics](#dataset-statistics)
3. [Download Instructions](#download-instructions)
4. [Dataset Structure](#dataset-structure)
5. [Image Specifications](#image-specifications)
6. [Data Characteristics](#data-characteristics)
7. [Data Validation](#data-validation)
8. [Using Your Own Dataset](#using-your-own-dataset)
9. [Data Augmentation](#data-augmentation)

---

## Dataset Overview

### Dataset Name
Chest X-Ray Images (Pneumonia)

### Source
Kaggle: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia

### Citation
Kermany, D. S., Goldbaum, M., Cai, W., Valentino, C. C., Liang, H., Baxter, S. L., ... & Cui, Y. (2018). Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning. Cell, 172(5), 1122-1131.

### License
CC0: Public Domain - Free for research and educational use

### Original Source
Images from the following sources:
- Guangzhou Women and Children's Medical Center
- NIH Chest X-ray Dataset: https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community

---

## Dataset Statistics

### Overall Size
- **Total Images:** 5,863
- **Total Size:** ~2.0 GB
- **Format:** JPEG
- **Classes:** 2 (Binary Classification)

### Class Distribution

| Class | Train | Validation | Test | Total |
|-------|-------|------------|------|-------|
| NORMAL | 1,349 | 234 | 235 | 1,818 |
| PNEUMONIA | 3,875 | 390 | 391 | 4,656 |
| **Total** | **5,224** | **624** | **626** | **6,474** |

### Class Imbalance Ratio
- PNEUMONIA : NORMAL = 2.56 : 1
- This imbalance is handled using **Focal Loss** during training

### Data Split Strategy
- **Training:** 80% of total
- **Validation:** 10% of total
- **Testing:** 10% of total

**Note:** Standard splits provided by Kaggle dataset

---

## Download Instructions

### Method 1: Manual Download (Recommended for First Time)

**Step 1:** Go to Kaggle
```
https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
```

**Step 2:** Click the "Download" Button
- If not logged in, create a free Kaggle account
- Click the large "Download" button (top-right)

**Step 3:** Extract the ZIP File
- The file `chest-xray-pneumonia.zip` will download (~2GB)
- Extract to a folder of your choice
- Example: `~/Downloads/chest_xray/`

**Step 4:** Verify Extraction
```bash
ls -la ~/Downloads/chest_xray/
# You should see: train/, val/, test/ folders
```

---

### Method 2: Command Line Download (Requires Kaggle API)

**Prerequisites:**
1. Install Kaggle CLI:
   ```bash
   pip install kaggle
   ```

2. Get API Credentials:
   - Visit: https://www.kaggle.com/settings/account
   - Click "Create New API Token"
   - This downloads `kaggle.json`
   - Place it in: `~/.kaggle/kaggle.json`

3. Set Permissions (macOS/Linux):
   ```bash
   chmod 600 ~/.kaggle/kaggle.json
   ```

**Download Dataset:**
```bash
# Navigate to where you want dataset
cd ~/Downloads

# Download dataset
kaggle datasets download -d paultimothymooney/chest-xray-pneumonia

# Extract
unzip chest-xray-pneumonia.zip
```

**Verify:**
```bash
ls -la chest_xray/
```

---

## Dataset Structure

### Expected Directory Structure

```
chest_xray/
├── train/
│   ├── NORMAL/
│   │   ├── NORMAL2-IM-1430_0_0.jpeg
│   │   ├── NORMAL2-IM-1431_0_0.jpeg
│   │   └── ... (1,349 files total)
│   └── PNEUMONIA/
│       ├── person1000_0_100.jpeg
│       ├── person1000_93_1.jpeg
│       └── ... (3,875 files total)
├── val/
│   ├── NORMAL/
│   │   └── ... (234 files)
│   └── PNEUMONIA/
│       └── ... (390 files)
└── test/
    ├── NORMAL/
    │   └── ... (235 files)
    └── PNEUMONIA/
        └── ... (391 files)
```

### File Naming Convention

- **NORMAL images:** `NORMAL<ID>_<COUNT>.jpeg`
  - Example: `NORMAL2-IM-1430_0_0.jpeg`
  - ID: Unique identifier
  - COUNT: Number in sequence (usually 0)

- **PNEUMONIA images:** `person<ID>_<COUNT>.jpeg`
  - Example: `person1000_0_100.jpeg`
  - ID: Patient/person identifier
  - COUNT: Sequence number

**Note:** File names are arbitrary and don't affect training

---

## Image Specifications

### Image Properties

| Property | Value |
|----------|-------|
| **Format** | JPEG |
| **Color Space** | Grayscale (8-bit) |
| **Bit Depth** | 8 bits per pixel |
| **Typical Size** | 512 × 512 to 2048 × 2048 pixels |
| **File Size** | 20 KB to 500 KB per image |
| **Compression** | JPEG (lossy) |

### Model Input Requirements

Our model resizes all images to:
- **Resolution:** 224 × 224 pixels
- **Color Space:** RGB (converted from grayscale)
- **Value Range:** 0-1 (normalized)

Resizing is automatic in the data pipeline.

### Image Quality

- **Original Quality:** High quality scans
- **Artifacts:** Some images contain:
  - Patient ID overlays
  - Hospital logos
  - Dates/timestamps
  - Measurement annotations
- **Processing:** Images are used as-is (no artifact removal)

---

## Data Characteristics

### Patient Demographics

The dataset includes:
- **Pediatric patients** (ages 1-5 years) - Primary cohort
- **Adult patients** (ages 20+)
- Both male and female patients
- Various radiographic techniques

### Clinical Context

**NORMAL Images:**
- Healthy lungs with no abnormalities
- Clear lung fields
- Normal heart size
- No focal consolidations

**PNEUMONIA Images:**
- Bacterial pneumonia (majority)
- Viral pneumonia (subset)
- Community-acquired pneumonia (CAP)
- Various severity levels

### Radiographic Variations

Images show natural variations:
- Different X-ray equipment/generators
- Various exposure levels
- Different patient positions:
  - Posteroanterior (PA) view
  - Anteroposterior (AP) view
  - Lateral views (some)
- Different inspiration levels (breathing depth)

---

## Data Validation

### Validation Script

The provided `prepare_data.py` script includes validation:

```bash
python training/prepare_data.py --output ./datasets/
```

This checks:
- ✓ All JPEG files are valid
- ✓ Images are readable
- ✓ Required folder structure exists
- ✓ Class distribution is correct

### Manual Validation

Check specific image:
```python
from PIL import Image

# Open and verify image
img = Image.open('chest_xray/train/NORMAL/image.jpeg')
print(f"Size: {img.size}")
print(f"Mode: {img.mode}")  # Should be 'L' for grayscale or 'RGB'
img.verify()  # Check file integrity
```

### Common Issues

**Issue: Images won't load**
- Cause: Corrupted JPEG file
- Solution: Delete and re-download from Kaggle

**Issue: Wrong folder structure**
- Cause: Incorrect extraction location
- Solution: Re-extract to correct location

**Issue: Missing classes**
- Cause: Incomplete download
- Solution: Re-download entire dataset

---

## Using Your Own Dataset

### Requirements

To use your own chest X-ray dataset, it must have:

1. **Folder Structure:**
   ```
   your_dataset/
   ├── train/
   │   ├── NORMAL/
   │   └── PNEUMONIA/
   ├── val/
   │   ├── NORMAL/
   │   └── PNEUMONIA/
   └── test/
       ├── NORMAL/
       └── PNEUMONIA/
   ```

2. **Image Format:**
   - JPEG or PNG format
   - Grayscale chest X-rays
   - Any resolution (resized to 224×224 automatically)

3. **Minimum Data:**
   - At least 100 images per class in training set
   - Ideally 500+ images per class for good results

4. **Data Quality:**
   - Images must be clear (not blurry)
   - No corrupted files
   - Consistent image type (all X-rays)

### Converting Custom Dataset

If your dataset has different structure:

```python
import os
import shutil
from pathlib import Path

# Example: Convert from different structure
source = Path('/path/to/your/images')
target = Path('./datasets/custom_chest_xray')

# Create target structure
for split in ['train', 'val', 'test']:
    for class_name in ['NORMAL', 'PNEUMONIA']:
        os.makedirs(target / split / class_name, exist_ok=True)

# Copy images (example - adjust paths as needed)
for image_path in (source / 'normal').glob('*.jpg'):
    dest = target / 'train' / 'NORMAL' / image_path.name
    shutil.copy2(image_path, dest)
```

### Training with Custom Dataset

```bash
python training/train.py --data_path ./datasets/custom_chest_xray --epochs 50
```

---

## Data Augmentation

### Applied During Training

The training pipeline applies augmentation to prevent overfitting:

**Augmentations Applied:**
- **Rotation:** ±20 degrees
- **Width Shift:** ±20% of width
- **Height Shift:** ±20% of height
- **Shear:** 15% shear range
- **Zoom:** ±20% zoom
- **Horizontal Flip:** Yes (realistic for X-rays)
- **Brightness:** 0.8 to 1.2x multiplier

### Why Augmentation?

- **Dataset Size:** Only ~5,000 images, needs augmentation
- **Overfitting Prevention:** More training variations
- **Real-World Robustness:** Handles different conditions
- **Medical Context:** Different positioning/exposure are realistic

### Augmentation Example Code

```python
from tensorflow.keras.preprocessing.image import ImageDataGenerator

augmentation = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.15,
    zoom_range=0.2,
    horizontal_flip=True,
    brightness_range=[0.8, 1.2],
    fill_mode='nearest'
)
```

### Validation Data

**No augmentation applied to validation/test data:**
- Only preprocessing (normalization)
- Ensures fair evaluation
- Represents real-world scenario

---

## Data Imbalance Handling

### Problem
- PNEUMONIA images: 4,656 (71%)
- NORMAL images: 1,818 (29%)
- Imbalance ratio: 2.56:1

### Solution: Focal Loss

Instead of standard cross-entropy, we use **Focal Loss**:

```python
class FocalLoss(tf.keras.losses.Loss):
    def __init__(self, gamma=2.0, alpha=0.25):
        self.gamma = gamma  # Focus parameter
        self.alpha = alpha  # Class balance parameter
```

**How it works:**
- Down-weights easy (well-classified) examples
- Up-weights hard (misclassified) examples
- Especially effective for imbalanced datasets
- Focuses learning on minority class (NORMAL)

### Results
- Better sensitivity (recall) on NORMAL class
- More balanced predictions
- Better precision-recall tradeoff

---

## Dataset Limitations & Biases

### Important Disclaimers

1. **Pediatric Dataset:**
   - Primarily children ages 1-5
   - May not generalize to adult patients
   - Different anatomy and presentation

2. **Geographic Bias:**
   - From specific hospital/region
   - Different equipment types
   - May not match your institution

3. **Limited Diversity:**
   - Specific equipment/techniques
   - Limited patient demographics
   - Missing some pneumonia types (e.g., COVID-19 era)

4. **Clinical Limitations:**
   - No clinical history included
   - No follow-up images
   - Single timepoint per patient

5. **Image Quality:**
   - Some artifacts present
   - Varying exposure levels
   - Not standardized intensity

### Recommendation

**This model should NOT be used for clinical diagnosis without:**
- Validation on your institutional data
- Comparison with radiologist readings
- Testing on current equipment
- Regulatory approval (FDA, etc.)

---

## Advanced Data Topics

### Class Weights

Alternative to Focal Loss (if not using):
```python
class_weight = {
    0: 1.0,  # NORMAL
    1: 0.39  # PNEUMONIA (less weight)
}
model.fit(..., class_weight=class_weight)
```

### Stratified Splitting

Ensures balanced splits:
```python
from sklearn.model_selection import train_test_split
train, test = train_test_split(data, stratify=labels)
```

### Cross-Validation

For robust evaluation:
```python
from sklearn.model_selection import StratifiedKFold
kfold = StratifiedKFold(n_splits=5)
```

---

## References

1. **Original Paper:**
   Kermany, D. S., et al. (2018). Cell, 172(5), 1122-1131.

2. **NIH Chest X-ray Dataset:**
   https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community

3. **Focal Loss Paper:**
   Lin, T. Y., et al. (2017). ICCV.

4. **DenseNet Paper:**
   Huang, G., et al. (2017). CVPR.

5. **Medical Imaging Preprocessing:**
   - Image Processing in Radiology - Bushberg et al.
   - Deep Learning in Medical Image Analysis - Greenspan et al.

---

**Last Updated:** 2025-05-03
**Version:** 1.0
**Dataset Version:** Kaggle Edition (2017-2018)
