import { Activity, Brain, Scan, Sparkles } from "lucide-react";

const LoadingAnalysis = () => {
  return (
    <div className="w-full max-w-md mx-auto py-12 animate-fade-in">
      <div className="relative flex flex-col items-center">
        {/* Main scanning animation */}
        <div className="relative w-32 h-32 mb-8">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
          
          {/* Spinning ring */}
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary animate-spin" />
          
          {/* Inner pulse */}
          <div className="absolute inset-4 rounded-full bg-primary/10 animate-pulse" />
          
          {/* Center icon */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Brain className="h-12 w-12 text-primary animate-pulse" />
          </div>
          
          {/* Scanning line effect */}
          <div className="absolute inset-0 overflow-hidden rounded-full">
            <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-accent to-transparent animate-scan" />
          </div>
        </div>

        {/* Status text */}
        <h3 className="font-display font-semibold text-xl text-foreground mb-2">
          Analyzing X-Ray
        </h3>
        <p className="text-muted-foreground text-center mb-8">
          Our AI model is processing your chest X-ray image
        </p>

        {/* Progress steps */}
        <div className="space-y-3 w-full max-w-xs">
          <ProgressStep icon={Scan} label="Preprocessing image" delay={0} />
          <ProgressStep icon={Brain} label="Running DenseNet121 model" delay={0.5} />
          <ProgressStep icon={Sparkles} label="Generating Grad-CAM" delay={1} />
          <ProgressStep icon={Activity} label="Preparing results" delay={1.5} />
        </div>
      </div>
    </div>
  );
};

const ProgressStep = ({ 
  icon: Icon, 
  label, 
  delay 
}: { 
  icon: React.ElementType; 
  label: string; 
  delay: number;
}) => {
  return (
    <div 
      className="flex items-center gap-3 p-3 rounded-lg bg-card border border-border animate-fade-in"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="p-2 rounded-lg bg-primary/10">
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <span className="text-sm text-foreground">{label}</span>
      <div className="ml-auto">
        <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
      </div>
    </div>
  );
};

export default LoadingAnalysis;
