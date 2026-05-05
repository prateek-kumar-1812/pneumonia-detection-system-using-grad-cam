"""
Data Preparation Script for Pneumonia Detection
===============================================

This script prepares the chest X-ray dataset for training.

Features:
- Download dataset from Kaggle (requires authentication)
- Organize data into train/val/test splits
- Validate image integrity
- Generate dataset statistics

Usage:
    # Option 1: Organize existing Kaggle dataset
    python prepare_data.py --source /path/to/downloaded/chest_xray --output ../datasets/

    # Option 2: Download from Kaggle (requires kaggle.json)
    python prepare_data.py --download --output ../datasets/

Dataset Info:
- Source: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
- Size: ~2GB
- Classes: NORMAL (1583 images), PNEUMONIA (4273 images)
- Format: JPEG
"""

import os
import shutil
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict


def validate_images(image_dir):
    """
    Validate that all images in a directory are valid JPEG files
    
    Args:
        image_dir: Directory containing images
        
    Returns:
        list: List of invalid image paths
    """
    invalid_images = []
    valid_count = 0
    
    for image_path in Path(image_dir).glob('*.jpeg'):
        try:
            with Image.open(image_path) as img:
                img.verify()
                valid_count += 1
        except Exception as e:
            print(f"[WARNING] Invalid image: {image_path} - {e}")
            invalid_images.append(str(image_path))
    
    print(f"[INFO] {valid_count} valid images found in {image_dir}")
    return invalid_images


def organize_dataset(source_path, output_path, val_split=0.1, test_split=0.2):
    """
    Organize Kaggle dataset into train/val/test structure
    
    Expected source structure:
        chest_xray/
        ├── train/
        │   ├── NORMAL/
        │   └── PNEUMONIA/
        ├── val/
        │   ├── NORMAL/
        │   └── PNEUMONIA/
        └── test/
            ├── NORMAL/
            └── PNEUMONIA/
    
    Output structure (same as input, validated and reorganized)
    
    Args:
        source_path: Path to source dataset
        output_path: Path to output dataset
        val_split: Fraction of training data for validation
        test_split: Fraction of training data for test set
    """
    
    print(f"[INFO] Organizing dataset from {source_path}")
    
    source_path = Path(source_path)
    output_path = Path(output_path)
    
    # Create output directories
    for split in ['train', 'val', 'test']:
        for class_name in ['NORMAL', 'PNEUMONIA']:
            os.makedirs(output_path / split / class_name, exist_ok=True)
    
    # Process existing splits
    dataset_stats = defaultdict(lambda: defaultdict(int))
    
    for split in ['train', 'val', 'test']:
        split_path = source_path / split
        if not split_path.exists():
            print(f"[WARNING] {split} directory not found at {split_path}")
            continue
        
        for class_name in ['NORMAL', 'PNEUMONIA']:
            class_path = split_path / class_name
            if not class_path.exists():
                continue
            
            print(f"\n[INFO] Processing {split}/{class_name}...")
            
            # Validate and copy images
            invalid_count = 0
            valid_count = 0
            
            for image_path in class_path.glob('*.jpeg'):
                try:
                    # Validate image
                    with Image.open(image_path) as img:
                        img.verify()
                    
                    # Copy to output
                    dest_path = output_path / split / class_name / image_path.name
                    shutil.copy2(image_path, dest_path)
                    valid_count += 1
                    dataset_stats[split][class_name] += 1
                    
                except Exception as e:
                    print(f"[WARNING] Skipping invalid image: {image_path.name}")
                    invalid_count += 1
            
            print(f"[INFO] Copied {valid_count} images, skipped {invalid_count} invalid images")
    
    # Print statistics
    print("\n" + "=" * 70)
    print("Dataset Organization Summary")
    print("=" * 70)
    
    total_images = 0
    for split in ['train', 'val', 'test']:
        print(f"\n{split.upper()} Split:")
        split_total = 0
        for class_name in ['NORMAL', 'PNEUMONIA']:
            count = dataset_stats[split][class_name]
            print(f"  {class_name:12}: {count:5} images")
            split_total += count
        print(f"  {'Total':12}: {split_total:5} images")
        total_images += split_total
    
    print(f"\n{'TOTAL':12}: {total_images:5} images")
    print("=" * 70)
    
    return dataset_stats


