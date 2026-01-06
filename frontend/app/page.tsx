"use client";

import { Header } from "@/components/header";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { StatCardSkeleton } from "@/components/ui/skeleton";
import { Building2, AlertTriangle, AlertCircle, CheckCircle2, Upload, ArrowRight } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

interface DashboardStats {
  totalProperties: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
  recentUploads: Array<{
    id: string;
    filename: string;
    date: string;
    status: string;
    total_rows: number;
  }>;
}

export default function HomePage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      const mockStats: DashboardStats = {
        totalProperties: 0,
        highRisk: 0,
        mediumRisk: 0,
        lowRisk: 0,
        recentUploads: [],
      };

      const savedJobs = localStorage.getItem("parceliq_jobs");
      if (savedJobs) {
        try {
          const jobs = JSON.parse(savedJobs);

          // Fetch real-time status for each job
          const recentJobsWithStatus = await Promise.all(
            jobs.slice(0, 5).map(async (job: any) => {
              try {
                const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/status/${job.job_id}`);
                if (statusResponse.ok) {
                  const statusData = await statusResponse.json();

                  // If job is completed, fetch summary to update stats
                  if (statusData.status === 'completed') {
                    try {
                      const summaryResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/results/${job.job_id}/summary`);
                      if (summaryResponse.ok) {
                        const summaryData = await summaryResponse.json();
                        mockStats.totalProperties += summaryData.total_properties || 0;
                        mockStats.highRisk += summaryData.risk_distribution?.high || 0;
                        mockStats.mediumRisk += summaryData.risk_distribution?.medium || 0;
                        mockStats.lowRisk += summaryData.risk_distribution?.low || 0;
                      }
                    } catch (e) {
                      console.error('Error fetching summary:', e);
                    }
                  }

                  return {
                    id: statusData.job_id,
                    filename: statusData.filename,
                    date: statusData.uploaded_at || new Date().toISOString(),
                    status: statusData.status,
                    total_rows: statusData.total_rows || 0,
                  };
                }
              } catch (e) {
                console.error('Error fetching job status:', e);
              }

              // Fallback to stored data
              return {
                id: job.job_id,
                filename: job.filename,
                date: job.uploaded_at || new Date().toISOString(),
                status: job.status || 'unknown',
                total_rows: job.total_rows || 0,
              };
            })
          );

          mockStats.recentUploads = recentJobsWithStatus;
        } catch (e) {
          console.error("Error parsing saved jobs", e);
        }
      }

      setStats(mockStats);
      setLoading(false);
    }

    loadDashboardData();
  }, []);

  return (
    <div className="min-h-screen">
      <Header />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-20"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="inline-block mb-6"
          >
            <span className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-blue-500/10 via-green-500/10 to-red-500/10 border border-blue-500/20 backdrop-blur-sm">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
              <span className="text-sm font-semibold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                AI-Powered Property Intelligence
              </span>
            </span>
          </motion.div>

          <h1 className="text-6xl md:text-7xl font-extrabold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-blue-600 via-green-600 to-red-600 bg-clip-text text-transparent">
              Bulk Land Risk Analysis
            </span>
            <span className="block text-4xl md:text-5xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent mt-3">
              in Seconds, Not Days
            </span>
          </h1>

          <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed">
            Professional property intelligence platform for real estate investors. Analyze flood zones, wetlands, road
            access, and more with <span className="font-bold text-blue-600">AI-powered insights</span>.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link href="/upload">
              <Button size="lg" className="gap-2 text-lg shadow-2xl shadow-blue-500/30">
                <Upload className="h-6 w-6" />
                Start Free Analysis
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="gap-2 text-lg">
              <Building2 className="h-6 w-6" />
              View Sample Report
            </Button>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            {[
              "⚡ Lightning Fast",
              "🎯 99% Accuracy",
              "🔒 Secure & Private",
              "📊 Detailed Reports"
            ].map((feature, i) => (
              <motion.span
                key={feature}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + i * 0.1 }}
                className="px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-slate-200 text-slate-700 font-medium shadow-sm"
              >
                {feature}
              </motion.span>
            ))}
          </div>
        </motion.div>

        {/* Stats Overview */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                Portfolio Overview
              </h2>
              <p className="text-slate-600 mt-2">Real-time analytics across all your properties</p>
            </div>
          </div>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <StatCardSkeleton key={i} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Total Properties"
                value={stats?.totalProperties || 0}
                icon={Building2}
                color="blue"
                delay={0}
              />
              <StatCard
                title="High Risk"
                value={stats?.highRisk || 0}
                icon={AlertTriangle}
                color="red"
                delay={0.1}
              />
              <StatCard
                title="Medium Risk"
                value={stats?.mediumRisk || 0}
                icon={AlertCircle}
                color="yellow"
                delay={0.2}
              />
              <StatCard
                title="Low Risk"
                value={stats?.lowRisk || 0}
                icon={CheckCircle2}
                color="green"
                delay={0.3}
              />
            </div>
          )}
        </div>

        {/* Recent Uploads */}
        <div>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                Recent Uploads
              </h2>
              <p className="text-slate-600 mt-2">Track your analysis history</p>
            </div>
            <Link href="/upload">
              <Button variant="secondary" size="md" className="gap-2">
                <Upload className="h-5 w-5" />
                New Upload
              </Button>
            </Link>
          </div>

          {stats && stats.recentUploads.length > 0 ? (
            <Card gradient hover>
              <div className="divide-y divide-slate-100">
                {stats.recentUploads.map((upload, index) => (
                  <motion.div
                    key={upload.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="p-6 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-green-50/50 transition-all duration-300 cursor-pointer group"
                    onClick={() => router.push(`/results/${upload.id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-5 flex-1">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-green-500 rounded-2xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                          <Building2 className="h-6 w-6 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="font-bold text-slate-900 text-lg">{upload.filename}</p>
                          <p className="text-sm text-slate-600 mt-1">
                            {new Date(upload.date).toLocaleDateString()} • {upload.total_rows} properties
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        {upload.status === "completed" ? (
                          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg shadow-green-500/30">
                            <CheckCircle2 className="h-4 w-4" />
                            COMPLETED
                          </span>
                        ) : upload.status === "processing" ? (
                          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30">
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                              className="h-4 w-4 border-2 border-white border-t-transparent rounded-full"
                            />
                            PROCESSING
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg shadow-red-500/30">
                            <AlertTriangle className="h-4 w-4" />
                            FAILED
                          </span>
                        )}
                        <ArrowRight className="h-6 w-6 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all duration-300" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          ) : (
            <Card className="p-16" gradient>
              <div className="text-center">
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.5 }}
                  className="inline-flex items-center justify-center p-6 bg-gradient-to-br from-blue-500 to-green-500 rounded-3xl mb-6 shadow-2xl shadow-blue-500/20"
                >
                  <Upload className="h-12 w-12 text-white" />
                </motion.div>
                <h3 className="text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
                  No uploads yet
                </h3>
                <p className="text-slate-600 mb-8 text-lg">Get started by uploading your first CSV file</p>
                <Link href="/upload">
                  <Button size="lg" className="gap-2 shadow-2xl shadow-blue-500/30">
                    <Upload className="h-5 w-5" />
                    Upload CSV Now
                    <ArrowRight className="h-5 w-5" />
                  </Button>
                </Link>
              </div>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
