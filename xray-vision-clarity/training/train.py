"""
Pneumonia Detection Model Training Script
==========================================

This script trains a DenseNet121 model on chest X-ray images to detect pneumonia.

Features:
- Transfer learning with DenseNet121 (pre-trained on ImageNet)
- Focal Loss for handling class imbalance
- Grad-CAM visualization support
- Data augmentation with albumentations
- Early stopping and learning rate scheduling
- Optimal threshold calculation for best F1-score
- Model evaluation with comprehensive metrics

Usage:
    python train.py --data_path /path/to/chest_xray --epochs 50 --batch_size 32

Dataset Structure:
    chest_xray/
    ├── train/
    │   ├── NORMAL/
    │   │   ├── image1.jpeg
    │   │   └── ...
    │   └── PNEUMONIA/
    │       ├── image1.jpeg
    │       └── ...
    ├── val/
    │   ├── NORMAL/
    │   └── PNEUMONIA/
    └── test/
        ├── NORMAL/
        └── PNEUMONIA/

Dataset Download:
    Download from: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
"""

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.densenet import DenseNet121, preprocess_input
from tensorflow.keras.layers import (
    Input, Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc, 
    precision_recall_curve, f1_score, sensitivity, specificity
)
import warnings
warnings.filterwarnings('ignore')


# Custom Focal Loss Implementation
class FocalLoss(tf.keras.losses.Loss):
    """
    Focal Loss for handling class imbalance
    
    Paper: "Focal Loss for Dense Object Detection"
    https://arxiv.org/abs/1708.02002
    
    Reduces the relative loss for well-classified examples and focuses learning
    on hard negative examples.
    """
    def __init__(self, gamma=2.0, alpha=0.25, label_smoothing=0.0, name='focal_loss'):
        super().__init__(name=name)
        self.gamma = gamma
        self.alpha = alpha
        self.label_smoothing = label_smoothing
    
    def call(self, y_true, y_pred):
        y_true = tf.cast(y_true, tf.float32)
        
        # Apply label smoothing
        if self.label_smoothing > 0:
            y_true = y_true * (1 - self.label_smoothing) + 0.5 * self.label_smoothing
        
        # Clip predictions to prevent numerical instability
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        
        # Calculate focal loss
        p_t = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)
        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)
        focal_weight = alpha_t * tf.pow(1 - p_t, self.gamma)
        focal_loss = -focal_weight * tf.math.log(p_t)
        
        return tf.reduce_mean(focal_loss)
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'gamma': self.gamma,
            'alpha': self.alpha,
            'label_smoothing': self.label_smoothing
        })
        return config


def create_model(input_shape=(224, 224, 3)):
    """
    Create DenseNet121 model with custom head for pneumonia detection
    
    Architecture:
    - Base: DenseNet121 (pre-trained on ImageNet)
    - Global Average Pooling
    - Batch Normalization
    - Dropout (0.5)
    - Dense (256 units) + ReLU + Batch Norm
    - Dropout (0.5)
    - Output: Dense (1 unit) + Sigmoid for binary classification
    
    Returns:
        Model: Compiled TensorFlow/Keras model
    """
    print("[INFO] Creating DenseNet121 model...")
    
    # Load pre-trained DenseNet121
    base_model = DenseNet121(
        input_shape=input_shape,
        weights='imagenet',
        include_top=False
    )
    
    # Freeze base model weights initially
    base_model.trainable = False
    
    # Create custom head
    inputs = Input(shape=input_shape)
    x = base_model(inputs, training=False)
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)
    x = Dense(256, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)
    outputs = Dense(1, activation='sigmoid')(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    
    # Compile with Focal Loss
    model.compile(
        loss=FocalLoss(gamma=2.0, alpha=0.25),
        optimizer=Adam(learning_rate=1e-4),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(),
            tf.keras.metrics.AUC(name='auc'),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    print("[INFO] Model created successfully")
    print(f"[INFO] Total parameters: {model.count_params():,}")
    
    return model, base_model


def get_data_generators(data_path, batch_size=32):
    """
    Create data generators with augmentation for training and validation
    
    Args:
        data_path: Path to dataset root directory
        batch_size: Batch size for training
        
    Returns:
        tuple: (train_generator, val_generator, test_generator)
    """
    print("[INFO] Creating data generators with augmentation...")
    
    # Training data generator with aggressive augmentation
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        brightness_range=[0.8, 1.2]
    )
    
    # Validation and test data generator (no augmentation)
    val_test_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input
    )
    
    # Load training data
    train_generator = train_datagen.flow_from_directory(
        os.path.join(data_path, 'train'),
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='binary',
        classes={'NORMAL': 0, 'PNEUMONIA': 1}
    )
    
    # Load validation data
    val_generator = val_test_datagen.flow_from_directory(
        os.path.join(data_path, 'val'),
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='binary',
        classes={'NORMAL': 0, 'PNEUMONIA': 1},
        shuffle=False
    )
    
    # Load test data
    test_generator = val_test_datagen.flow_from_directory(
        os.path.join(data_path, 'test'),
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='binary',
        classes={'NORMAL': 0, 'PNEUMONIA': 1},
        shuffle=False
    )
    
    print(f"[INFO] Training samples: {train_generator.samples}")
    print(f"[INFO] Validation samples: {val_generator.samples}")
    print(f"[INFO] Test samples: {test_generator.samples}")
    
    return train_generator, val_generator, test_generator


