import { Github, FileText } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-border bg-card/50 mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-center md:text-left">
            <p className="text-sm text-muted-foreground">
              Academic Research Project • Built with TensorFlow & React
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Model: DenseNet121 trained on Chest X-Ray Pneumonia Dataset
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <a 
              href="https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <FileText className="h-4 w-4" />
              Dataset
            </a>
            <a 
              href="#"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Github className="h-4 w-4" />
              Source Code
            </a>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs text-center text-muted-foreground">
            ⚠️ <strong>Disclaimer:</strong> This application is for educational and research purposes only. 
            It is not intended for clinical use or medical diagnosis. Always consult qualified healthcare professionals.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
