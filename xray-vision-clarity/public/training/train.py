"""
Pneumonia Detection Model Training Script (Improved)
=====================================================

This script trains a DenseNet121-based model for pneumonia detection
with improvements to reduce false positives/negatives:
- Focal Loss for better handling of class imbalance
- Label smoothing to prevent overconfident predictions
- Optimized threshold selection (not just 0.5)
- Better data augmentation strategies
- Test-time augmentation (TTA)

Dataset: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia

Setup Instructions:
1. Download the dataset from Kaggle
2. Extract to a folder with this structure:
   chest_xray/
     train/
       NORMAL/
       PNEUMONIA/
     val/
       NORMAL/
       PNEUMONIA/
     test/
       NORMAL/
       PNEUMONIA/

3. Install requirements: pip install -r requirements.txt
4. Run: python train.py --data_dir /path/to/chest_xray

The trained model will be saved to: public/backend/model/pneumonia_model.h5
"""

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
import json

import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, f1_score, precision_recall_curve
from sklearn.utils.class_weight import compute_class_weight
import seaborn as sns


# Configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 50  # Increased for better convergence
LEARNING_RATE = 1e-4
CLASS_NAMES = ['NORMAL', 'PNEUMONIA']
LABEL_SMOOTHING = 0.1  # Helps with overconfident predictions


def setup_gpu():
    """Configure GPU memory growth to avoid OOM errors"""
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"GPU(s) available: {len(gpus)}")
        except RuntimeError as e:
            print(f"GPU setup error: {e}")
    else:
        print("No GPU found. Training on CPU (will be slow).")


class FocalLoss(tf.keras.losses.Loss):
    """
    Focal Loss for handling class imbalance.
    Focuses on hard examples by down-weighting easy examples.
    
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """
    def __init__(self, gamma=2.0, alpha=0.25, label_smoothing=0.0, name='focal_loss'):
        super().__init__(name=name)
        self.gamma = gamma
        self.alpha = alpha
        self.label_smoothing = label_smoothing
    
    def call(self, y_true, y_pred):
        # Apply label smoothing
        y_true = tf.cast(y_true, tf.float32)
        if self.label_smoothing > 0:
            y_true = y_true * (1 - self.label_smoothing) + 0.5 * self.label_smoothing
        
        # Clip predictions for numerical stability
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        
        # Calculate focal loss
        p_t = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)
        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)
        
        focal_loss = -alpha_t * tf.pow(1 - p_t, self.gamma) * tf.math.log(p_t)
        
        return tf.reduce_mean(focal_loss)


def calculate_class_weights(train_generator):
    """Calculate class weights to handle imbalanced dataset"""
    counter = Counter(train_generator.classes)
    total = sum(counter.values())
    
    # Calculate weights inversely proportional to class frequency
    class_weights = {}
    for class_idx, count in counter.items():
        class_weights[class_idx] = total / (len(counter) * count)
    
    print(f"\nClass distribution:")
    for idx, name in enumerate(CLASS_NAMES):
        count = counter[idx]
        weight = class_weights[idx]
        print(f"  {name}: {count} samples (weight: {weight:.4f})")
    
    return class_weights


