# Quick Start Guide: Pneumonia Detection Web Application

**Get the application running in 30 minutes!**

---

## For Testing Only (No Training Required)

If you just want to test the application without training:

### 1. Clone and Install Frontend
```bash
git clone https://github.com/SanjeevSharma012/xray-vision-clarity.git
cd xray-vision-clarity
npm install
```

### 2. Start Frontend
```bash
npm run dev
# Open: http://localhost:5173/x-ray-vision-clarity/
```

**Note:** Backend won't be available in demo mode yet, but UI will work.

---

## For Full Setup with Training (2-4 hours)

### Prerequisites
- Git, Node.js, Python 3.9+
- 8GB+ RAM, 20GB disk space
- NVIDIA GPU recommended (for faster training)

### Step 1: Setup Frontend (5 minutes)
```bash
git clone https://github.com/SanjeevSharma012/xray-vision-clarity.git
cd xray-vision-clarity
npm install
```

### Step 2: Prepare Dataset (10 minutes)
```bash
# Download from: https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
# Extract to: ~/Downloads/chest_xray

# Navigate to training
cd training

# Organize dataset
python prepare_data.py --source ~/Downloads/chest_xray --output ../datasets/
```

### Step 3: Train Model (1-3 hours)
```bash
# Install training dependencies
pip install -r requirements.txt

# Train model
python train.py --data_path ../datasets/chest_xray --epochs 50

# Wait for training to complete...
# Model will be saved to: ../public/backend/model/
```

### Step 4: Start Backend (5 minutes)
```bash
cd public/backend
pip install -r requirements.txt
python app.py
# Server runs at: http://localhost:5000
```

### Step 5: Start Frontend (5 minutes)
```bash
# New terminal, back to project root
npm run dev
# Open: http://localhost:5173/x-ray-vision-clarity/
```

### Step 6: Test Application
1. Upload any chest X-ray image
2. Wait for analysis (3-5 seconds)
3. View results with Grad-CAM visualization
4. Download PDF report

---

## Typical Timeline

| Task | Time | Command |
|------|------|---------|
| Clone & Install | 5 min | `git clone && npm install` |
| Download Dataset | 5 min | Download from Kaggle |
| Prepare Dataset | 5 min | `python prepare_data.py` |
| **Train Model** | **60-180 min** | `python train.py` |
| Setup Backend | 5 min | `pip install && python app.py` |
| Setup Frontend | 5 min | `npm run dev` |
| **Total** | **90-210 min** | ~1.5-3.5 hours |

---

## Common Issues & Quick Fixes

### "ModuleNotFoundError: No module named 'tensorflow'"
```bash
cd public/backend
pip install -r requirements.txt
```

### "Cannot find /datasets/chest_xray"
```bash
# Dataset not prepared yet
cd training
python prepare_data.py --source ~/Downloads/chest_xray --output ../datasets/
```

### "Port 5000 already in use"
```bash
# Kill process using port 5000 or use different port
python app.py --port 5001
```

### "Cannot connect to backend"
```bash
# Backend might not be running
# Ensure backend server is started and accessible
curl http://localhost:5000/health
```

---

## Project Structure

```
xray-vision-clarity/
├── src/                    # React Frontend
├── public/backend/         # Flask Backend
├── training/               # Model Training Code
│   ├── train.py           # Training script
│   ├── prepare_data.py    # Dataset preparation
│   └── requirements.txt
├── datasets/               # (To be created) Dataset storage
├── COMPLETE_SETUP_GUIDE.md # Detailed setup (this file)
├── DATASET_GUIDE.md        # Dataset documentation
├── QUICK_START.md          # Quick start (this file)
└── package.json            # Frontend dependencies
```

---

## What You'll Get

### Frontend Features
- Modern React UI with dark mode
- Real-time image upload with drag-and-drop
- Pneumonia detection with confidence scores
- Grad-CAM visualization (explainable AI)
- Affected lung area percentage
- PDF report download
- Medical disclaimers and guidelines

### Backend Features
- Flask REST API
- DenseNet121 deep learning model
- Real-time predictions (~3-5 seconds)
- Grad-CAM heatmap generation
- Affected area calculation
- CORS enabled for frontend

### Model Features
- Transfer learning (DenseNet121)
- Focal Loss for class imbalance
- ~95% accuracy on test set
- Optimal threshold calibration
- Medical-grade metrics

---

## Next Steps

1. **Read COMPLETE_SETUP_GUIDE.md** for detailed instructions
2. **Read DATASET_GUIDE.md** for dataset information
3. **Complete training** if you want to use real model
4. **Deploy to cloud** (Vercel, Heroku, AWS, etc.)
5. **Publish your work** on GitHub or academic venues

---

## Architecture Overview

```
User Browser
    ↓
React Frontend (http://localhost:5173)
    ↓ (POST with image)
Flask Backend (http://localhost:5000)
    ↓
DenseNet121 Model
    ↓ (Prediction)
Grad-CAM Visualization
    ↓
Return Results to Frontend
    ↓
Display Results + PDF Download
```

---

## API Endpoints

### Health Check
```bash
GET http://localhost:5000/health
```

### Predict Pneumonia
```bash
POST http://localhost:5000/predict
Content-Type: multipart/form-data

# Body: file upload
```

Response:
```json
{
  "label": "PNEUMONIA",
  "probability": 0.92,
  "affected_area_percentage": 25.5,
  "gradcam": "base64_image_data",
  "overlay": "base64_image_data"
}
```

---

## Testing With Curl

```bash
# Test API health
curl http://localhost:5000/health

# Upload image for prediction
curl -F "file=@/path/to/image.jpg" http://localhost:5000/predict
```

---

## System Requirements Summary

| Requirement | Minimum | Recommended |
|-------------|---------|------------|
| RAM | 8 GB | 16 GB |
| Storage | 20 GB | 50 GB |
| GPU | None | NVIDIA (2GB+) |
| Python | 3.9 | 3.11 |
| Node.js | 16 LTS | 18 LTS |

---

## Performance Tips

1. **Faster Training:** Use NVIDIA GPU
2. **Faster Inference:** Use quantized model
3. **Better Results:** More data, longer training
4. **Smoother UI:** Chrome/Edge browsers

---

## Getting Help

1. Check console logs (Frontend: F12, Backend: Terminal)
2. Read COMPLETE_SETUP_GUIDE.md troubleshooting section
3. Verify all prerequisites are installed
4. Check GitHub issues or create new one

---

## Resources

- **Framework:** TensorFlow/Keras, React, Flask
- **Dataset:** Kaggle Chest X-ray Pneumonia
- **Model:** DenseNet121
- **Visualization:** Grad-CAM
- **Explainability:** Focal Loss + Area Calculation

---

## Deployment Ready

After testing locally, deploy to:
- **Frontend:** Vercel, Netlify, GitHub Pages
- **Backend:** Heroku, AWS Lambda, Google Cloud Run
- **Model:** Can be containerized with Docker

---

**Ready to begin? Start with Step 1 above!**

For more details, see: `COMPLETE_SETUP_GUIDE.md`
