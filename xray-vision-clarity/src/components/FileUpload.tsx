import { useState, useCallback } from "react";
import { Upload, Image, X, FileX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
}

const FileUpload = ({ onFileSelect, isLoading }: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    const validTypes = ["image/jpeg", "image/png", "image/jpg"];
    if (!validTypes.includes(file.type)) {
      setError("Please upload a valid image file (JPEG or PNG)");
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return false;
    }
    setError(null);
    return true;
  };

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearSelection = () => {
    setPreview(null);
    setSelectedFile(null);
    setError(null);
  };

  const handleAnalyze = () => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      {!preview ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={cn(
            "relative border-2 border-dashed rounded-2xl p-12 transition-all duration-300 cursor-pointer",
            "bg-card hover:bg-secondary/50",
            isDragging
              ? "border-accent bg-accent/5 scale-[1.02]"
              : "border-border hover:border-primary/50",
            error && "border-destructive/50 bg-destructive/5"
          )}
        >
          <input
            type="file"
            accept="image/jpeg,image/png,image/jpg"
            onChange={handleInputChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isLoading}
          />
          
          <div className="flex flex-col items-center text-center">
            <div className={cn(
              "p-4 rounded-2xl mb-4 transition-colors",
              isDragging ? "bg-accent/20" : "bg-primary/10"
            )}>
              {error ? (
                <FileX className="h-10 w-10 text-destructive" />
              ) : (
                <Upload className={cn(
                  "h-10 w-10 transition-colors",
                  isDragging ? "text-accent" : "text-primary"
                )} />
              )}
            </div>
            
            <h3 className="font-display font-semibold text-lg text-foreground mb-2">
              {error ? "Invalid File" : "Upload Chest X-Ray"}
            </h3>
            
            <p className="text-sm text-muted-foreground mb-4">
              {error || "Drag and drop your X-ray image here, or click to browse"}
            </p>
            
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Image className="h-4 w-4" />
              <span>Supports JPEG, PNG • Max 10MB</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-card rounded-2xl p-6 shadow-card animate-fade-in">
          <div className="relative group">
            <img
              src={preview}
              alt="X-ray preview"
              className="w-full max-h-80 object-contain rounded-xl bg-secondary"
            />
            <button
              onClick={clearSelection}
              disabled={isLoading}
              className="absolute top-3 right-3 p-2 bg-card/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-destructive hover:text-destructive-foreground transition-colors disabled:opacity-50"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Image className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-sm text-foreground truncate max-w-[200px]">
                  {selectedFile?.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {selectedFile && (selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            
            <Button
              onClick={handleAnalyze}
              disabled={isLoading}
              variant="medical"
              size="lg"
            >
              {isLoading ? "Analyzing..." : "Analyze X-Ray"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