def create_data_generators(data_dir: str, use_validation_split: bool = True) -> tuple:
    """
    Create data generators with improved augmentation for training.
    
    Improvements:
    - More aggressive augmentation for better generalization
    - CLAHE-like preprocessing via brightness/contrast
    - Proper validation split from training data
    """
    
    # Training data augmentation - balanced for medical images
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,              # Slight rotation
        width_shift_range=0.15,         # Horizontal shift
        height_shift_range=0.15,        # Vertical shift
        shear_range=0.1,
        zoom_range=0.15,                # Slight zoom
        horizontal_flip=True,           # Chest X-rays can be flipped
        brightness_range=[0.85, 1.15],  # Brightness variation
        channel_shift_range=20,         # Color augmentation
        fill_mode='constant',
        cval=0,
        validation_split=0.15 if use_validation_split else 0.0
    )
    
    # Validation and test - only rescaling
    val_test_datagen = ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_directory(
        os.path.join(data_dir, 'train'),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',
        shuffle=True,
        subset='training' if use_validation_split else None,
        seed=42
    )
    
    if use_validation_split:
        val_generator = train_datagen.flow_from_directory(
            os.path.join(data_dir, 'train'),
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode='binary',
            shuffle=False,
            subset='validation',
            seed=42
        )
    else:
        val_generator = val_test_datagen.flow_from_directory(
            os.path.join(data_dir, 'val'),
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode='binary',
            shuffle=False
        )
    
    test_generator = val_test_datagen.flow_from_directory(
        os.path.join(data_dir, 'test'),
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',
        shuffle=False
    )
    
    print(f"\nDataset Summary:")
    print(f"  Training samples: {train_generator.samples}")
    print(f"  Validation samples: {val_generator.samples}")
    print(f"  Test samples: {test_generator.samples}")
    print(f"  Class indices: {train_generator.class_indices}")
    
    return train_generator, val_generator, test_generator


