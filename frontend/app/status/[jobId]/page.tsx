"use client";

import { useEffect, use } from "react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { useJobStatus } from "@/lib/hooks";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, MapPin, Droplets, TrendingUp, Car, AlertTriangle, ArrowRight, Copy, Check } from "lucide-react";
import { formatNumber } from "@/lib/utils";

interface ProcessingStepProps {
  icon: React.ElementType;
  label: string;
  isCompleted: boolean;
  isActive: boolean;
  delay: number;
}

function ProcessingStep({ icon: Icon, label, isCompleted, isActive, delay }: ProcessingStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay }}
      className="flex items-center gap-4"
    >
      <div
        className={`
          flex items-center justify-center h-12 w-12 rounded-xl border-2 transition-all duration-300
          ${
            isCompleted
              ? "bg-green-50 border-green-500 text-green-600"
              : isActive
              ? "bg-blue-50 border-blue-500 text-blue-600"
              : "bg-slate-50 border-slate-200 text-slate-400"
          }
        `}
      >
        {isCompleted ? <CheckCircle2 className="h-6 w-6" /> : <Icon className="h-6 w-6" />}
      </div>
      <div className="flex-1">
        <p
          className={`font-medium ${
            isCompleted ? "text-green-900" : isActive ? "text-blue-900" : "text-slate-600"
          }`}
        >
          {label}
        </p>
      </div>
      {isActive && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        </motion.div>
      )}
    </motion.div>
  );
}

export default function StatusPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = use(params);
  const router = useRouter();
  const { data: status, isLoading, error } = useJobStatus(jobId);

  useEffect(() => {
    if (status?.status === "completed") {
      const timer = setTimeout(() => {
        router.push(`/results/${jobId}`);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [status?.status, jobId, router]);

  const progress = status?.progress_percentage || 0;
  const processedRows = status?.processed_rows || 0;
  const totalRows = status?.total_rows || 0;

  const steps = [
    { icon: MapPin, label: "Geocoding addresses", threshold: 0 },
    { icon: Droplets, label: "Analyzing flood zones", threshold: 20 },
    { icon: AlertTriangle, label: "Checking wetlands", threshold: 40 },
    { icon: TrendingUp, label: "Calculating slope", threshold: 60 },
    { icon: Car, label: "Assessing road access", threshold: 80 },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="max-w-2xl mx-auto">
            <Card className="p-12">
              <LoadingSpinner text="Loading status..." />
            </Card>
          </div>
        </main>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="max-w-2xl mx-auto">
            <Card className="p-12 text-center">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-foreground mb-2">Job not found</h2>
              <p className="text-muted-foreground mb-6">
                The job you're looking for doesn't exist or has been removed
              </p>
              <Button onClick={() => router.push("/")}>Go to Dashboard</Button>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-foreground mb-3">
                {status.status === "completed" ? "Analysis Complete!" : "Processing Properties"}
              </h1>
              <p className="text-muted-foreground mb-2">{status.filename}</p>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-600 font-mono">Job ID: {jobId}</p>
                <button
                  onClick={() => navigator.clipboard.writeText(jobId)}
                  className="text-blue-600 hover:text-blue-700 transition-colors"
                  title="Copy Job ID"
                >
                  <Copy className="h-3 w-3" />
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Save this Job ID to access results from any device
              </p>
            </div>

            <Card className="mb-6 p-8">
              {/* Progress Header */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">
                      {status.status === "completed" ? "Analysis Complete!" : "Processing Properties"}
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      {status.status === "processing" && "Analyzing geospatial data and risk factors..."}
                      {status.status === "completed" && "All properties have been analyzed successfully"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-4xl font-bold text-slate-900">{progress.toFixed(0)}%</p>
                    <p className="text-sm text-muted-foreground">Complete</p>
                  </div>
                </div>

                <div className="relative h-4 bg-slate-100 rounded-full overflow-hidden shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 rounded-full shadow-sm"
                  />
                  {status.status === "processing" && (
                    <motion.div
                      animate={{ x: [0, 300, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                    />
                  )}
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="p-5 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
                  <p className="text-sm font-medium text-blue-700 mb-2">Processed</p>
                  <p className="text-3xl font-bold text-blue-900">{formatNumber(processedRows)}</p>
                  <p className="text-xs text-blue-600 mt-1">properties analyzed</p>
                </div>
                <div className="p-5 bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl border border-slate-200">
                  <p className="text-sm font-medium text-slate-700 mb-2">Total</p>
                  <p className="text-3xl font-bold text-slate-900">{formatNumber(totalRows)}</p>
                  <p className="text-xs text-slate-600 mt-1">properties in batch</p>
                </div>
                <div className="p-5 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
                  <p className="text-sm font-medium text-green-700 mb-2">Remaining</p>
                  <p className="text-3xl font-bold text-green-900">{formatNumber(totalRows - processedRows)}</p>
                  <p className="text-xs text-green-600 mt-1">properties left</p>
                </div>
              </div>

              <div className="space-y-4">
                {steps.map((step, index) => (
                  <ProcessingStep
                    key={step.label}
                    icon={step.icon}
                    label={step.label}
                    isCompleted={progress > step.threshold + 20}
                    isActive={progress >= step.threshold && progress <= step.threshold + 20}
                    delay={index * 0.1}
                  />
                ))}
              </div>

              {status.status === "completed" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.4, delay: 0.5 }}
                  className="mt-8 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-6 w-6 text-green-600" />
                    <p className="font-medium text-green-900">Analysis completed successfully!</p>
                  </div>
                  <Button
                    onClick={() => router.push(`/results/${jobId}`)}
                    className="gap-2"
                  >
                    View Results
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </motion.div>
              )}

              {status.status === "failed" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mt-8 p-4 bg-red-50 border border-red-200 rounded-xl"
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-6 w-6 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-900">Processing failed</p>
                      <p className="text-sm text-red-700 mt-1">
                        {status.error_message || "An unknown error occurred"}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </Card>

            {status.status === "processing" && (
              <p className="text-center text-sm text-muted-foreground">
                This may take a few minutes depending on the number of properties...
              </p>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
