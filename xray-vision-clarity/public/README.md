# Explainable Pneumonia Detection Using Deep Learning (with Grad-CAM)

A complete solution for detecting pneumonia in chest X-ray images using deep learning with visual explanations powered by Grad-CAM.

⚠️ **DISCLAIMER**: This project is for **educational and research purposes only**. It is NOT intended for clinical diagnosis or medical decision-making. Always consult qualified healthcare professionals for medical advice.

## 🎯 Features

- **AI-Powered Detection**: DenseNet121 model trained on chest X-ray images
- **Visual Explanations**: Grad-CAM heatmaps showing which regions influenced the prediction
- **Clean UI**: Modern React frontend with drag-and-drop upload
- **REST API**: Flask backend for easy integration
- **Transfer Learning**: Pre-trained on ImageNet, fine-tuned for pneumonia detection

## 📁 Project Structure

```
project/
├── src/                          # React Frontend
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── HeroSection.tsx
│   │   ├── FileUpload.tsx
│   │   ├── LoadingAnalysis.tsx
│   │   ├── ResultsDisplay.tsx
│   │   └── Footer.tsx
│   ├── lib/
│   │   └── api.ts               # API client
│   └── pages/
│       └── Index.tsx            # Main page
│
├── public/
│   ├── backend/                 # Flask Backend
│   │   ├── app.py              # Flask API server
│   │   ├── requirements.txt    # Python dependencies
│   │   └── model/              # Model directory
│   │       └── pneumonia_model.h5  # Trained model (after training)
│   │
│   └── training/               # Model Training
│       ├── train.py           # Training script
│       └── requirements.txt   # Training dependencies
│
└── README.md
```

## 🚀 Quick Start

### 1. Train the Model

First, download the dataset from Kaggle:
- Dataset: [Chest X-Ray Images (Pneumonia)](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia)

```bash
# Navigate to training directory
cd public/training

# Install dependencies
pip install -r requirements.txt

# Train the model (replace path with your dataset location)
python train.py --data_dir /path/to/chest_xray
```

The trained model will be saved to `public/backend/model/pneumonia_model.h5`

### 2. Start the Backend

```bash
# Navigate to backend directory
cd public/backend

# Install dependencies
pip install -r requirements.txt

# Start Flask server
python app.py
```

The backend will run at `http://localhost:5000`

### 3. Start the Frontend

```bash
# From project root
npm install
npm run dev
```

The frontend will run at `http://localhost:8080`

### 4. Configure API URL (Optional)

If your Flask backend runs on a different port/host, create a `.env` file:

```env
VITE_API_URL=http://localhost:5000
```

## 📊 API Documentation

### POST /predict

Analyze a chest X-ray image for pneumonia.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` - The chest X-ray image (JPEG/PNG)

**Response:**
```json
{
  "label": "PNEUMONIA",
  "probability": 0.94,
  "gradcam": "<base64-encoded-heatmap>",
  "overlay": "<base64-encoded-overlay>"
}
```

### GET /health

Check server status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## 🧠 Model Architecture

- **Base Model**: DenseNet121 (pre-trained on ImageNet)
- **Custom Head**: 
  - Global Average Pooling
  - Dense(256, ReLU) + Dropout(0.5)
  - Dense(128, ReLU) + Dropout(0.3)
  - Dense(1, Sigmoid)
- **Training Strategy**: Two-phase transfer learning
  1. Train with frozen base (50% epochs)
  2. Fine-tune unfrozen top layers (50% epochs)

## 🎨 Frontend Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** components
- **Lucide React** icons
- **React Router** for navigation

## 🔧 Backend Tech Stack

- **Flask** web framework
- **TensorFlow/Keras** for model inference
- **OpenCV** for image processing
- **Flask-CORS** for cross-origin requests

## 📈 Expected Performance

On the test set from the Kaggle dataset:
- **Accuracy**: ~92-95%
- **AUC**: ~0.96-0.98
- **Sensitivity**: ~95-98%
- **Specificity**: ~85-90%

*Note: Actual results may vary based on training conditions and hyperparameters.*

## 🔬 Understanding Grad-CAM

Grad-CAM (Gradient-weighted Class Activation Mapping) helps visualize which regions of the X-ray the model focused on:

- **Red/Warm colors**: High importance for the prediction
- **Blue/Cool colors**: Low importance
- **Overlay**: Combined view of original X-ray and heatmap

This explainability helps medical professionals understand and validate the AI's decision-making process.

## 📝 Citation

If using the Kaggle dataset:
```
@data{chest-xray-pneumonia,
  author = {Paul Mooney},
  title = {Chest X-Ray Images (Pneumonia)},
  year = {2018},
  publisher = {Kaggle},
  url = {https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia}
}
```

## ⚠️ Important Notes

1. **Not for Clinical Use**: This is a research/educational project
2. **Model Accuracy**: While the model achieves high accuracy, it should never replace professional medical diagnosis
3. **Dataset Limitations**: The training data may not represent all populations or conditions
4. **Privacy**: Do not upload real patient data without proper consent and anonymization

## 📄 License

This project is for educational purposes. The dataset has its own license terms on Kaggle.

---

Built with ❤️ for academic research and education.