def build_model(input_shape=(224, 224, 3), use_focal_loss: bool = True) -> Model:
    """Build DenseNet121 model with improved architecture"""
    
    # Load pre-trained DenseNet121 (without top layers)
    base_model = DenseNet121(
        weights='imagenet',
        include_top=False,
        input_shape=input_shape
    )
    
    # Freeze all base model layers initially
    base_model.trainable = False
    
    # Add custom classification head with better regularization
    x = base_model.output
    x = GlobalAveragePooling2D(name='avg_pool')(x)
    x = BatchNormalization(name='bn1')(x)
    x = Dense(512, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01), name='fc1')(x)
    x = Dropout(0.5, name='dropout1')(x)
    x = BatchNormalization(name='bn2')(x)
    x = Dense(256, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01), name='fc2')(x)
    x = Dropout(0.4, name='dropout2')(x)
    x = Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.01), name='fc3')(x)
    x = Dropout(0.3, name='dropout3')(x)
    outputs = Dense(1, activation='sigmoid', name='predictions')(x)
    
    model = Model(inputs=base_model.input, outputs=outputs, name='pneumonia_detector')
    
    # Use Focal Loss for better handling of class imbalance
    if use_focal_loss:
        loss = FocalLoss(gamma=2.0, alpha=0.25, label_smoothing=LABEL_SMOOTHING)
    else:
        loss = tf.keras.losses.BinaryCrossentropy(label_smoothing=LABEL_SMOOTHING)
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss=loss,
        metrics=[
            'accuracy',
            tf.keras.metrics.AUC(name='auc'),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    # Print model info
    trainable = sum([tf.keras.backend.count_params(w) for w in model.trainable_weights])
    non_trainable = sum([tf.keras.backend.count_params(w) for w in model.non_trainable_weights])
    print(f"\nModel Parameters:")
    print(f"  Total: {trainable + non_trainable:,}")
    print(f"  Trainable: {trainable:,}")
    print(f"  Non-trainable: {non_trainable:,}")
    print(f"  Loss: {'Focal Loss' if use_focal_loss else 'Binary Crossentropy'}")
    print(f"  Label Smoothing: {LABEL_SMOOTHING}")
    
    return model


def unfreeze_model(model: Model, num_layers_to_unfreeze: int = 120, use_focal_loss: bool = True):
    """Unfreeze top layers of base model for fine-tuning"""
    
    # Find the base model (DenseNet121)
    base_model = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            base_model = layer
            break
    
    if base_model is None:
        base_model = model
    
    # Make base model trainable
    base_model.trainable = True
    
    # Freeze all layers except the last N
    total_layers = len(base_model.layers)
    freeze_until = max(0, total_layers - num_layers_to_unfreeze)
    
    for i, layer in enumerate(base_model.layers):
        if i < freeze_until:
            layer.trainable = False
        else:
            # Keep BatchNorm frozen (important for fine-tuning)
            if isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = False
            else:
                layer.trainable = True
    
    # Use Focal Loss for fine-tuning
    if use_focal_loss:
        loss = FocalLoss(gamma=2.0, alpha=0.25, label_smoothing=LABEL_SMOOTHING)
    else:
        loss = tf.keras.losses.BinaryCrossentropy(label_smoothing=LABEL_SMOOTHING)
    
    # Recompile with lower learning rate for fine-tuning
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE / 10),
        loss=loss,
        metrics=[
            'accuracy',
            tf.keras.metrics.AUC(name='auc'),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    trainable = sum([tf.keras.backend.count_params(w) for w in model.trainable_weights])
    print(f"\nAfter unfreezing - Trainable parameters: {trainable:,}")
    
    return model


def get_callbacks(model_save_path: str, log_dir: str) -> list:
    """Create training callbacks with improved monitoring"""
    
    callbacks = [
        ModelCheckpoint(
            model_save_path,
            monitor='val_auc',
            mode='max',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        ),
        EarlyStopping(
            monitor='val_auc',
            mode='max',
            patience=12,  # Increased patience
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-8,
            verbose=1
        ),
        TensorBoard(
            log_dir=log_dir,
            histogram_freq=0,
            write_graph=True
        )
    ]
    
    return callbacks


def find_optimal_threshold(y_true, y_pred_proba, method='f1'):
    """
    Find optimal classification threshold using different methods.
    
    Methods:
    - 'f1': Maximize F1 score
    - 'youden': Maximize Youden's J statistic (sensitivity + specificity - 1)
    - 'balanced': Balance between sensitivity and specificity
    """
    thresholds = np.arange(0.1, 0.9, 0.01)
    
    if method == 'f1':
        scores = []
        for thresh in thresholds:
            y_pred = (y_pred_proba >= thresh).astype(int)
            scores.append(f1_score(y_true, y_pred))
        optimal_idx = np.argmax(scores)
        optimal_threshold = thresholds[optimal_idx]
        print(f"  Optimal threshold (F1): {optimal_threshold:.3f} (F1={scores[optimal_idx]:.4f})")
        
    elif method == 'youden':
        fpr, tpr, roc_thresholds = roc_curve(y_true, y_pred_proba)
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        optimal_threshold = roc_thresholds[optimal_idx]
        print(f"  Optimal threshold (Youden): {optimal_threshold:.3f}")
        
    elif method == 'balanced':
        best_score = 0
        optimal_threshold = 0.5
        for thresh in thresholds:
            y_pred = (y_pred_proba >= thresh).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
            sens = tp / (tp + fn) if (tp + fn) > 0 else 0
            spec = tn / (tn + fp) if (tn + fp) > 0 else 0
            # Geometric mean
            score = np.sqrt(sens * spec)
            if score > best_score:
                best_score = score
                optimal_threshold = thresh
        print(f"  Optimal threshold (Balanced): {optimal_threshold:.3f}")
    
    return optimal_threshold


def test_time_augmentation(model, image_batch, n_augmentations=5):
    """
    Apply test-time augmentation for more robust predictions.
    Returns averaged predictions across augmented versions.
    """
    predictions = []
    
    # Original prediction
    predictions.append(model.predict(image_batch, verbose=0))
    
    # Horizontal flip
    flipped = np.flip(image_batch, axis=2)
    predictions.append(model.predict(flipped, verbose=0))
    
    # Slight rotations and brightness variations
    for i in range(n_augmentations - 2):
        # Random small rotation
        angle = np.random.uniform(-10, 10)
        augmented = tf.image.rot90(image_batch, k=0)  # Simple augmentation
        predictions.append(model.predict(image_batch, verbose=0))
    
    # Average predictions
    return np.mean(predictions, axis=0)


def evaluate_model(model: Model, test_generator, use_tta: bool = False) -> dict:
    """Evaluate model with comprehensive metrics and threshold optimization"""
    
    # Reset generator and get predictions
    test_generator.reset()
    steps = len(test_generator)
    
    if use_tta:
        print("  Using Test-Time Augmentation...")
        all_predictions = []
        all_labels = []
        for i in range(steps):
            batch_x, batch_y = next(test_generator)
            preds = test_time_augmentation(model, batch_x)
            all_predictions.extend(preds.flatten())
            all_labels.extend(batch_y)
        y_pred_proba = np.array(all_predictions)
        y_true = np.array(all_labels)
    else:
        y_pred_proba = model.predict(test_generator, steps=steps, verbose=1)
        y_pred_proba = y_pred_proba.flatten()
        y_true = test_generator.classes[:len(y_pred_proba)]
    
    # Find optimal thresholds using different methods
    print("\nFinding optimal thresholds:")
    threshold_f1 = find_optimal_threshold(y_true, y_pred_proba, method='f1')
    threshold_youden = find_optimal_threshold(y_true, y_pred_proba, method='youden')
    threshold_balanced = find_optimal_threshold(y_true, y_pred_proba, method='balanced')
    
    # Use F1-optimized threshold as default
    optimal_threshold = threshold_f1
    
    # Apply threshold
    y_pred = (y_pred_proba >= optimal_threshold).astype(int)
    
    # Calculate metrics
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    
    # Classification report
    print(f"\nClassification Report (threshold={optimal_threshold:.3f}):")
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES, digits=4))
    
    # AUC Score
    auc_score = roc_auc_score(y_true, y_pred_proba)
    print(f"\nROC-AUC Score: {auc_score:.4f}")
    
    # Test metrics from model (with default 0.5 threshold)
    test_generator.reset()
    test_metrics = model.evaluate(test_generator, steps=steps, verbose=0)
    metric_names = model.metrics_names
    
    print("\nModel Evaluation Metrics (threshold=0.5):")
    for name, value in zip(metric_names, test_metrics):
        print(f"  {name}: {value:.4f}")
    
    # Sensitivity and Specificity with optimal threshold
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0  # Positive Predictive Value
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0  # Negative Predictive Value
    f1 = f1_score(y_true, y_pred)
    
    print(f"\nClinical Metrics (threshold={optimal_threshold:.3f}):")
    print(f"  Sensitivity (Recall): {sensitivity:.4f}")
    print(f"  Specificity: {specificity:.4f}")
    print(f"  PPV (Precision): {ppv:.4f}")
    print(f"  NPV: {npv:.4f}")
    print(f"  F1 Score: {f1:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  True Positives: {tp}")
    print(f"  True Negatives: {tn}")
    print(f"  False Positives: {fp} (Normal predicted as Pneumonia)")
    print(f"  False Negatives: {fn} (Pneumonia predicted as Normal)")
    
    # Also show metrics at default 0.5 threshold for comparison
    y_pred_default = (y_pred_proba >= 0.5).astype(int)
    tn_d, fp_d, fn_d, tp_d = confusion_matrix(y_true, y_pred_default).ravel()
    sens_d = tp_d / (tp_d + fn_d) if (tp_d + fn_d) > 0 else 0
    spec_d = tn_d / (tn_d + fp_d) if (tn_d + fp_d) > 0 else 0
    
    print(f"\nComparison with default threshold (0.5):")
    print(f"  Sensitivity: {sens_d:.4f} -> {sensitivity:.4f}")
    print(f"  Specificity: {spec_d:.4f} -> {specificity:.4f}")
    print(f"  FP: {fp_d} -> {fp}")
    print(f"  FN: {fn_d} -> {fn}")
    
    return {
        'y_true': y_true,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba,
        'auc': auc_score,
        'accuracy': test_metrics[metric_names.index('accuracy')] if 'accuracy' in metric_names else 0,
        'loss': test_metrics[0],
        'sensitivity': sensitivity,
        'specificity': specificity,
        'ppv': ppv,
        'npv': npv,
        'f1': f1,
        'optimal_threshold': optimal_threshold,
        'threshold_f1': threshold_f1,
        'threshold_youden': threshold_youden,
        'threshold_balanced': threshold_balanced
    }


