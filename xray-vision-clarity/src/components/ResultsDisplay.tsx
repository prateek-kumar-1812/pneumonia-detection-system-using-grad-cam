import { AlertTriangle, CheckCircle, Eye, Layers, TrendingUp, Info, Download } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { generatePneumoniaReport } from "@/lib/pdf-generator";

export interface PredictionResult {
  label: string;
  probability: number;
  gradcam: string;
  overlay: string;
  affectedAreaPercentage?: number;
}

interface ResultsDisplayProps {
  result: PredictionResult;
  originalImage: string;
  onReset: () => void;
}

const ResultsDisplay = ({ result, originalImage, onReset }: ResultsDisplayProps) => {
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const isPneumonia = result.label.toUpperCase() === "PNEUMONIA";
  const confidencePercent = Math.round(result.probability * 100);
  const affectedArea = result.affectedAreaPercentage ?? 0;

  const handleDownloadReport = async () => {
    try {
      setIsGeneratingPDF(true);
      await generatePneumoniaReport({
        confidence: result.probability,
        affectedAreaPercentage: affectedArea,
        predictedClass: result.label.toLowerCase(),
        originalImage,
        gradcamImage: result.gradcam,
        overlayImage: result.overlay,
      });
    } catch (error) {
      console.error('[v0] Error downloading report:', error);
      alert('Failed to generate PDF report. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Prediction Result Card */}
      <div className={cn(
        "rounded-2xl p-6 border-2",
        isPneumonia 
          ? "bg-destructive/5 border-destructive/30" 
          : "bg-success/5 border-success/30"
      )}>
        <div className="flex items-start gap-4">
          <div className={cn(
            "p-3 rounded-xl",
            isPneumonia ? "bg-destructive/20" : "bg-success/20"
          )}>
            {isPneumonia ? (
              <AlertTriangle className="h-8 w-8 text-destructive" />
            ) : (
              <CheckCircle className="h-8 w-8 text-success" />
            )}
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className={cn(
                "font-display font-bold text-2xl",
                isPneumonia ? "text-destructive" : "text-success"
              )}>
                {result.label}
              </h2>
              <span className={cn(
                "px-3 py-1 rounded-full text-sm font-semibold",
                isPneumonia 
                  ? "bg-destructive/20 text-destructive" 
                  : "bg-success/20 text-success"
              )}>
                {isPneumonia ? "Detected" : "Not Detected"}
              </span>
            </div>
            
            <p className="text-muted-foreground mb-4">
              {isPneumonia 
                ? "Signs of pneumonia have been detected in this chest X-ray. Please consult a healthcare professional for proper diagnosis."
                : "No signs of pneumonia detected in this chest X-ray. The lung fields appear normal."
              }
            </p>

            {/* Confidence meter */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <TrendingUp className="h-4 w-4" />
                  Confidence Score
                </span>
                <span className={cn(
                  "text-xl font-bold",
                  isPneumonia ? "text-destructive" : "text-success"
                )}>
                  {confidencePercent}%
                </span>
              </div>
              <div className="h-3 bg-secondary rounded-full overflow-hidden">
                <div 
                  className={cn(
                    "h-full rounded-full transition-all duration-1000",
                    isPneumonia ? "bg-destructive" : "bg-success"
                  )}
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
            </div>

            {/* Affected Area Display */}
            {isPneumonia && affectedArea > 0 && (
              <div className="space-y-2 p-4 rounded-lg bg-destructive/5 border border-destructive/20">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-sm font-medium text-foreground">
                    <TrendingUp className="h-4 w-4" />
                    Affected Lung Area
                  </span>
                  <span className="text-lg font-bold text-destructive">
                    {affectedArea.toFixed(2)}%
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Approximate percentage of lung tissue showing abnormalities
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Image comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ImageCard 
          title="Original X-Ray" 
          subtitle="Input image"
          icon={Eye}
          image={originalImage}
        />
        <ImageCard 
          title="Grad-CAM Heatmap" 
          subtitle="Model attention regions"
          icon={Layers}
          image={result.gradcam}
        />
        <ImageCard 
          title="Overlay Analysis" 
          subtitle="Heatmap + X-Ray"
          icon={Layers}
          image={result.overlay}
          highlighted
        />
      </div>

      {/* Explainability info */}
      <div className="bg-card rounded-xl p-5 border border-border">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-accent/10">
            <Info className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-1">Understanding Grad-CAM</h4>
            <p className="text-sm text-muted-foreground">
              Gradient-weighted Class Activation Mapping (Grad-CAM) highlights the regions of the X-ray that the AI model focused on when making its prediction. 
              <span className="text-accent font-medium"> Red/warm areas</span> indicate high importance, while 
              <span className="text-primary font-medium"> blue/cool areas</span> indicate lower relevance. 
              This helps explain the model's decision-making process.
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4 flex-wrap">
        <Button 
          onClick={handleDownloadReport} 
          disabled={isGeneratingPDF}
          variant="outline" 
          size="lg"
        >
          <Download className="h-4 w-4 mr-2" />
          {isGeneratingPDF ? 'Generating...' : 'Download Report'}
        </Button>
        <Button onClick={onReset} variant="medical" size="lg">
          Analyze Another X-Ray
        </Button>
      </div>

      {/* Disclaimer */}
      <div className="text-center py-4 px-6 bg-warning/10 rounded-xl border border-warning/30">
        <p className="text-sm text-warning font-medium">
          ⚠️ This tool is for research and educational purposes only. It is NOT intended for clinical diagnosis or medical decision-making. 
          Always consult a qualified healthcare professional for medical advice.
        </p>
      </div>
    </div>
  );
};

const ImageCard = ({ 
  title, 
  subtitle, 
  icon: Icon,
  image,
  highlighted = false
}: { 
  title: string; 
  subtitle: string; 
  icon: React.ElementType;
  image: string;
  highlighted?: boolean;
}) => {
  return (
    <div className={cn(
      "bg-card rounded-xl overflow-hidden border transition-all hover:shadow-card-hover",
      highlighted ? "border-accent shadow-glow" : "border-border"
    )}>
      <div className="aspect-square bg-secondary">
        <img 
          src={image} 
          alt={title}
          className="w-full h-full object-contain"
        />
      </div>
      <div className="p-4">
        <div className="flex items-center gap-2 mb-1">
          <Icon className={cn(
            "h-4 w-4",
            highlighted ? "text-accent" : "text-primary"
          )} />
          <h4 className="font-semibold text-foreground">{title}</h4>
        </div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  );
};

export default ResultsDisplay;
