"""
Flask Backend for Pneumonia Detection API
==========================================
This file should be run separately from the React frontend.

Setup Instructions:
1. cd public/backend
2. pip install -r requirements.txt
3. python app.py

The server will run on http://localhost:5000
"""

import os
import io
import json
import base64
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import cv2

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
MODEL_PATH = os.path.join(MODEL_DIR, 'pneumonia_model.h5')
CONFIG_PATH = os.path.join(MODEL_DIR, 'model_config.json')
IMG_SIZE = (224, 224)
CLASS_NAMES = ['NORMAL', 'PNEUMONIA']
DEFAULT_THRESHOLD = 0.5

# Global variables
model = None
model_config = None
optimal_threshold = DEFAULT_THRESHOLD


class FocalLoss(tf.keras.losses.Loss):
    """Focal Loss - must match training definition"""
    def __init__(self, gamma=2.0, alpha=0.25, label_smoothing=0.0, name='focal_loss'):
        super().__init__(name=name)
        self.gamma = gamma
        self.alpha = alpha
        self.label_smoothing = label_smoothing
    
    def call(self, y_true, y_pred):
        y_true = tf.cast(y_true, tf.float32)
        if self.label_smoothing > 0:
            y_true = y_true * (1 - self.label_smoothing) + 0.5 * self.label_smoothing
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        p_t = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)
        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)
        focal_loss = -alpha_t * tf.pow(1 - p_t, self.gamma) * tf.math.log(p_t)
        return tf.reduce_mean(focal_loss)


def load_model_config():
    """Load model configuration including optimal threshold"""
    global model_config, optimal_threshold
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            model_config = json.load(f)
        optimal_threshold = model_config.get('optimal_threshold', DEFAULT_THRESHOLD)
        print(f"Model config loaded. Using optimal threshold: {optimal_threshold:.3f}")
        print(f"Model metrics: AUC={model_config['metrics']['auc']:.4f}, "
              f"Sensitivity={model_config['metrics']['sensitivity']:.4f}, "
              f"Specificity={model_config['metrics']['specificity']:.4f}")
    else:
        print(f"Warning: Config not found at {CONFIG_PATH}. Using default threshold: {DEFAULT_THRESHOLD}")
        optimal_threshold = DEFAULT_THRESHOLD


def load_pneumonia_model():
    """Load the trained model with custom objects"""
    global model
    if model is None:
        if os.path.exists(MODEL_PATH):
            # Load with custom loss function
            model = load_model(
                MODEL_PATH,
                custom_objects={'FocalLoss': FocalLoss}
            )
            print(f"Model loaded from {MODEL_PATH}")
        else:
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Please train the model first using training/train.py"
            )
    return model


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image for model prediction"""
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to model input size
    image = image.resize(IMG_SIZE)
    
    # Convert to array and preprocess
    img_array = img_to_array(image)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0  # Normalize
    
    return img_array


def generate_gradcam(model, img_array: np.ndarray, class_idx: int) -> np.ndarray:
    """Generate Grad-CAM heatmap for the prediction"""
    # Get the last convolutional layer
    # For DenseNet121, use 'conv5_block16_concat'
    last_conv_layer_name = 'conv5_block16_concat'
    
    try:
        last_conv_layer = model.get_layer(last_conv_layer_name)
    except ValueError:
        # Fallback: find the last conv layer
        for layer in reversed(model.layers):
            if 'conv' in layer.name.lower():
                last_conv_layer = layer
                break
    
    # Create gradient model
    grad_model = tf.keras.Model(
        inputs=[model.inputs],
        outputs=[last_conv_layer.output, model.output]
    )
    
    # Compute gradients
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        loss = predictions[:, class_idx]
    
    grads = tape.gradient(loss, conv_outputs)
    
    # Global average pooling of gradients
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Weight the channels by corresponding gradients
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    # Normalize heatmap
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    heatmap = heatmap.numpy()
    
    return heatmap


def create_heatmap_overlay(original_image: Image.Image, heatmap: np.ndarray) -> tuple:
    """Create colored heatmap and overlay on original image"""
    # Resize original image
    original = original_image.resize(IMG_SIZE)
    original_array = np.array(original)
    
    # Resize heatmap to match image size
    heatmap_resized = cv2.resize(heatmap, IMG_SIZE)
    
    # Apply colormap
    heatmap_colored = cv2.applyColorMap(
        np.uint8(255 * heatmap_resized), 
        cv2.COLORMAP_JET
    )
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    # Create overlay
    overlay = cv2.addWeighted(original_array, 0.6, heatmap_colored, 0.4, 0)
    
    return heatmap_colored, overlay


def image_to_base64(image_array: np.ndarray) -> str:
    """Convert numpy array to base64 string"""
    image = Image.fromarray(image_array.astype('uint8'))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'model_loaded': model is not None,
        'optimal_threshold': optimal_threshold,
        'config_loaded': model_config is not None
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict pneumonia from chest X-ray image
    
    Expects: multipart/form-data with 'file' field containing the image
    
    Returns: JSON with label, probability, gradcam, and overlay (base64 encoded)
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Load model
        model = load_pneumonia_model()
        
        # Read and preprocess image
        image = Image.open(file.stream)
        img_array = preprocess_image(image)
        
        # Make prediction
        prediction = model.predict(img_array, verbose=0)
        probability = float(prediction[0][0])
        
        # Use optimal threshold (not 0.5) for better accuracy
        class_idx = 1 if probability >= optimal_threshold else 0
        label = CLASS_NAMES[class_idx]
        
        # Calculate confidence based on distance from threshold
        if class_idx == 1:
            # PNEUMONIA: confidence based on how much above threshold
            confidence = min(100, (probability - optimal_threshold) / (1 - optimal_threshold) * 100 + 50)
        else:
            # NORMAL: confidence based on how much below threshold
            confidence = min(100, (optimal_threshold - probability) / optimal_threshold * 100 + 50)
        
        confidence = max(50, min(99, confidence))  # Clamp between 50-99
        
        # Generate Grad-CAM
        heatmap = generate_gradcam(model, img_array, class_idx)
        
        # Create visualizations
        heatmap_colored, overlay = create_heatmap_overlay(image, heatmap)
        
        # Calculate affected area percentage from Grad-CAM heatmap
        # Apply threshold to identify affected regions (50% of max intensity)
        threshold = 0.5 * np.max(heatmap)
        affected_pixels = np.sum(heatmap > threshold)
        total_pixels = heatmap.size
        affected_area_percentage = (affected_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Only show affected area for pneumonia predictions
        if class_idx == 0:  # PNEUMONIA class
            affected_area_percentage = float(affected_area_percentage)
        else:
            affected_area_percentage = 0.0
        
        # Convert to base64
        gradcam_base64 = image_to_base64(heatmap_colored)
        overlay_base64 = image_to_base64(overlay)
        
        return jsonify({
            'label': label,
            'probability': round(confidence, 2),
            'raw_probability': round(probability, 4),
            'threshold': round(optimal_threshold, 3),
            'gradcam': gradcam_base64,
            'overlay': overlay_base64,
            'affected_area_percentage': round(affected_area_percentage, 2)
        })
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


if __name__ == '__main__':
    # Load config first
    load_model_config()
    
    # Try to load model on startup
    try:
        load_pneumonia_model()
    except FileNotFoundError:
        print("Warning: Model not found. Please train the model first.")
    
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