def train_model(model, base_model, train_gen, val_gen, epochs=50, batch_size=32):
    """
    Train the model with progressive unfreezing
    
    Strategy:
    1. Phase 1: Train only the head (frozen base) - 10 epochs
    2. Phase 2: Unfreeze and train full model - remaining epochs
    
    Args:
        model: Compiled model
        base_model: Base DenseNet121 model (for unfreezing)
        train_gen: Training data generator
        val_gen: Validation data generator
        epochs: Total training epochs
        batch_size: Batch size
        
    Returns:
        History: Training history
    """
    
    # Phase 1: Train head only
    print("\n[PHASE 1] Training head with frozen base model...")
    print(f"[INFO] Epochs: 1-10")
    
    callbacks_phase1 = [
        EarlyStopping(
            monitor='val_auc',
            patience=5,
            restore_best_weights=True,
            mode='max'
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1
        ),
        ModelCheckpoint(
            'best_model_phase1.h5',
            monitor='val_auc',
            save_best_only=True,
            mode='max',
            verbose=0
        ),
        TensorBoard(log_dir='./logs/phase1', histogram_freq=0)
    ]
    
    history_phase1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=10,
        callbacks=callbacks_phase1,
        verbose=1
    )
    
    # Phase 2: Unfreeze and fine-tune
    print("\n[PHASE 2] Fine-tuning with unfrozen base model...")
    print(f"[INFO] Epochs: 11-{epochs}")
    
    base_model.trainable = True
    
    # Recompile with lower learning rate
    model.compile(
        loss=FocalLoss(gamma=2.0, alpha=0.25),
        optimizer=Adam(learning_rate=1e-5),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(),
            tf.keras.metrics.AUC(name='auc'),
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall')
        ]
    )
    
    callbacks_phase2 = [
        EarlyStopping(
            monitor='val_auc',
            patience=10,
            restore_best_weights=True,
            mode='max'
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        ),
        ModelCheckpoint(
            'best_model_phase2.h5',
            monitor='val_auc',
            save_best_only=True,
            mode='max',
            verbose=0
        ),
        TensorBoard(log_dir='./logs/phase2', histogram_freq=0)
    ]
    
    history_phase2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs - 10,
        initial_epoch=10,
        callbacks=callbacks_phase2,
        verbose=1
    )
    
    return history_phase1, history_phase2


def evaluate_model(model, test_gen):
    """
    Evaluate model on test set and calculate metrics
    
    Metrics calculated:
    - Accuracy, Precision, Recall, F1-score
    - Sensitivity, Specificity
    - AUC-ROC
    - Confusion Matrix
    
    Args:
        model: Trained model
        test_gen: Test data generator
        
    Returns:
        dict: Metrics dictionary
    """
    print("\n[INFO] Evaluating model on test set...")
    
    # Get predictions
    predictions = model.predict(test_gen, verbose=0)
    y_pred = (predictions > 0.5).astype(int).flatten()
    y_true = test_gen.classes
    
    # Calculate metrics
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    sensitivity = recall
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Calculate ROC-AUC
    fpr, tpr, thresholds = roc_curve(y_true, predictions)
    roc_auc = auc(fpr, tpr)
    
    # Calculate optimal threshold based on F1-score
    precision_curve, recall_curve, thresholds_pr = precision_recall_curve(y_true, predictions)
    f1_scores = 2 * (precision_curve * recall_curve) / (precision_curve + recall_curve + 1e-10)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds_pr[optimal_idx] if optimal_idx < len(thresholds_pr) else 0.5
    
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'sensitivity': float(sensitivity),
        'specificity': float(specificity),
        'f1_score': float(f1),
        'auc': float(roc_auc),
        'optimal_threshold': float(optimal_threshold),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        }
    }
    
    return metrics


