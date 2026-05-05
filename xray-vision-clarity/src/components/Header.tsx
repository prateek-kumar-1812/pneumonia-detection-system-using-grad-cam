import { Activity, Shield } from "lucide-react";

const Header = () => {
  return (
    <header className="w-full border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/10">
            <Activity className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg text-foreground">
              PneumoVision AI
            </h1>
            <p className="text-xs text-muted-foreground">
              Explainable Pneumonia Detection
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-warning/10 px-3 py-1.5 rounded-full">
          <Shield className="h-3.5 w-3.5 text-warning" />
          <span className="font-medium">Research Use Only</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
