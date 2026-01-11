"use client";

import { useState, useMemo, use } from "react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/ui/risk-badge";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { StatCard } from "@/components/ui/stat-card";
import { InsightsPanel } from "@/components/insights-panel";
import { useJobResults, useJobSummary, useTriggerAIAnalysis, useTriggerSkipTrace } from "@/lib/hooks";
import { PropertyResult, api, ExportStatus } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Download,
  Search,
  ChevronDown,
  ChevronUp,
  MapPin,
  Droplets,
  TrendingUp,
  Car,
  Shield,
  FileText,
  Zap,
  Image as ImageIcon,
  Sparkles,
  UserSearch,
  Phone,
  Mail,
  Home,
  X,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";

export default function ResultsPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = use(params);
  const { data: results, isLoading, error, refetch } = useJobResults(jobId);
  const { data: summary } = useJobSummary(jobId);
  const triggerAI = useTriggerAIAnalysis();
  const triggerSkipTrace = useTriggerSkipTrace();

  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<string | null>(null);
  const [countyFilter, setCountyFilter] = useState<string | null>(null);
  const [postalCodeFilter, setPostalCodeFilter] = useState<string | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);
  const [activeTab, setActiveTab] = useState<"table" | "insights">("insights");
  const [aiProcessing, setAiProcessing] = useState(false);
  const [skipTraceProcessing, setSkipTraceProcessing] = useState(false);
  const [skipTraceProgress, setSkipTraceProgress] = useState({ traced: 0, total: 0 });
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);
  const [exportLoading, setExportLoading] = useState(false);

  const handleTriggerAI = async () => {
    try {
      await triggerAI.mutateAsync(jobId);
      setAiProcessing(true);
      // Start polling for updates
      const pollInterval = setInterval(async () => {
        const updated = await refetch();
        // Check if AI analysis is complete
        const hasProcessing = updated.data?.results.some(p =>
          !p.ai_analysis && p.ai_analysis_status !== 'error'
        );
        if (!hasProcessing) {
          clearInterval(pollInterval);
          setAiProcessing(false);
        }
      }, 10000); // Poll every 10 seconds

      // Stop polling after 30 minutes max
      setTimeout(() => {
        clearInterval(pollInterval);
        setAiProcessing(false);
      }, 1800000);
    } catch (error) {
      alert("Failed to start AI analysis. Please try again.");
      setAiProcessing(false);
    }
  };

  const handleTriggerSkipTrace = async () => {
    try {
      const response = await triggerSkipTrace.mutateAsync(jobId);
      const alreadyTraced = response.already_traced || 0;
      const totalProps = response.total_properties || 0;
      const toProcess = totalProps - alreadyTraced;

      if (toProcess === 0) {
        // All already traced, just refresh to show results
        await refetch();
        return;
      }

      // Start loading state
      setSkipTraceProcessing(true);
      setSkipTraceProgress({ traced: alreadyTraced, total: totalProps });

      // Poll for updates every 5 seconds
      const pollInterval = setInterval(async () => {
        const updated = await refetch();

        // Count properties with owner info
        const tracedCount = updated.data?.results.filter(
          (p) => p.owner_info && p.owner_info.status !== "pending"
        ).length || 0;

        setSkipTraceProgress({ traced: tracedCount, total: totalProps });

        // Check if all complete
        if (tracedCount >= totalProps) {
          clearInterval(pollInterval);
          setSkipTraceProcessing(false);
        }
      }, 5000);

      // Stop polling after 10 minutes max
      setTimeout(() => {
        clearInterval(pollInterval);
        setSkipTraceProcessing(false);
      }, 600000);
    } catch (error) {
      alert("Failed to start skip tracing. Please try again.");
      setSkipTraceProcessing(false);
    }
  };

  // Get unique counties and postal codes for filters
  const uniqueCounties = useMemo(() => {
    if (!results?.results) return [];
    const counties = results.results
      .map(p => p.address.county)
      .filter((c): c is string => c !== null && c !== undefined);
    return [...new Set(counties)].sort();
  }, [results]);

  const uniquePostalCodes = useMemo(() => {
    if (!results?.results) return [];
    const codes = results.results
      .map(p => p.address.zip)
      .filter((c): c is string => c !== null && c !== undefined);
    return [...new Set(codes)].sort();
  }, [results]);

  const filteredAndSortedResults = useMemo(() => {
    if (!results?.results) return [];

    let filtered = results.results.filter((property) => {
      const matchesSearch =
        property.address.full_address.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRiskFilter = !riskFilter || property.phase1_risk?.overall_risk === riskFilter;
      const matchesCountyFilter = !countyFilter || property.address.county === countyFilter;
      const matchesPostalCodeFilter = !postalCodeFilter || property.address.zip === postalCodeFilter;

      return matchesSearch && matchesRiskFilter && matchesCountyFilter && matchesPostalCodeFilter;
    });

    if (sortConfig) {
      filtered.sort((a, b) => {
        let aValue: any;
        let bValue: any;

        if (sortConfig.key === "address") {
          aValue = a.address.full_address;
          bValue = b.address.full_address;
        } else if (sortConfig.key === "risk") {
          const riskOrder = { HIGH: 3, MEDIUM: 2, LOW: 1, "": 0 };
          aValue = riskOrder[a.phase1_risk?.overall_risk as keyof typeof riskOrder] || 0;
          bValue = riskOrder[b.phase1_risk?.overall_risk as keyof typeof riskOrder] || 0;
        }

        if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [results, searchQuery, riskFilter, countyFilter, postalCodeFilter, sortConfig]);

  // Calculate risk distribution from filtered results (for accurate stat cards)
  const filteredRiskDistribution = useMemo(() => {
    if (!results?.results) return { high: 0, medium: 0, low: 0, total: 0 };

    // Apply all filters EXCEPT risk filter to get accurate counts for stat cards
    const baseFiltered = results.results.filter((property) => {
      const matchesSearch =
        property.address.full_address.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCountyFilter = !countyFilter || property.address.county === countyFilter;
      const matchesPostalCodeFilter = !postalCodeFilter || property.address.zip === postalCodeFilter;
      return matchesSearch && matchesCountyFilter && matchesPostalCodeFilter;
    });

    return {
      high: baseFiltered.filter(p => p.phase1_risk?.overall_risk === "HIGH").length,
      medium: baseFiltered.filter(p => p.phase1_risk?.overall_risk === "MEDIUM").length,
      low: baseFiltered.filter(p => p.phase1_risk?.overall_risk === "LOW").length,
      total: baseFiltered.length
    };
  }, [results, searchQuery, countyFilter, postalCodeFilter]);

  const handleSort = (key: string) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  };

  const handleExportClick = async () => {
    // Fetch export status to check what data is available
    setExportLoading(true);
    try {
      const status = await api.getExportStatus(jobId);
      setExportStatus(status);

      // If both AI and owner info are complete, export directly
      if (status.ai_analysis.complete && status.owner_info.complete) {
        performExport();
      } else {
        // Show warning dialog
        setShowExportDialog(true);
      }
    } catch (error) {
      console.error("Failed to get export status:", error);
      // If we can't get status, just export anyway
      performExport();
    } finally {
      setExportLoading(false);
    }
  };

  const performExport = () => {
    // Use the backend export endpoint which includes all original CSV columns
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    window.location.href = `${API_BASE_URL}/results/${jobId}/export`;
    setShowExportDialog(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Card className="p-16" gradient>
            <LoadingSpinner text="Loading results..." />
          </Card>
        </main>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Card className="p-16 text-center" gradient>
            <div className="p-4 bg-gradient-to-br from-red-500 to-red-600 rounded-3xl inline-block mb-6 shadow-2xl shadow-red-500/30">
              <AlertTriangle className="h-16 w-16 text-white" />
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
              Failed to load results
            </h2>
            <p className="text-slate-600 text-lg">Please try again later</p>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 gap-4">
            <div>
              <h1 className="text-5xl font-extrabold mb-3">
                <span className="bg-gradient-to-r from-blue-600 via-green-600 to-red-600 bg-clip-text text-transparent">
                  Analysis Results
                </span>
              </h1>
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-blue-600" />
                <p className="text-lg text-slate-600 font-medium">{results.filename}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleTriggerAI}
                variant="secondary"
                size="lg"
                className="gap-2 shadow-2xl shadow-purple-500/30"
                disabled={triggerAI.isPending}
              >
                <Sparkles className="h-5 w-5" />
                {triggerAI.isPending ? "Starting AI..." : "Run AI Analysis"}
              </Button>
              <Button
                onClick={handleTriggerSkipTrace}
                variant="secondary"
                size="lg"
                className="gap-2 shadow-2xl shadow-blue-500/30"
                disabled={triggerSkipTrace.isPending || skipTraceProcessing}
              >
                {skipTraceProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
                    Finding Owners...
                  </>
                ) : (
                  <>
                    <UserSearch className="h-5 w-5" />
                    {triggerSkipTrace.isPending ? "Starting..." : "Find Owners"}
                  </>
                )}
              </Button>
              <Button
                onClick={handleExportClick}
                variant="secondary"
                size="lg"
                className="gap-2 shadow-2xl shadow-green-500/30"
                disabled={exportLoading}
              >
                {exportLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-green-600 border-t-transparent" />
                    Checking...
                  </>
                ) : (
                  <>
                    <Download className="h-5 w-5" />
                    Export CSV
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* AI Processing Progress Banner */}
          {aiProcessing && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <Card className="p-6 bg-gradient-to-r from-purple-50 via-pink-50 to-purple-50 border-2 border-purple-300" gradient>
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-200 border-t-purple-600"></div>
                    <Sparkles className="h-6 w-6 text-purple-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-purple-900 mb-1">
                      🤖 AI Analysis In Progress
                    </h3>
                    <p className="text-sm text-purple-700">
                      Analyzing satellite and street view imagery for all properties... This page will auto-update as results become available.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="flex-1 bg-purple-200 rounded-full h-2">
                        <div className="bg-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
                      </div>
                      <span className="text-xs font-semibold text-purple-600">Processing...</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="bg-purple-600 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg">
                      AUTO-REFRESHING
                    </div>
                    <p className="text-xs text-purple-600 mt-2">Every 10 seconds</p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Skip Trace Processing Progress Banner */}
          {skipTraceProcessing && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              <Card className="p-6 bg-gradient-to-r from-blue-50 via-indigo-50 to-blue-50 border-2 border-blue-300" gradient>
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
                    <UserSearch className="h-6 w-6 text-blue-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-blue-900 mb-1">
                      🔍 Finding Property Owners...
                    </h3>
                    <p className="text-sm text-blue-700">
                      Searching public records for owner contact information including phone numbers, emails, and mailing addresses.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="flex-1 bg-blue-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{
                            width: skipTraceProgress.total > 0
                              ? `${Math.round((skipTraceProgress.traced / skipTraceProgress.total) * 100)}%`
                              : '10%'
                          }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-blue-600">
                        {skipTraceProgress.traced} / {skipTraceProgress.total} properties
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg">
                      {Math.round((skipTraceProgress.traced / Math.max(skipTraceProgress.total, 1)) * 100)}% COMPLETE
                    </div>
                    <p className="text-xs text-blue-600 mt-2">Auto-refreshing every 5s</p>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}

          {results?.results && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                title="Total Properties"
                value={filteredRiskDistribution.total}
                icon={Building2}
                color="gray"
                delay={0}
              />
              <StatCard
                title="High Risk"
                value={filteredRiskDistribution.high}
                icon={AlertTriangle}
                color="red"
                delay={0.1}
              />
              <StatCard
                title="Medium Risk"
                value={filteredRiskDistribution.medium}
                icon={AlertCircle}
                color="yellow"
                delay={0.2}
              />
              <StatCard
                title="Low Risk"
                value={filteredRiskDistribution.low}
                icon={CheckCircle2}
                color="green"
                delay={0.3}
              />
            </div>
          )}

          {/* Tab Switcher */}
          <div className="flex gap-3 mb-8">
            <button
              onClick={() => setActiveTab("insights")}
              className={`relative px-8 py-4 rounded-2xl text-base font-bold transition-all duration-300 overflow-hidden ${
                activeTab === "insights"
                  ? "text-white shadow-2xl shadow-blue-500/30"
                  : "text-slate-700 hover:bg-white/50 border-2 border-slate-200"
              }`}
            >
              {activeTab === "insights" && (
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-green-500"></div>
              )}
              <span className="relative z-10">📊 Insights & Analytics</span>
            </button>
            <button
              onClick={() => setActiveTab("table")}
              className={`relative px-8 py-4 rounded-2xl text-base font-bold transition-all duration-300 overflow-hidden ${
                activeTab === "table"
                  ? "text-white shadow-2xl shadow-green-500/30"
                  : "text-slate-700 hover:bg-white/50 border-2 border-slate-200"
              }`}
            >
              {activeTab === "table" && (
                <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-blue-500"></div>
              )}
              <span className="relative z-10">📋 Property Table</span>
            </button>
          </div>

          {/* Insights View */}
          {activeTab === "insights" && summary && (
            <InsightsPanel summary={summary} />
          )}

          {/* Table View */}
          {activeTab === "table" && (
            <>
              <Card className="mb-8 p-8" gradient>
            <div className="flex flex-col gap-5">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-6 w-6 text-blue-500" />
                  <input
                    type="text"
                    placeholder="Search by address or name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-14 pr-4 py-4 border-2 border-blue-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base font-medium shadow-lg"
                  />
                </div>
                <div className="flex gap-3">
                  {[
                    { risk: "LOW", color: "from-green-500 to-green-600" },
                    { risk: "MEDIUM", color: "from-yellow-500 to-yellow-600" },
                    { risk: "HIGH", color: "from-red-500 to-red-600" }
                  ].map(({ risk, color }) => (
                    <button
                      key={risk}
                      onClick={() => setRiskFilter(riskFilter === risk ? null : risk)}
                      className={`px-6 py-3 rounded-2xl text-sm font-bold transition-all duration-300 ${
                        riskFilter === risk
                          ? `bg-gradient-to-r ${color} text-white shadow-2xl`
                          : "bg-white text-slate-700 hover:bg-slate-50 border-2 border-slate-200"
                      }`}
                    >
                      {risk}
                    </button>
                  ))}
                  {riskFilter && (
                    <button
                      onClick={() => setRiskFilter(null)}
                      className="px-6 py-3 rounded-2xl text-sm font-bold bg-white text-slate-700 hover:bg-slate-50 border-2 border-slate-200 transition-all"
                    >
                      ✕ Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Additional Filters */}
              <div className="flex flex-col md:flex-row gap-3">
                <div className="flex-1">
                  <select
                    value={countyFilter || ""}
                    onChange={(e) => setCountyFilter(e.target.value || null)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">All Counties</option>
                    {uniqueCounties.map((county) => (
                      <option key={county} value={county}>
                        {county}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex-1">
                  <select
                    value={postalCodeFilter || ""}
                    onChange={(e) => setPostalCodeFilter(e.target.value || null)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">All Postal Codes</option>
                    {uniquePostalCodes.map((code) => (
                      <option key={code} value={code}>
                        {code}
                      </option>
                    ))}
                  </select>
                </div>
                {(countyFilter || postalCodeFilter) && (
                  <button
                    onClick={() => {
                      setCountyFilter(null);
                      setPostalCodeFilter(null);
                    }}
                    className="px-4 py-2 rounded-xl text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200"
                  >
                    Clear Filters
                  </button>
                )}
              </div>
            </div>
          </Card>

          <Card gradient>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-slate-50 to-slate-100 border-b-2 border-blue-200">
                  <tr>
                    <th className="px-6 py-5 text-left text-sm font-bold text-slate-700 uppercase tracking-wide">
                      <button
                        onClick={() => handleSort("address")}
                        className="flex items-center gap-2 hover:text-blue-600 transition-colors"
                      >
                        📍 Address
                        {sortConfig?.key === "address" &&
                          (sortConfig.direction === "asc" ? (
                            <ChevronUp className="h-5 w-5" />
                          ) : (
                            <ChevronDown className="h-5 w-5" />
                          ))}
                      </button>
                    </th>
                    <th className="px-6 py-5 text-left text-sm font-bold text-slate-700 uppercase tracking-wide">
                      <button
                        onClick={() => handleSort("risk")}
                        className="flex items-center gap-2 hover:text-blue-600 transition-colors"
                      >
                        ⚠️ Risk
                        {sortConfig?.key === "risk" &&
                          (sortConfig.direction === "asc" ? (
                            <ChevronUp className="h-5 w-5" />
                          ) : (
                            <ChevronDown className="h-5 w-5" />
                          ))}
                      </button>
                    </th>
                    <th className="px-6 py-5 text-left text-sm font-bold text-slate-700 uppercase tracking-wide">
                      🏷️ Highlights
                    </th>
                    <th className="px-6 py-5 text-left text-sm font-bold text-slate-700 uppercase tracking-wide">
                      🤖 AI
                    </th>
                    <th className="px-6 py-5"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredAndSortedResults.map((property, index) => (
                    <PropertyRow
                      key={index}
                      property={property}
                      index={index}
                      isExpanded={expandedRow === index}
                      onToggle={() => setExpandedRow(expandedRow === index ? null : index)}
                    />
                  ))}
                </tbody>
              </table>

              {filteredAndSortedResults.length === 0 && (
                <div className="p-16 text-center">
                  <div className="inline-block p-4 bg-gradient-to-br from-slate-200 to-slate-300 rounded-3xl mb-4">
                    <Search className="h-12 w-12 text-slate-500" />
                  </div>
                  <p className="text-slate-600 text-lg font-medium">No properties match your filters</p>
                </div>
              )}
            </div>
          </Card>

          <p className="text-sm text-muted-foreground mt-4 text-center">
            Showing {formatNumber(filteredAndSortedResults.length)} of {formatNumber(results.total_properties)}{" "}
            properties
          </p>

          {/* Legal Disclaimer */}
          <Card className="mt-10 p-8" gradient>
            <div className="flex items-start gap-5">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-slate-600 rounded-2xl flex-shrink-0 shadow-xl">
                <Shield className="h-7 w-7 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 mb-3 text-xl">⚖️ Legal Disclaimer</h3>
                <p className="text-base text-slate-700 leading-relaxed">
                  This report is for informational purposes only and should not be construed as legal advice.
                  Property buyers should conduct their own due diligence and consult with qualified professionals
                  (including real estate attorneys, surveyors, environmental consultants, and title companies)
                  before making any purchasing decisions. The data provided herein is sourced from publicly
                  available datasets and may not be complete, accurate, or current. We make no warranties or
                  representations regarding the accuracy, completeness, or timeliness of this information.
                </p>
              </div>
            </div>
          </Card>
            </>
          )}
        </motion.div>
      </main>

      {/* Export Warning Dialog */}
      <AnimatePresence>
        {showExportDialog && exportStatus && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowExportDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-xl">
                    <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">Export Warning</h3>
                </div>
                <button
                  onClick={() => setShowExportDialog(false)}
                  className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  <X className="h-5 w-5 text-slate-500" />
                </button>
              </div>

              <div className="space-y-4 mb-6">
                <p className="text-slate-600">
                  Some data may be missing from your export:
                </p>

                <div className="space-y-3">
                  {/* AI Analysis Warning */}
                  {!exportStatus.ai_analysis.complete && (
                    <div className={`p-4 rounded-xl border-2 ${
                      exportStatus.ai_analysis.available
                        ? "bg-yellow-50 border-yellow-200"
                        : "bg-red-50 border-red-200"
                    }`}>
                      <div className="flex items-center gap-3">
                        <Sparkles className={`h-5 w-5 ${
                          exportStatus.ai_analysis.available ? "text-yellow-600" : "text-red-600"
                        }`} />
                        <div className="flex-1">
                          <p className={`font-semibold ${
                            exportStatus.ai_analysis.available ? "text-yellow-900" : "text-red-900"
                          }`}>
                            AI Analysis
                          </p>
                          <p className={`text-sm ${
                            exportStatus.ai_analysis.available ? "text-yellow-700" : "text-red-700"
                          }`}>
                            {exportStatus.ai_analysis.available
                              ? `${exportStatus.ai_analysis.count} of ${exportStatus.total_properties} properties analyzed`
                              : "No AI analysis has been run yet"
                            }
                          </p>
                        </div>
                        {!exportStatus.ai_analysis.available && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              setShowExportDialog(false);
                              handleTriggerAI();
                            }}
                            className="text-xs"
                          >
                            Run AI Analysis
                          </Button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Owner Info Warning */}
                  {!exportStatus.owner_info.complete && (
                    <div className={`p-4 rounded-xl border-2 ${
                      exportStatus.owner_info.available
                        ? "bg-yellow-50 border-yellow-200"
                        : "bg-red-50 border-red-200"
                    }`}>
                      <div className="flex items-center gap-3">
                        <UserSearch className={`h-5 w-5 ${
                          exportStatus.owner_info.available ? "text-yellow-600" : "text-red-600"
                        }`} />
                        <div className="flex-1">
                          <p className={`font-semibold ${
                            exportStatus.owner_info.available ? "text-yellow-900" : "text-red-900"
                          }`}>
                            Owner Information
                          </p>
                          <p className={`text-sm ${
                            exportStatus.owner_info.available ? "text-yellow-700" : "text-red-700"
                          }`}>
                            {exportStatus.owner_info.available
                              ? `${exportStatus.owner_info.count} of ${exportStatus.total_properties} owners found`
                              : "No owner search has been run yet"
                            }
                          </p>
                        </div>
                        {!exportStatus.owner_info.available && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              setShowExportDialog(false);
                              handleTriggerSkipTrace();
                            }}
                            className="text-xs"
                          >
                            Find Owners
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Original Columns Info */}
                {exportStatus.original_columns.length > 0 && (
                  <div className="p-4 bg-green-50 border-2 border-green-200 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <p className="font-semibold text-green-900">Original CSV Columns Preserved</p>
                    </div>
                    <p className="text-sm text-green-700">
                      All {exportStatus.original_columns.length} columns from your uploaded CSV will be included in the export.
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-3 justify-end">
                <Button
                  variant="secondary"
                  onClick={() => setShowExportDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={performExport}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export Anyway
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function PropertyRow({
  property,
  index,
  isExpanded,
  onToggle,
}: {
  property: PropertyResult;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const risk = property.phase1_risk;

  const highlights = [];
  if (risk?.wetlands.status) highlights.push("Wetlands");
  if (risk?.flood_zone.severity === "HIGH") highlights.push("High Flood");
  if (risk?.landlocked) highlights.push("Landlocked");
  if (risk?.protected_land.is_protected) highlights.push("Protected");

  return (
    <>
      <motion.tr
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className="hover:bg-gradient-to-r hover:from-blue-50/30 hover:to-green-50/30 transition-all duration-300 cursor-pointer group"
        onClick={onToggle}
      >
        <td className="px-6 py-5">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-green-500 rounded-xl mt-1 group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <MapPin className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-slate-900 text-base">{property.address.street}</p>
              <p className="text-sm text-slate-600 mt-1 font-medium">
                {property.address.city}, {property.address.state} {property.address.zip}
              </p>
            </div>
          </div>
        </td>
        <td className="px-6 py-5">
          {risk?.overall_risk ? (
            <RiskBadge risk={risk.overall_risk} />
          ) : (
            <span className="text-sm text-slate-500 font-medium">N/A</span>
          )}
        </td>
        <td className="px-6 py-5">
          <div className="flex flex-wrap gap-2">
            {highlights.slice(0, 3).map((highlight) => (
              <span
                key={highlight}
                className="px-3 py-1.5 bg-gradient-to-r from-slate-100 to-slate-200 text-slate-700 text-xs font-bold rounded-lg shadow-sm"
              >
                {highlight}
              </span>
            ))}
            {highlights.length > 3 && (
              <span className="px-3 py-1.5 bg-gradient-to-r from-blue-100 to-green-100 text-blue-700 text-xs font-bold rounded-lg shadow-sm">
                +{highlights.length - 3} more
              </span>
            )}
          </div>
        </td>
        <td className="px-6 py-5">
          {property.ai_analysis ? (
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-1.5 rounded-lg shadow-lg">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-purple-600">Analyzed</span>
                {property.ai_analysis.overall_risk?.level && (
                  <span className="text-xs text-purple-500">
                    {property.ai_analysis.overall_risk.level}
                  </span>
                )}
              </div>
            </div>
          ) : property.ai_analysis_status === 'processing' ? (
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
              <span className="text-xs font-medium text-purple-600">Processing...</span>
            </div>
          ) : property.ai_analysis_status === 'pending' ? (
            <div className="flex items-center gap-2">
              <div className="bg-gray-300 p-1.5 rounded-lg">
                <Sparkles className="h-4 w-4 text-gray-500" />
              </div>
              <span className="text-xs font-medium text-gray-500">Pending</span>
            </div>
          ) : (
            <span className="text-xs text-gray-400">—</span>
          )}
        </td>
        <td className="px-6 py-5 text-right">
          <button className="p-2 rounded-xl bg-white border-2 border-slate-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm group-hover:scale-110">
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </button>
        </td>
      </motion.tr>
      {isExpanded && risk && (
        <tr>
          <td colSpan={5} className="px-6 py-4 bg-slate-50">
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              {/* Risk Factors Section */}
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3">Risk Factors</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
                    <Droplets className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Flood Zone</p>
                      <p className="font-medium text-foreground">{risk.flood_zone.zone || "N/A"}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Severity: {risk.flood_zone.severity || "N/A"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
                    <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Slope</p>
                      <p className="font-medium text-foreground">
                        {risk.slope.percentage ? `${risk.slope.percentage}%` : "N/A"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Severity: {risk.slope.severity || "N/A"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
                    <Car className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Road Access</p>
                      <p className="font-medium text-foreground">{risk.road_access.has_access ? "Yes" : "No"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
                    <Shield className="h-5 w-5 text-orange-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Protected Land</p>
                      <p className="font-medium text-foreground">
                        {risk.protected_land.is_protected ? "Yes" : "No"}
                      </p>
                      {risk.protected_land.type && (
                        <p className="text-xs text-muted-foreground mt-1">{risk.protected_land.type}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Analysis Section - PREMIUM */}
              {property.ai_analysis && (
                <div className="mt-6">
                  <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-purple-50 rounded-xl p-6 border-2 border-purple-200 shadow-lg">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-2 rounded-lg">
                        <Sparkles className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <h4 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                          AI-Powered Premium Insights
                        </h4>
                        <p className="text-xs text-purple-600">Advanced Computer Vision Analysis</p>
                      </div>
                      <div className="ml-auto">
                        <span className="px-3 py-1 bg-purple-600 text-white text-xs font-bold rounded-full">
                          PRO
                        </span>
                      </div>
                    </div>

                    {/* Property Images - Satellite & Street View */}
                    {(property.ai_analysis.imagery?.satellite?.url || property.ai_analysis.imagery?.street_view_1?.url || property.ai_analysis.imagery?.street?.url) && (
                      <div className="mb-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Satellite View */}
                          {property.ai_analysis.imagery?.satellite?.url && (
                            <div className="relative group overflow-hidden rounded-xl shadow-xl hover:shadow-2xl transition-shadow duration-300">
                              <img
                                src={property.ai_analysis.imagery.satellite.url}
                                alt="Satellite view analysis"
                                className="w-full h-64 object-cover transform group-hover:scale-105 transition-transform duration-500"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                              <div className="absolute top-3 right-3">
                                <div className="bg-blue-500/90 backdrop-blur-sm text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg">
                                  ✓ AI Analyzed
                                </div>
                              </div>
                              <div className="absolute bottom-3 left-3 right-3">
                                <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm text-blue-900 text-xs font-semibold px-3 py-2 rounded-lg shadow-lg">
                                  <ImageIcon className="h-4 w-4" />
                                  <span>Satellite View - {property.ai_analysis.imagery.satellite.source}</span>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Street View - Check street_view_1 first, then fall back to legacy street field */}
                          {(property.ai_analysis.imagery?.street_view_1?.url || property.ai_analysis.imagery?.street?.url) && (
                            <div className="relative group overflow-hidden rounded-xl shadow-xl hover:shadow-2xl transition-shadow duration-300">
                              <img
                                src={property.ai_analysis.imagery?.street_view_1?.url || property.ai_analysis.imagery?.street?.url || ''}
                                alt="Street view analysis"
                                className="w-full h-64 object-cover transform group-hover:scale-105 transition-transform duration-500"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                              <div className="absolute top-3 right-3">
                                <div className="bg-green-500/90 backdrop-blur-sm text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg">
                                  ✓ AI Analyzed
                                </div>
                              </div>
                              <div className="absolute bottom-3 left-3 right-3">
                                <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm text-purple-900 text-xs font-semibold px-3 py-2 rounded-lg shadow-lg">
                                  <ImageIcon className="h-4 w-4" />
                                  <span>Street View - {property.ai_analysis.imagery?.street_view_1?.source || property.ai_analysis.imagery?.street?.source}</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                  {/* AI Detections Grid - Premium Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Road Condition */}
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-5 rounded-xl border-2 border-blue-200 shadow-md hover:shadow-lg transition-shadow">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="bg-blue-600 p-2 rounded-lg">
                          <Car className="h-5 w-5 text-white" />
                        </div>
                        <p className="text-sm font-bold text-blue-900">Road Condition</p>
                      </div>
                      <p className="text-2xl font-extrabold text-blue-700 mb-2">{property.ai_analysis.road_condition?.type || "Unknown"}</p>
                      {property.ai_analysis.road_condition?.confidence !== null && (
                        <div className="flex items-center gap-2 mb-3">
                          <div className="flex-1 bg-blue-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${Math.round(property.ai_analysis.road_condition.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-blue-700">
                            {Math.round(property.ai_analysis.road_condition.confidence * 100)}%
                          </span>
                        </div>
                      )}
                      <p className="text-xs text-blue-600 leading-relaxed">
                        {property.ai_analysis.road_condition?.type === "PAVED" && "Well-maintained paved road provides excellent access and property value."}
                        {property.ai_analysis.road_condition?.type === "GRAVEL" && "Gravel road may require maintenance but provides adequate access."}
                        {property.ai_analysis.road_condition?.type === "DIRT" && "Unpaved dirt road may affect accessibility, especially in wet weather."}
                        {property.ai_analysis.road_condition?.type === "POOR" && "Road condition needs improvement; may increase development costs."}
                        {(!property.ai_analysis.road_condition?.type || property.ai_analysis.road_condition?.type === "UNKNOWN") && "Road condition could not be determined from available imagery."}
                      </p>
                    </div>

                    {/* Power Lines */}
                    <div className="bg-gradient-to-br from-yellow-50 to-orange-100 p-5 rounded-xl border-2 border-yellow-200 shadow-md hover:shadow-lg transition-shadow">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="bg-yellow-600 p-2 rounded-lg">
                          <Zap className="h-5 w-5 text-white" />
                        </div>
                        <p className="text-sm font-bold text-yellow-900">Power Lines</p>
                      </div>
                      <p className="text-2xl font-extrabold text-yellow-700 mb-2">
                        {property.ai_analysis.power_lines?.visible ? "✓ Detected" : "✗ None"}
                      </p>
                      {property.ai_analysis.power_lines?.distance_meters !== null && property.ai_analysis.power_lines?.visible && (
                        <p className="text-sm font-semibold text-yellow-700 mb-2">
                          ~{Math.round(property.ai_analysis.power_lines.distance_meters)}m away
                        </p>
                      )}
                      <p className="text-xs text-yellow-700 leading-relaxed">
                        {property.ai_analysis.power_lines?.visible || property.ai_analysis.power_lines_street?.visible
                          ? "✅ Electrical infrastructure detected - Good utility access available. Easy connection for development."
                          : "⚠️ No electrical infrastructure visible - May require expensive utility installation."}
                      </p>
                    </div>

                    {/* Nearby Development */}
                    <div className="bg-gradient-to-br from-green-50 to-emerald-100 p-5 rounded-xl border-2 border-green-200 shadow-md hover:shadow-lg transition-shadow">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="bg-green-600 p-2 rounded-lg">
                          <Building2 className="h-5 w-5 text-white" />
                        </div>
                        <p className="text-sm font-bold text-green-900">Development</p>
                      </div>
                      <p className="text-2xl font-extrabold text-green-700 mb-2">
                        {property.ai_analysis.nearby_development?.type || "Unknown"}
                      </p>
                      {property.ai_analysis.nearby_structures?.count !== null && property.ai_analysis.nearby_structures?.count !== undefined && (
                        <p className="text-sm font-semibold text-green-700 mb-1">
                          {property.ai_analysis.nearby_structures.count} structures detected
                        </p>
                      )}
                      {property.ai_analysis.nearby_structures?.types && property.ai_analysis.nearby_structures.types.length > 0 && (
                        <p className="text-xs text-green-600 mt-2">
                          Types: {property.ai_analysis.nearby_structures.types.join(", ")}
                        </p>
                      )}
                      {property.ai_analysis.nearby_structures?.density && (
                        <p className="text-xs text-green-600">
                          Density: {property.ai_analysis.nearby_structures.density}
                        </p>
                      )}
                      {property.ai_analysis.nearby_structures?.details && (
                        <p className="text-xs text-green-700 mt-2 italic">
                          {property.ai_analysis.nearby_structures.details}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* AI Risk Badge */}
                  {property.ai_analysis.overall_risk?.level && (
                    <div className="mt-4 flex items-center gap-2 justify-end">
                      <span className="text-xs text-purple-600 font-semibold">AI Risk Assessment:</span>
                      <RiskBadge risk={property.ai_analysis.overall_risk.level.toLowerCase()} />
                      {property.ai_analysis.overall_risk.confidence !== null && (
                        <span className="text-xs text-purple-600">
                          ({Math.round(property.ai_analysis.overall_risk.confidence * 100)}% confidence)
                        </span>
                      )}
                    </div>
                  )}

                  {/* Overall AI Summary - Comprehensive Review */}
                  <div className="mt-6 bg-gradient-to-br from-purple-50 via-pink-50 to-purple-50 rounded-xl p-6 border-2 border-purple-200 shadow-lg">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-3 rounded-lg shadow-lg">
                        <Sparkles className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h4 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                          AI Comprehensive Analysis
                        </h4>
                        <p className="text-xs text-purple-600">Combined insights from satellite and street view imagery</p>
                      </div>
                    </div>

                    <div className="space-y-3 text-sm text-purple-900 leading-relaxed">
                      {/* Power Lines Summary */}
                      <p>
                        <span className="font-bold text-purple-700">⚡ Power Infrastructure:</span>{" "}
                        {property.ai_analysis.power_lines?.visible || property.ai_analysis.power_lines_street?.visible ? (
                          <>
                            ✅ <strong>Excellent electrical infrastructure access.</strong> Utility poles and power lines detected in the area.
                            {property.ai_analysis.power_lines_street?.position && (
                              <> Lines are positioned <strong>{property.ai_analysis.power_lines_street.position.replace(/_/g, ' ')}</strong> relative to the property.</>
                            )}
                            {property.ai_analysis.power_lines?.distance_meters && (
                              <> Satellite view confirms infrastructure approximately <strong>{Math.round(property.ai_analysis.power_lines.distance_meters)}m</strong> from property center.</>
                            )}
                            {" "}Property has good utility access for easy and cost-effective electrical connection. {property.ai_analysis.power_lines_street?.position === 'directly_above' ? 'Note: Overhead clearance required for tall structures.' : 'Ideal positioning for development.'}
                          </>
                        ) : (
                          "⚠️ No overhead power lines or electrical infrastructure detected in either satellite or street view imagery. Property may lack electrical utility access - contact local utility company to verify service availability and connection costs before purchase."
                        )}
                      </p>

                      {/* Road Condition Summary */}
                      <p>
                        <span className="font-bold text-purple-700">🛣️ Access & Roads:</span>{" "}
                        {property.ai_analysis.road_condition?.type ? (
                          <>
                            Property has <strong>{property.ai_analysis.road_condition.type.toLowerCase()}</strong> road access
                            {property.ai_analysis.road_condition.confidence && (
                              <> (AI confidence: {Math.round(property.ai_analysis.road_condition.confidence * 100)}%)</>
                            )}.
                            {property.ai_analysis.road_condition.type === "PAVED" && " Excellent paved road provides reliable year-round access and supports property value."}
                            {property.ai_analysis.road_condition.type === "GRAVEL" && " Gravel surface provides adequate access but may require periodic maintenance."}
                            {property.ai_analysis.road_condition.type === "DIRT" && " Unpaved road may present challenges during wet weather and could increase development costs."}
                            {property.ai_analysis.road_condition.type === "POOR" && " Road condition shows signs of deterioration that may require repair for optimal access."}
                          </>
                        ) : (
                          "Road condition analysis inconclusive from available imagery. Ground-level verification recommended."
                        )}
                      </p>

                      {/* Development & Surroundings Summary */}
                      <p>
                        <span className="font-bold text-purple-700">🏘️ Surrounding Area:</span>{" "}
                        {property.ai_analysis.nearby_development?.type ? (
                          <>
                            Area classified as <strong>{property.ai_analysis.nearby_development.type.toLowerCase()}</strong> development
                            {property.ai_analysis.nearby_development.count ? (
                              <> with <strong>{property.ai_analysis.nearby_development.count}</strong> structures identified in the vicinity</>
                            ) : null}.
                            {property.ai_analysis.nearby_development.type === "RESIDENTIAL" && " Good for community living with established neighborhood infrastructure and services."}
                            {property.ai_analysis.nearby_development.type === "COMMERCIAL" && " Active commercial area may experience higher traffic and noise levels."}
                            {property.ai_analysis.nearby_development.type === "AGRICULTURAL" && " Rural agricultural setting offers open space and quiet surroundings."}
                            {property.ai_analysis.nearby_development.type === "UNDEVELOPED" && " Limited nearby development may indicate fewer immediate amenities and services."}
                            {property.ai_analysis.nearby_development.type === "INDUSTRIAL" && " Industrial area characteristics warrant consideration of environmental and traffic factors."}
                          </>
                        ) : (
                          "Area development pattern could not be determined from imagery. Site visit recommended for detailed assessment."
                        )}
                      </p>

                      {/* Overall Risk Factors */}
                      {property.ai_analysis.overall_risk?.factors && property.ai_analysis.overall_risk.factors.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-purple-200">
                          <p className="font-bold text-purple-700 mb-2">🎯 Key Risk Factors Identified:</p>
                          <ul className="list-disc list-inside space-y-1 text-xs">
                            {property.ai_analysis.overall_risk.factors.slice(0, 5).map((factor: string, idx: number) => (
                              <li key={idx}>{factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="mt-4 pt-4 border-t border-purple-200 text-xs text-purple-600 flex items-center justify-between">
                      <span>
                        Analysis powered by GPT-4o Vision • Model: {property.ai_analysis.model_version || "v1.0"}
                      </span>
                      {property.ai_analysis.processing_time_seconds && (
                        <span>Processed in {property.ai_analysis.processing_time_seconds.toFixed(1)}s</span>
                      )}
                    </div>
                  </div>
                  </div>
                </div>
              )}

              {/* Owner Information Section - Full Skip Trace Data */}
              {property.owner_info && property.owner_info.found && (
                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <UserSearch className="h-4 w-4 text-blue-600" />
                    Owner Information
                    {property.owner_info.contact?.phone_count && (
                      <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                        {property.owner_info.contact.phone_count} phones
                      </span>
                    )}
                    {property.owner_info.contact?.email_count && (
                      <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded-full">
                        {property.owner_info.contact.email_count} emails
                      </span>
                    )}
                  </h4>

                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border-2 border-blue-200 shadow-lg">
                    {/* Owner Name & Compliance Flags */}
                    <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
                      <div>
                        {property.owner_info.name?.full && (
                          <p className="text-lg font-bold text-blue-900 mb-2">
                            {property.owner_info.name.full}
                          </p>
                        )}
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          {property.owner_info.details?.owner_type && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
                              {property.owner_info.details.owner_type}
                            </span>
                          )}
                          {property.owner_info.details?.owner_occupied !== null && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
                              {property.owner_info.details.owner_occupied ? "Owner Occupied" : "Non-Owner Occupied"}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Compliance Flags */}
                      {property.owner_info.compliance && (
                        <div className="flex flex-wrap gap-2">
                          {property.owner_info.compliance.is_deceased && (
                            <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold flex items-center gap-1">
                              ⚠️ Deceased
                            </span>
                          )}
                          {property.owner_info.compliance.is_litigator && (
                            <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold flex items-center gap-1">
                              ⚖️ Litigator
                            </span>
                          )}
                          {property.owner_info.compliance.has_dnc && (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-bold flex items-center gap-1">
                              📵 DNC
                            </span>
                          )}
                          {property.owner_info.compliance.has_tcpa && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-bold flex items-center gap-1">
                              🚫 TCPA
                            </span>
                          )}
                          {property.owner_info.compliance.has_bankruptcy && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-bold flex items-center gap-1">
                              💰 Bankruptcy
                            </span>
                          )}
                          {property.owner_info.compliance.has_involuntary_lien && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-bold flex items-center gap-1">
                              📋 Lien
                            </span>
                          )}
                          {!property.owner_info.compliance.is_deceased &&
                           !property.owner_info.compliance.is_litigator &&
                           !property.owner_info.compliance.has_dnc &&
                           !property.owner_info.compliance.has_tcpa && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-bold flex items-center gap-1">
                              ✅ Clean
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                      {/* ALL Phone Numbers */}
                      <div className="bg-white rounded-lg p-4 border border-blue-100 shadow-sm">
                        <p className="text-sm font-bold text-blue-800 mb-3 flex items-center gap-2">
                          <Phone className="h-4 w-4" />
                          Phone Numbers
                          {property.owner_info.contact?.phone_count && property.owner_info.contact.phone_count > 0 && (
                            <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                              {property.owner_info.contact.phone_count}
                            </span>
                          )}
                        </p>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {property.owner_info.contact?.phone_list && property.owner_info.contact.phone_list.length > 0 ? (
                            property.owner_info.contact.phone_list.map((phone, idx) => (
                              <div key={idx} className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <p className="font-bold text-blue-900 text-base">
                                      {phone.formatted || phone.number}
                                    </p>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                        phone.type === 'Mobile' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                                      }`}>
                                        {phone.type}
                                      </span>
                                      {phone.tested && (
                                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">Tested</span>
                                      )}
                                    </div>
                                    <p className="text-xs text-blue-600 mt-1 truncate" title={phone.carrier}>
                                      {phone.carrier || 'Unknown carrier'}
                                    </p>
                                    {phone.last_reported_date && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        Last seen: {new Date(phone.last_reported_date).toLocaleDateString()}
                                      </p>
                                    )}
                                  </div>
                                  <div className="flex flex-col items-end gap-1.5 ml-3">
                                    <div className="flex items-center gap-1">
                                      <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                                        phone.score >= 90 ? 'bg-green-200 text-green-800' :
                                        phone.score >= 70 ? 'bg-yellow-200 text-yellow-800' :
                                        'bg-gray-200 text-gray-800'
                                      }`}>
                                        {phone.score}%
                                      </span>
                                    </div>
                                    <div className="flex flex-wrap gap-1 justify-end">
                                      {phone.reachable ? (
                                        <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">✓ Reachable</span>
                                      ) : (
                                        <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">✗ Unreachable</span>
                                      )}
                                      {phone.dnc && (
                                        <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded font-medium">📵 DNC</span>
                                      )}
                                      {phone.tcpa && (
                                        <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">🚫 TCPA</span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <>
                              {property.owner_info.contact?.phone_primary && (
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="font-semibold text-blue-900">{property.owner_info.contact.phone_primary}</p>
                                  <p className="text-xs text-blue-600">Primary</p>
                                </div>
                              )}
                              {property.owner_info.contact?.phone_mobile && property.owner_info.contact.phone_mobile !== property.owner_info.contact.phone_primary && (
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="font-semibold text-blue-900">{property.owner_info.contact.phone_mobile}</p>
                                  <p className="text-xs text-blue-600">Mobile</p>
                                </div>
                              )}
                              {property.owner_info.contact?.phone_secondary && (
                                <div className="p-2 bg-blue-50 rounded-lg">
                                  <p className="font-semibold text-blue-900">{property.owner_info.contact.phone_secondary}</p>
                                  <p className="text-xs text-blue-600">Secondary</p>
                                </div>
                              )}
                            </>
                          )}
                          {!property.owner_info.contact?.phone_list?.length && !property.owner_info.contact?.phone_primary && (
                            <p className="text-sm text-gray-500 italic">No phone numbers found</p>
                          )}
                        </div>
                      </div>

                      {/* ALL Email Addresses */}
                      <div className="bg-white rounded-lg p-4 border border-green-100 shadow-sm">
                        <p className="text-sm font-bold text-green-800 mb-3 flex items-center gap-2">
                          <Mail className="h-4 w-4" />
                          Email Addresses
                          {property.owner_info.contact?.email_count && (
                            <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded-full">
                              {property.owner_info.contact.email_count}
                            </span>
                          )}
                        </p>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {property.owner_info.contact?.email_list && property.owner_info.contact.email_list.length > 0 ? (
                            property.owner_info.contact.email_list.map((email, idx) => (
                              <div key={idx} className="p-2 bg-green-50 rounded-lg text-sm flex items-center justify-between">
                                <p className="font-semibold text-green-900 break-all">{email.email}</p>
                                {email.tested && (
                                  <span className="text-xs bg-green-200 text-green-800 px-1.5 py-0.5 rounded ml-2 flex-shrink-0">
                                    Verified
                                  </span>
                                )}
                              </div>
                            ))
                          ) : (
                            <>
                              {property.owner_info.contact?.email_primary && (
                                <div className="p-2 bg-green-50 rounded-lg">
                                  <p className="font-semibold text-green-900 break-all">{property.owner_info.contact.email_primary}</p>
                                </div>
                              )}
                              {property.owner_info.contact?.email_secondary && (
                                <div className="p-2 bg-green-50 rounded-lg">
                                  <p className="font-semibold text-green-900 break-all">{property.owner_info.contact.email_secondary}</p>
                                </div>
                              )}
                            </>
                          )}
                          {!property.owner_info.contact?.email_list?.length && !property.owner_info.contact?.email_primary && (
                            <p className="text-sm text-gray-500 italic">No email addresses found</p>
                          )}
                        </div>
                      </div>

                      {/* Mailing Address */}
                      <div className="bg-white rounded-lg p-4 border border-purple-100 shadow-sm">
                        <p className="text-sm font-bold text-purple-800 mb-3 flex items-center gap-2">
                          <Home className="h-4 w-4" />
                          Mailing Address
                        </p>
                        {property.owner_info.mailing_address?.full ? (
                          <div className="space-y-2">
                            <div className="p-3 bg-purple-50 rounded-lg">
                              <p className="font-semibold text-purple-900">
                                {property.owner_info.mailing_address.street}
                              </p>
                              <p className="text-sm text-purple-700">
                                {property.owner_info.mailing_address.city}, {property.owner_info.mailing_address.state} {property.owner_info.mailing_address.zip}
                                {property.owner_info.mailing_address.zip_plus4 && `-${property.owner_info.mailing_address.zip_plus4}`}
                              </p>
                              {property.owner_info.mailing_address.county && (
                                <p className="text-xs text-purple-600 mt-1">
                                  {property.owner_info.mailing_address.county} County
                                </p>
                              )}
                            </div>
                            {property.owner_info.mailing_address.validity && (
                              <div className="flex items-center gap-1 text-xs">
                                {property.owner_info.mailing_address.validity === 'Valid' ? (
                                  <span className="text-green-600">✓ Address Verified</span>
                                ) : (
                                  <span className="text-yellow-600">⚠ {property.owner_info.mailing_address.validity}</span>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">No mailing address found</p>
                        )}
                      </div>
                    </div>

                    {/* Metadata Footer */}
                    <div className="mt-5 pt-4 border-t border-blue-200 flex flex-wrap items-center justify-between gap-2 text-xs text-blue-700">
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="font-medium">Source: {property.owner_info.metadata?.source || "BatchData API"}</span>
                        {property.owner_info.metadata?.confidence !== null && property.owner_info.metadata?.confidence !== undefined && (
                          <span>Confidence: {Math.round(property.owner_info.metadata.confidence * 100)}%</span>
                        )}
                        {property.owner_info.metadata?.processing_time_seconds && (
                          <span>Processed in {property.owner_info.metadata.processing_time_seconds.toFixed(1)}s</span>
                        )}
                      </div>
                      {property.owner_info.metadata?.retrieved_at && (
                        <span className="text-blue-500">
                          Retrieved: {new Date(property.owner_info.metadata.retrieved_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* No Owner Info Found or Pending */}
              {property.owner_info && !property.owner_info.found && (
                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <UserSearch className="h-4 w-4 text-slate-400" />
                    Owner Information
                  </h4>
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 text-center">
                    {property.owner_info.status === 'pending' ? (
                      <>
                        <p className="text-sm text-slate-600">🔍 Searching for owner...</p>
                        <p className="text-xs text-slate-500 mt-1">This may take a few moments</p>
                      </>
                    ) : property.owner_info.status === 'error' ? (
                      <>
                        <p className="text-sm text-red-600">❌ Search failed</p>
                        <p className="text-xs text-slate-500 mt-1">Please try again later</p>
                      </>
                    ) : (
                      <>
                        <p className="text-sm text-slate-600">No owner information available</p>
                        <p className="text-xs text-slate-500 mt-1">Owner not found in public records</p>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Owner Info Not Yet Searched */}
              {!property.owner_info && (
                <div className="mt-6">
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200 text-center">
                    <p className="text-sm text-yellow-800">💡 Click "Find Owners" above to search for owner contact information</p>
                  </div>
                </div>
              )}
            </motion.div>
          </td>
        </tr>
      )}
    </>
  );
}