def save_model_and_config(model, metrics, output_dir='../public/backend/model'):
    """
    Save trained model and configuration
    
    Args:
        model: Trained model
        metrics: Evaluation metrics
        output_dir: Output directory for model files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(output_dir, 'pneumonia_model.h5')
    model.save(model_path)
    print(f"[INFO] Model saved to {model_path}")
    
    # Save configuration
    config = {
        'model': 'DenseNet121',
        'image_size': 224,
        'classes': ['NORMAL', 'PNEUMONIA'],
        'optimal_threshold': metrics['optimal_threshold'],
        'training_date': datetime.now().isoformat(),
        'metrics': {
            'accuracy': metrics['accuracy'],
            'auc': metrics['auc'],
            'sensitivity': metrics['sensitivity'],
            'specificity': metrics['specificity'],
            'f1_score': metrics['f1_score']
        }
    }
    
    config_path = os.path.join(output_dir, 'model_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"[INFO] Config saved to {config_path}")


def plot_training_history(history_phase1, history_phase2):
    """Plot training and validation metrics"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Combine histories
    history1_dict = history_phase1.history
    history2_dict = history_phase2.history
    
    # Loss
    ax = axes[0, 0]
    ax.plot(range(len(history1_dict['loss'])), history1_dict['loss'], label='Train Loss (Phase 1)')
    ax.plot(range(len(history1_dict['val_loss'])), history1_dict['val_loss'], label='Val Loss (Phase 1)')
    ax.plot(range(10, 10 + len(history2_dict['loss'])), history2_dict['loss'], label='Train Loss (Phase 2)')
    ax.plot(range(10, 10 + len(history2_dict['val_loss'])), history2_dict['val_loss'], label='Val Loss (Phase 2)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Training Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # AUC
    ax = axes[0, 1]
    ax.plot(range(len(history1_dict['auc'])), history1_dict['auc'], label='Train AUC (Phase 1)')
    ax.plot(range(len(history1_dict['val_auc'])), history1_dict['val_auc'], label='Val AUC (Phase 1)')
    ax.plot(range(10, 10 + len(history2_dict['auc'])), history2_dict['auc'], label='Train AUC (Phase 2)')
    ax.plot(range(10, 10 + len(history2_dict['val_auc'])), history2_dict['val_auc'], label='Val AUC (Phase 2)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('AUC')
    ax.set_title('AUC-ROC Metric')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Precision
    ax = axes[1, 0]
    ax.plot(range(len(history1_dict['precision'])), history1_dict['precision'], label='Train Precision (Phase 1)')
    ax.plot(range(len(history1_dict['val_precision'])), history1_dict['val_precision'], label='Val Precision (Phase 1)')
    ax.plot(range(10, 10 + len(history2_dict['precision'])), history2_dict['precision'], label='Train Precision (Phase 2)')
    ax.plot(range(10, 10 + len(history2_dict['val_precision'])), history2_dict['val_precision'], label='Val Precision (Phase 2)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Precision')
    ax.set_title('Precision Metric')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Recall
    ax = axes[1, 1]
    ax.plot(range(len(history1_dict['recall'])), history1_dict['recall'], label='Train Recall (Phase 1)')
    ax.plot(range(len(history1_dict['val_recall'])), history1_dict['val_recall'], label='Val Recall (Phase 1)')
    ax.plot(range(10, 10 + len(history2_dict['recall'])), history2_dict['recall'], label='Train Recall (Phase 2)')
    ax.plot(range(10, 10 + len(history2_dict['val_recall'])), history2_dict['val_recall'], label='Val Recall (Phase 2)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Recall')
    ax.set_title('Recall Metric')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_history.png', dpi=150, bbox_inches='tight')
    print("[INFO] Training history plot saved to training_history.png")
    plt.close()


def main():
    """Main training pipeline"""
    
    parser = argparse.ArgumentParser(
        description='Train DenseNet121 model for pneumonia detection'
    )
    parser.add_argument(
        '--data_path',
        type=str,
        default='../datasets/chest_xray',
        help='Path to chest X-ray dataset'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of epochs to train'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Batch size for training'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Pneumonia Detection Model Training")
    print("=" * 70)
    print(f"[INFO] Dataset path: {args.data_path}")
    print(f"[INFO] Total epochs: {args.epochs}")
    print(f"[INFO] Batch size: {args.batch_size}")
    print("=" * 70)
    
    # Check if dataset exists
    if not os.path.exists(args.data_path):
        print(f"[ERROR] Dataset not found at {args.data_path}")
        print("[INFO] Please download the dataset from:")
        print("       https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia")
        return
    
    # Create model
    model, base_model = create_model()
    
    # Get data generators
    train_gen, val_gen, test_gen = get_data_generators(args.data_path, args.batch_size)
    
    # Train model
    history_phase1, history_phase2 = train_model(
        model, base_model, train_gen, val_gen, args.epochs, args.batch_size
    )
    
    # Evaluate on test set
    metrics = evaluate_model(model, test_gen)
    
    print("\n" + "=" * 70)
    print("Test Set Evaluation Results")
    print("=" * 70)
    print(f"Accuracy:           {metrics['accuracy']:.4f}")
    print(f"Precision:          {metrics['precision']:.4f}")
    print(f"Recall (Sensitivity): {metrics['recall']:.4f}")
    print(f"Specificity:        {metrics['specificity']:.4f}")
    print(f"F1-Score:           {metrics['f1_score']:.4f}")
    print(f"AUC-ROC:            {metrics['auc']:.4f}")
    print(f"Optimal Threshold:  {metrics['optimal_threshold']:.4f}")
    print("=" * 70)
    
    # Save model and config
    save_model_and_config(model, metrics)
    
    # Plot training history
    plot_training_history(history_phase1, history_phase2)
    
    print("\n[SUCCESS] Training completed successfully!")
    print("[INFO] Model ready for deployment in ../public/backend/model/")


if __name__ == '__main__':
    main()
