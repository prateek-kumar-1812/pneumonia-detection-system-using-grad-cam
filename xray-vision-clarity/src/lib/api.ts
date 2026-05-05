import { PredictionResult } from "@/components/ResultsDisplay";

// Backend API URL - change this to your Flask server URL
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function predictPneumonia(file: File): Promise<PredictionResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Prediction failed" }));
    throw new Error(error.message || "Failed to analyze image");
  }

  const data = await response.json();
  
  return {
    label: data.label,
    probability: data.probability,
    gradcam: `data:image/png;base64,${data.gradcam}`,
    overlay: `data:image/png;base64,${data.overlay}`,
    affectedAreaPercentage: data.affected_area_percentage || 0,
  };
}

// Demo mode function - simulates API response for testing UI
export async function predictPneumoniaDemo(file: File): Promise<PredictionResult> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 3000));
  
  // Random result for demo
  const isPneumonia = Math.random() > 0.5;
  
  // Create a preview of the uploaded image
  const imageUrl = await new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.readAsDataURL(file);
  });

  return {
    label: isPneumonia ? "PNEUMONIA" : "NORMAL",
    probability: isPneumonia ? 0.87 + Math.random() * 0.1 : 0.92 + Math.random() * 0.05,
    gradcam: imageUrl, // In demo mode, just show the original
    overlay: imageUrl, // In demo mode, just show the original
    affectedAreaPercentage: isPneumonia ? 15 + Math.random() * 35 : 0, // 15-50% for pneumonia, 0% for normal
  };
}