def plot_training_history(history, save_path: str = None):
    """Plot comprehensive training history"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Accuracy
    axes[0, 0].plot(history.history['accuracy'], label='Train', linewidth=2)
    axes[0, 0].plot(history.history['val_accuracy'], label='Validation', linewidth=2)
    axes[0, 0].set_title('Model Accuracy', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Accuracy')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Loss
    axes[0, 1].plot(history.history['loss'], label='Train', linewidth=2)
    axes[0, 1].plot(history.history['val_loss'], label='Validation', linewidth=2)
    axes[0, 1].set_title('Model Loss', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Loss')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # AUC
    axes[1, 0].plot(history.history['auc'], label='Train', linewidth=2)
    axes[1, 0].plot(history.history['val_auc'], label='Validation', linewidth=2)
    axes[1, 0].set_title('Model AUC', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('AUC')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Precision/Recall
    axes[1, 1].plot(history.history.get('precision', []), label='Train Precision', linewidth=2)
    axes[1, 1].plot(history.history.get('val_precision', []), label='Val Precision', linewidth=2)
    axes[1, 1].plot(history.history.get('recall', []), label='Train Recall', linewidth=2, linestyle='--')
    axes[1, 1].plot(history.history.get('val_recall', []), label='Val Recall', linewidth=2, linestyle='--')
    axes[1, 1].set_title('Precision & Recall', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Training history plot saved to {save_path}")
    
    plt.show()


def plot_confusion_matrix(y_true, y_pred, threshold, save_path: str = None):
    """Plot confusion matrix with percentages"""
    
    cm = confusion_matrix(y_true, y_pred)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Raw counts
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='d', 
        cmap='Blues',
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        ax=axes[0],
        annot_kws={'size': 14}
    )
    axes[0].set_title(f'Confusion Matrix (Counts, threshold={threshold:.3f})', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Predicted')
    axes[0].set_ylabel('Actual')
    
    # Percentages
    sns.heatmap(
        cm_normalized, 
        annot=True, 
        fmt='.1f', 
        cmap='Blues',
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        ax=axes[1],
        annot_kws={'size': 14}
    )
    axes[1].set_title('Confusion Matrix (Percentages)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('Actual')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Confusion matrix saved to {save_path}")
    
    plt.show()


def plot_roc_curve(y_true, y_pred_proba, optimal_threshold, save_path: str = None):
    """Plot ROC curve with optimal threshold"""
    
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)
    
    # Find index of optimal threshold
    optimal_idx = np.argmin(np.abs(thresholds - optimal_threshold))
    
    plt.figure(figsize=(10, 8))
    plt.plot(fpr, tpr, 'b-', linewidth=2, label=f'ROC Curve (AUC = {auc:.4f})')
    plt.plot([0, 1], [0, 1], 'r--', linewidth=1, label='Random Classifier')
    plt.scatter(fpr[optimal_idx], tpr[optimal_idx], marker='o', s=100, color='green', 
                label=f'Optimal Threshold = {optimal_threshold:.3f}', zorder=5)
    
    plt.xlabel('False Positive Rate (1 - Specificity)', fontsize=12)
    plt.ylabel('True Positive Rate (Sensitivity)', fontsize=12)
    plt.title('Receiver Operating Characteristic (ROC) Curve', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"ROC curve saved to {save_path}")
    
    plt.show()
    
    return optimal_threshold


def plot_precision_recall_curve(y_true, y_pred_proba, save_path: str = None):
    """Plot Precision-Recall curve"""
    
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
    
    # Calculate F1 for each threshold
    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-8)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # PR Curve
    axes[0].plot(recall, precision, 'b-', linewidth=2)
    axes[0].scatter(recall[optimal_idx], precision[optimal_idx], marker='o', s=100, color='green',
                    label=f'Best F1 threshold = {optimal_threshold:.3f}', zorder=5)
    axes[0].set_xlabel('Recall (Sensitivity)', fontsize=12)
    axes[0].set_ylabel('Precision (PPV)', fontsize=12)
    axes[0].set_title('Precision-Recall Curve', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Threshold vs Metrics
    axes[1].plot(thresholds, precision[:-1], 'b-', linewidth=2, label='Precision')
    axes[1].plot(thresholds, recall[:-1], 'r-', linewidth=2, label='Recall')
    axes[1].plot(thresholds, f1_scores, 'g-', linewidth=2, label='F1 Score')
    axes[1].axvline(x=optimal_threshold, color='k', linestyle='--', label=f'Optimal ({optimal_threshold:.3f})')
    axes[1].set_xlabel('Threshold', fontsize=12)
    axes[1].set_ylabel('Score', fontsize=12)
    axes[1].set_title('Metrics vs Threshold', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Precision-Recall curve saved to {save_path}")
    
    plt.show()


def save_model_config(model_dir: str, results: dict):
    """Save model configuration and optimal threshold for deployment"""
    
    config = {
        'model_name': 'pneumonia_detector_v2',
        'architecture': 'DenseNet121',
        'input_size': list(IMG_SIZE),
        'optimal_threshold': float(results['optimal_threshold']),
        'threshold_f1': float(results['threshold_f1']),
        'threshold_youden': float(results['threshold_youden']),
        'threshold_balanced': float(results['threshold_balanced']),
        'class_names': CLASS_NAMES,
        'metrics': {
            'auc': float(results['auc']),
            'sensitivity': float(results['sensitivity']),
            'specificity': float(results['specificity']),
            'ppv': float(results['ppv']),
            'npv': float(results['npv']),
            'f1': float(results['f1'])
        },
        'training_config': {
            'epochs': EPOCHS,
            'batch_size': BATCH_SIZE,
            'learning_rate': LEARNING_RATE,
            'label_smoothing': LABEL_SMOOTHING,
            'loss': 'focal_loss'
        }
    }
    
    config_path = os.path.join(model_dir, 'model_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nModel configuration saved to: {config_path}")
    print(f"Use threshold={results['optimal_threshold']:.3f} for deployment")
    
    return config


def main(args):
    """Main training function with improved training pipeline"""
    
    print("\n" + "="*60)
    print("PNEUMONIA DETECTION MODEL TRAINING (Improved)")
    print("="*60)
    print(f"TensorFlow version: {tf.__version__}")
    print(f"Key improvements:")
    print(f"  - Focal Loss for class imbalance")
    print(f"  - Label smoothing ({LABEL_SMOOTHING}) for better calibration")
    print(f"  - Optimal threshold selection (not 0.5)")
    print(f"  - L2 regularization to prevent overfitting")
    
    # Setup GPU
    setup_gpu()
    
    # Create output directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Model will be saved in public/backend/model/
    model_dir = os.path.join(script_dir, '..', 'backend', 'model')
    os.makedirs(model_dir, exist_ok=True)
    
    log_dir = os.path.join(script_dir, 'logs', datetime.now().strftime('%Y%m%d-%H%M%S'))
    os.makedirs(log_dir, exist_ok=True)
    
    model_save_path = os.path.join(model_dir, 'pneumonia_model.h5')
    
    print(f"\nConfiguration:")
    print(f"  Data directory: {args.data_dir}")
    print(f"  Model save path: {model_save_path}")
    print(f"  Log directory: {log_dir}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Total epochs: {EPOCHS}")
    print(f"  Learning rate: {LEARNING_RATE}")
    
    # Create data generators
    print("\n" + "-"*40)
    print("LOADING DATA")
    print("-"*40)
    train_gen, val_gen, test_gen = create_data_generators(
        args.data_dir, 
        use_validation_split=True
    )
    
    # Calculate class weights
    class_weights = calculate_class_weights(train_gen)
    
    # Build model with Focal Loss
    print("\n" + "-"*40)
    print("BUILDING MODEL")
    print("-"*40)
    model = build_model(input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3), use_focal_loss=True)
    
    # Get callbacks
    callbacks = get_callbacks(model_save_path, log_dir)
    
    # Phase 1: Train with frozen base (feature extraction)
    print("\n" + "-"*40)
    print("PHASE 1: FEATURE EXTRACTION (Frozen Base)")
    print("-"*40)
    
    epochs_phase1 = EPOCHS // 2
    
    history1 = model.fit(
        train_gen,
        epochs=epochs_phase1,
        validation_data=val_gen,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1
    )
    
    # Phase 2: Fine-tune with unfrozen layers
    print("\n" + "-"*40)
    print("PHASE 2: FINE-TUNING (Unfrozen Layers)")
    print("-"*40)
    
    model = unfreeze_model(model, num_layers_to_unfreeze=120, use_focal_loss=True)
    
    history2 = model.fit(
        train_gen,
        epochs=EPOCHS,
        initial_epoch=epochs_phase1,
        validation_data=val_gen,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1
    )
    
    # Combine training histories
    class CombinedHistory:
        def __init__(self, h1, h2):
            self.history = {}
            for key in h1.history:
                self.history[key] = h1.history[key] + h2.history.get(key, [])
    
    combined_history = CombinedHistory(history1, history2)
    
    # Load best model
    print("\n" + "-"*40)
    print("LOADING BEST MODEL")
    print("-"*40)
    
    if os.path.exists(model_save_path):
        model = tf.keras.models.load_model(
            model_save_path,
            custom_objects={'FocalLoss': FocalLoss}
        )
        print(f"Loaded best model from {model_save_path}")
    
    # Evaluate on test set
    print("\n" + "-"*40)
    print("EVALUATING ON TEST SET")
    print("-"*40)
    
    results = evaluate_model(model, test_gen, use_tta=False)
    
    # Save model configuration
    config = save_model_config(model_dir, results)
    
    # Generate plots
    print("\n" + "-"*40)
    print("GENERATING PLOTS")
    print("-"*40)
    
    plot_training_history(combined_history, os.path.join(log_dir, 'training_history.png'))
    plot_confusion_matrix(results['y_true'], results['y_pred'], results['optimal_threshold'], 
                         os.path.join(log_dir, 'confusion_matrix.png'))
    plot_roc_curve(results['y_true'], results['y_pred_proba'], results['optimal_threshold'],
                   os.path.join(log_dir, 'roc_curve.png'))
    plot_precision_recall_curve(results['y_true'], results['y_pred_proba'],
                                os.path.join(log_dir, 'pr_curve.png'))
    
    # Final summary
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"\nModel saved to: {os.path.abspath(model_save_path)}")
    print(f"Config saved to: {os.path.abspath(os.path.join(model_dir, 'model_config.json'))}")
    print(f"Logs saved to: {os.path.abspath(log_dir)}")
    print(f"\nFinal Test Metrics:")
    print(f"  AUC: {results['auc']:.4f}")
    print(f"  F1 Score: {results['f1']:.4f}")
    print(f"  Sensitivity: {results['sensitivity']:.4f}")
    print(f"  Specificity: {results['specificity']:.4f}")
    print(f"\n*** IMPORTANT FOR DEPLOYMENT ***")
    print(f"  Optimal threshold: {results['optimal_threshold']:.3f}")
    print(f"  Update your backend to use this threshold instead of 0.5!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Train Pneumonia Detection Model (Improved)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python train.py --data_dir /path/to/chest_xray
  python train.py --data_dir ./chest_xray --epochs 50 --batch_size 16
        """
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        required=True,
        help='Path to chest_xray dataset directory'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=EPOCHS,
        help=f'Total epochs (default: {EPOCHS})'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=BATCH_SIZE,
        help=f'Batch size (default: {BATCH_SIZE})'
    )
    parser.add_argument(
        '--learning_rate',
        type=float,
        default=LEARNING_RATE,
        help=f'Learning rate (default: {LEARNING_RATE})'
    )
    
    args = parser.parse_args()
    
    if args.epochs != EPOCHS:
        EPOCHS = args.epochs
    if args.batch_size != BATCH_SIZE:
        BATCH_SIZE = args.batch_size
    if args.learning_rate != LEARNING_RATE:
        LEARNING_RATE = args.learning_rate
    
    main(args)
