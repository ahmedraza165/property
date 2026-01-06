"use client";

import { useState } from "react";
import { Header } from "@/components/header";
import { UploadZone } from "@/components/ui/upload-zone";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useUploadCSV } from "@/lib/hooks";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FileText, AlertCircle, CheckCircle2 } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const uploadMutation = useUploadCSV();

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    uploadMutation.mutate(selectedFile, {
      onSuccess: (data) => {
        const savedJobs = localStorage.getItem("parceliq_jobs");
        const jobs = savedJobs ? JSON.parse(savedJobs) : [];
        jobs.unshift({
          job_id: data.job_id,
          filename: selectedFile.name,
          status: data.status,
          total_rows: data.total_rows,
          uploaded_at: new Date().toISOString(),
        });
        localStorage.setItem("parceliq_jobs", JSON.stringify(jobs));

        router.push(`/status/${data.job_id}`);
      },
    });
  };

  return (
    <div className="min-h-screen">
      <Header />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto"
        >
          <div className="text-center mb-12">
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-block mb-4"
            >
              <span className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-gradient-to-r from-blue-500/10 to-green-500/10 border border-blue-500/20">
                <FileText className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-semibold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                  Step 1: Upload Data
                </span>
              </span>
            </motion.div>
            <h1 className="text-5xl font-extrabold mb-4">
              <span className="bg-gradient-to-r from-blue-600 via-green-600 to-red-600 bg-clip-text text-transparent">
                Upload Property CSV
              </span>
            </h1>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Upload your property list and we'll analyze flood zones, wetlands, and more with our AI-powered system
            </p>
          </div>

          <Card className="mb-10" gradient>
            <CardHeader>
              <CardTitle className="text-3xl">📤 Upload File</CardTitle>
              <CardDescription className="text-base">
                Upload a CSV file containing property addresses. Max file size: 10MB
              </CardDescription>
            </CardHeader>
            <CardContent>
              <UploadZone onFileSelect={handleFileSelect} accept=".csv" maxSize={10} />

              {selectedFile && !uploadMutation.isPending && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 flex items-center justify-between p-6 bg-gradient-to-r from-blue-50 to-green-50 border-2 border-blue-200 rounded-2xl shadow-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-blue-500 to-green-500 rounded-xl shadow-lg">
                      <FileText className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <p className="font-bold text-blue-900 text-lg">{selectedFile.name}</p>
                      <p className="text-sm text-blue-700 font-medium mt-1">
                        {(selectedFile.size / 1024).toFixed(2)} KB • Ready to analyze
                      </p>
                    </div>
                  </div>
                  <Button onClick={handleUpload} size="lg" className="shadow-2xl shadow-blue-500/30">
                    <CheckCircle2 className="h-5 w-5 mr-2" />
                    Start Analysis
                  </Button>
                </motion.div>
              )}

              {uploadMutation.isPending && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-10 bg-gradient-to-r from-blue-50 to-green-50 border-2 border-blue-200 rounded-2xl"
                >
                  <LoadingSpinner text="Uploading and validating file..." />
                </motion.div>
              )}

              {uploadMutation.isError && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-6 bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-300 rounded-2xl flex items-start gap-4 shadow-lg shadow-red-500/20"
                >
                  <div className="p-2 bg-red-500 rounded-xl">
                    <AlertCircle className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <p className="font-bold text-red-900 text-lg">Upload failed</p>
                    <p className="text-sm text-red-700 mt-2">
                      {(uploadMutation.error as any)?.message || "An error occurred while uploading the file"}
                    </p>
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>

          <Card gradient>
            <CardHeader>
              <CardTitle className="text-3xl">📋 CSV Format Requirements</CardTitle>
              <CardDescription className="text-base">Your CSV file should include the following columns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: "Street address", required: true },
                  { name: "City", required: true },
                  { name: "State", required: true },
                  { name: "Postal Code", required: true },
                  { name: "Contact Id", required: false },
                  { name: "First Name", required: false },
                  { name: "Last Name", required: false },
                ].map((column) => (
                  <motion.div
                    key={column.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.02 }}
                    className="flex items-center justify-between p-4 bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-slate-100"
                  >
                    <span className="text-base font-bold text-slate-900">{column.name}</span>
                    {column.required ? (
                      <span className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold bg-gradient-to-r from-red-500 to-red-600 text-white rounded-full shadow-lg shadow-red-500/30">
                        <AlertCircle className="h-4 w-4" />
                        Required
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold bg-gradient-to-r from-slate-400 to-slate-500 text-white rounded-full shadow-md">
                        Optional
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-8 p-6 bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-300 rounded-2xl flex items-start gap-4 shadow-lg shadow-green-500/20"
              >
                <div className="p-2 bg-green-500 rounded-xl">
                  <CheckCircle2 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-bold text-green-900 text-lg">Maximum 20,000 properties per upload</p>
                  <p className="text-sm text-green-700 mt-2 font-medium">
                    ⚡ Processing typically takes 1-2 seconds per property
                  </p>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
