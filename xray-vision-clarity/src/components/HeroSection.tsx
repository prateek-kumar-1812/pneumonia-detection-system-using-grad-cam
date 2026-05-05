import { Brain, Shield, Zap, Eye } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="text-center py-12 px-4 animate-fade-in">
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 text-accent text-sm font-medium mb-6">
        <Brain className="h-4 w-4" />
        <span>Powered by DenseNet121 + Grad-CAM</span>
      </div>
      
      <h1 className="font-display font-bold text-4xl md:text-5xl lg:text-6xl text-foreground mb-4 max-w-3xl mx-auto leading-tight">
        Explainable{" "}
        <span className="text-gradient">Pneumonia Detection</span>{" "}
        Using Deep Learning
      </h1>
      
      <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
        Upload a chest X-ray image and get instant AI-powered analysis with visual explanations 
        showing exactly where the model detected potential pneumonia indicators.
      </p>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-3 mb-8">
        <FeaturePill icon={Zap} text="Instant Analysis" />
        <FeaturePill icon={Eye} text="Visual Explanations" />
        <FeaturePill icon={Shield} text="Transfer Learning" />
        <FeaturePill icon={Brain} text="Grad-CAM Heatmaps" />
      </div>
    </section>
  );
};

const FeaturePill = ({ icon: Icon, text }: { icon: React.ElementType; text: string }) => {
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-card rounded-full border border-border shadow-sm">
      <Icon className="h-4 w-4 text-primary" />
      <span className="text-sm font-medium text-foreground">{text}</span>
    </div>
  );
};

export default HeroSection;
