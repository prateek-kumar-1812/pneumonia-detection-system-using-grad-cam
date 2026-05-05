import { useState } from "react";
import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import FileUpload from "@/components/FileUpload";
import LoadingAnalysis from "@/components/LoadingAnalysis";
import ResultsDisplay, { PredictionResult } from "@/components/ResultsDisplay";
import Footer from "@/components/Footer";
import { predictPneumoniaDemo } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

type AppState = "idle" | "loading" | "results";

const Index = () => {
  const [appState, setAppState] = useState<AppState>("idle");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [originalImage, setOriginalImage] = useState<string>("");
  const { toast } = useToast();

  const handleFileSelect = async (file: File) => {
    setAppState("loading");
    
    // Create preview of original image
    const reader = new FileReader();
    reader.onload = (e) => setOriginalImage(e.target?.result as string);
    reader.readAsDataURL(file);

    try {
      // Using demo mode - replace with predictPneumonia(file) when Flask backend is ready
      const prediction = await predictPneumoniaDemo(file);
      setResult(prediction);
      setAppState("results");
      
      toast({
        title: "Analysis Complete",
        description: `Prediction: ${prediction.label} (${Math.round(prediction.probability * 100)}% confidence)`,
      });
    } catch (error) {
      console.error("Prediction error:", error);
      setAppState("idle");
      toast({
        title: "Analysis Failed",
        description: error instanceof Error ? error.message : "Failed to analyze image. Please ensure the Flask backend is running.",
        variant: "destructive",
      });
    }
  };

  const handleReset = () => {
    setAppState("idle");
    setResult(null);
    setOriginalImage("");
  };

  return (
    <div className="min-h-screen flex flex-col gradient-hero">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        {appState === "idle" && (
          <>
            <HeroSection />
            <FileUpload onFileSelect={handleFileSelect} isLoading={false} />
          </>
        )}

        {appState === "loading" && <LoadingAnalysis />}

        {appState === "results" && result && (
          <ResultsDisplay 
            result={result} 
            originalImage={originalImage}
            onReset={handleReset}
          />
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Index;
