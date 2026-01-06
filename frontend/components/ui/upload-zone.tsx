"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number; // in MB
  className?: string;
}

export function UploadZone({ onFileSelect, accept = ".csv", maxSize = 10, className }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback(
    (file: File) => {
      setError(null);

      if (!file.name.endsWith(".csv")) {
        setError("Please upload a CSV file");
        return false;
      }

      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > maxSize) {
        setError(`File size must be less than ${maxSize}MB`);
        return false;
      }

      return true;
    },
    [maxSize]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
          setSelectedFile(file);
          onFileSelect(file);
        }
      }
    },
    [onFileSelect, validateFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
          setSelectedFile(file);
          onFileSelect(file);
        }
      }
    },
    [onFileSelect, validateFile]
  );

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  return (
    <div className={cn("w-full", className)}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200",
          isDragging ? "border-blue-500 bg-blue-50" : "border-slate-200 hover:border-slate-300 bg-white",
          error && "border-red-300 bg-red-50"
        )}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          aria-label="Upload CSV file"
        />

        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="file-selected"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                <FileText className="h-12 w-12 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900">{selectedFile.name}</p>
                <p className="text-sm text-slate-500 mt-1">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
                className="absolute top-4 right-4 p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="no-file"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4"
            >
              <div className={cn(
                "p-4 rounded-xl border",
                error ? "bg-red-50 border-red-200" : "bg-slate-50 border-slate-200"
              )}>
                <Upload className={cn(
                  "h-12 w-12",
                  error ? "text-red-600" : "text-slate-400"
                )} />
              </div>
              <div>
                <p className="text-lg font-medium text-slate-900">
                  {isDragging ? "Drop your CSV file here" : "Upload CSV file"}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Drag and drop or click to browse (Max {maxSize}MB)
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-red-600 mt-4"
          >
            {error}
          </motion.p>
        )}
      </div>
    </div>
  );
}