def validate_dataset_structure(dataset_path):
    """
    Validate that dataset has correct structure and all files are valid
    
    Args:
        dataset_path: Path to dataset root
        
    Returns:
        bool: True if dataset is valid
    """
    
    print(f"\n[INFO] Validating dataset structure at {dataset_path}")
    
    required_structure = {
        'train': ['NORMAL', 'PNEUMONIA'],
        'val': ['NORMAL', 'PNEUMONIA'],
        'test': ['NORMAL', 'PNEUMONIA']
    }
    
    dataset_path = Path(dataset_path)
    
    for split, classes in required_structure.items():
        split_path = dataset_path / split
        
        if not split_path.exists():
            print(f"[ERROR] Missing split: {split}")
            return False
        
        for class_name in classes:
            class_path = split_path / class_name
            
            if not class_path.exists():
                print(f"[ERROR] Missing class: {split}/{class_name}")
                return False
            
            # Count images
            image_count = len(list(class_path.glob('*.jpeg')))
            if image_count == 0:
                print(f"[ERROR] No images found in {split}/{class_name}")
                return False
            
            print(f"[OK] {split}/{class_name}: {image_count} images")
    
    print("\n[SUCCESS] Dataset structure is valid")
    return True


def download_from_kaggle(output_path):
    """
    Download dataset from Kaggle (requires authentication)
    
    Prerequisites:
    1. Install kaggle: pip install kaggle
    2. Download kaggle.json from https://www.kaggle.com/settings/account
    3. Place kaggle.json at ~/.kaggle/kaggle.json
    4. chmod 600 ~/.kaggle/kaggle.json (on Unix)
    
    Args:
        output_path: Path to save dataset
    """
    
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("[ERROR] Kaggle API not installed")
        print("[INFO] Install with: pip install kaggle")
        return False
    
    print("[INFO] Authenticating with Kaggle...")
    api = KaggleApi()
    api.authenticate()
    
    print(f"[INFO] Downloading dataset to {output_path}")
    os.makedirs(output_path, exist_ok=True)
    
    # Download dataset
    api.dataset_download_files(
        'paultimothymooney/chest-xray-pneumonia',
        path=output_path,
        unzip=True
    )
    
    print("[SUCCESS] Dataset downloaded successfully")
    return True


def main():
    """Main data preparation pipeline"""
    
    parser = argparse.ArgumentParser(
        description='Prepare chest X-ray dataset for training'
    )
    parser.add_argument(
        '--source',
        type=str,
        help='Path to source dataset (Kaggle download)'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download dataset from Kaggle (requires kaggle.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='../datasets/',
        help='Output path for organized dataset'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Chest X-ray Dataset Preparation")
    print("=" * 70)
    
    # Determine source
    if args.download:
        print("[INFO] Mode: Download from Kaggle")
        download_from_kaggle(os.path.join(args.output, 'chest_xray_raw'))
        source_path = os.path.join(args.output, 'chest_xray_raw', 'chest_xray')
    elif args.source:
        print(f"[INFO] Mode: Organize existing dataset")
        source_path = args.source
    else:
        print("[ERROR] Please provide either --source or --download flag")
        parser.print_help()
        return
    
    # Check if source exists
    if not os.path.exists(source_path):
        print(f"[ERROR] Source path not found: {source_path}")
        return
    
    # Organize dataset
    output_dataset_path = os.path.join(args.output, 'chest_xray')
    organize_dataset(source_path, output_dataset_path)
    
    # Validate
    if validate_dataset_structure(output_dataset_path):
        print(f"\n[SUCCESS] Dataset ready at: {output_dataset_path}")
        print("[INFO] Next step: Run training with:")
        print(f"       python train.py --data_path {output_dataset_path}")
    else:
        print("[ERROR] Dataset validation failed")


if __name__ == '__main__':
    main()
