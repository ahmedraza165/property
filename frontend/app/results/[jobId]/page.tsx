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
import { PropertyResult } from "@/lib/api";
import { motion } from "framer-motion";
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
  Ruler,
  MapPinned,
  Waves,
  Zap,
  Image as ImageIcon,
  Sparkles,
  UserSearch,
  Phone,
  Mail,
  Home,
} from "lucide-react";
import { formatNumber, downloadCSV } from "@/lib/utils";

export default function ResultsPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = use(params);
  const { data: results, isLoading, error } = useJobResults(jobId);
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

  const handleTriggerAI = async () => {
    try {
      await triggerAI.mutateAsync(jobId);
      alert("AI analysis started! Refresh the page after a few minutes to see results.");
    } catch (error) {
      alert("Failed to start AI analysis. Please try again.");
    }
  };

  const handleTriggerSkipTrace = async () => {
    try {
      const response = await triggerSkipTrace.mutateAsync(jobId);
      const alreadyTraced = response.already_traced || 0;
      const totalProps = response.total_properties || 0;
      const toProcess = totalProps - alreadyTraced;

      if (toProcess === 0) {
        alert(`All ${totalProps} properties already have owner information!`);
      } else {
        alert(`Finding owners for ${toProcess} properties...\nThis may take a few minutes. The page will auto-refresh with results.`);
      }
    } catch (error) {
      alert("Failed to start skip tracing. Please try again.");
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

  const handleSort = (key: string) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  };

  const handleExport = () => {
    if (!filteredAndSortedResults.length) return;

    const exportData = filteredAndSortedResults.map((property) => ({
      Address: property.address.full_address,
      "Postal Code": property.address.zip || "N/A",
      County: property.address.county || "N/A",
      "Overall Risk": property.phase1_risk?.overall_risk || "N/A",
      Wetlands: property.phase1_risk?.wetlands.status || "N/A",
      "Flood Zone": property.phase1_risk?.flood_zone.zone || "N/A",
      "Flood Severity": property.phase1_risk?.flood_zone.severity || "N/A",
      "Slope %": property.phase1_risk?.slope.percentage || "N/A",
      "Road Access": property.phase1_risk?.road_access.has_access ? "Yes" : "No",
      Landlocked: property.phase1_risk?.landlocked ? "Yes" : "No",
      "Protected Land": property.phase1_risk?.protected_land.is_protected ? "Yes" : "No",
      "Water Available": property.phase1_risk?.water_utility.water_available === true ? "Yes" : property.phase1_risk?.water_utility.water_available === false ? "No" : "Unknown",
      "Sewer Available": property.phase1_risk?.water_utility.sewer_available === true ? "Yes" : property.phase1_risk?.water_utility.sewer_available === false ? "No" : "Unknown",
      "Legal Description": property.property_details?.legal_description || "N/A",

      // Owner Information
      "Owner Name": property.owner_info?.name?.full || "N/A",
      "Owner Type": property.owner_info?.details?.owner_type || "N/A",
      "Owner Occupied": property.owner_info?.details?.owner_occupied === true ? "Yes" : property.owner_info?.details?.owner_occupied === false ? "No" : "N/A",
      "Phone Primary": property.owner_info?.contact?.phone_primary || "N/A",
      "Phone Mobile": property.owner_info?.contact?.phone_mobile || "N/A",
      "Email Primary": property.owner_info?.contact?.email_primary || "N/A",
      "Mailing Address": property.owner_info?.mailing_address?.full || "N/A",
      "Owner Info Source": property.owner_info?.metadata?.source || "N/A",
      "Owner Info Confidence": property.owner_info?.metadata?.confidence ? `${Math.round(property.owner_info.metadata.confidence * 100)}%` : "N/A",
    }));

    // Add disclaimer at the top of CSV
    const disclaimer = "DISCLAIMER: This report is for informational purposes only and should not be construed as legal advice. Property buyers should conduct their own due diligence and consult with qualified professionals before making any purchasing decisions. The data provided herein is sourced from publicly available datasets and may not be complete or current.";

    downloadCSV(exportData, `property-analysis-${jobId}.csv`, disclaimer);
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
                disabled={triggerSkipTrace.isPending}
              >
                <UserSearch className="h-5 w-5" />
                {triggerSkipTrace.isPending ? "Starting..." : "Find Owners"}
              </Button>
              <Button onClick={handleExport} variant="secondary" size="lg" className="gap-2 shadow-2xl shadow-green-500/30">
                <Download className="h-5 w-5" />
                Export CSV
              </Button>
            </div>
          </div>

          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                title="Total Properties"
                value={summary.total_properties}
                icon={Building2}
                color="gray"
                delay={0}
              />
              <StatCard
                title="High Risk"
                value={summary.risk_distribution.high}
                icon={AlertTriangle}
                color="red"
                delay={0.1}
              />
              <StatCard
                title="Medium Risk"
                value={summary.risk_distribution.medium}
                icon={AlertCircle}
                color="yellow"
                delay={0.2}
              />
              <StatCard
                title="Low Risk"
                value={summary.risk_distribution.low}
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
        <td className="px-6 py-5 text-right">
          <button className="p-2 rounded-xl bg-white border-2 border-slate-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm group-hover:scale-110">
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </button>
        </td>
      </motion.tr>
      {isExpanded && risk && (
        <tr>
          <td colSpan={4} className="px-6 py-4 bg-slate-50">
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

                    {/* Street View Image - ONLY */}
                    {property.ai_analysis.imagery?.street?.url && (
                      <div className="mb-6">
                        <div className="relative group overflow-hidden rounded-lg shadow-xl">
                          <img
                            src={property.ai_analysis.imagery.street.url}
                            alt="Street view analysis"
                            className="w-full h-64 object-cover"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                            <div className="flex items-center gap-2 bg-white/90 backdrop-blur-sm text-purple-900 text-xs font-semibold px-3 py-1.5 rounded-full">
                              <ImageIcon className="h-3 w-3" />
                              Street View Analysis - {property.ai_analysis.imagery.street.source}
                            </div>
                            <div className="bg-green-500/90 backdrop-blur-sm text-white text-xs font-bold px-3 py-1.5 rounded-full">
                              ✓ AI Analyzed
                            </div>
                          </div>
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
                        <div className="flex items-center gap-2">
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
                        <p className="text-sm font-semibold text-yellow-700">
                          ~{Math.round(property.ai_analysis.power_lines.distance_meters)}m away
                        </p>
                      )}
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
                      {property.ai_analysis.nearby_development?.count !== null && (
                        <p className="text-sm font-semibold text-green-700">
                          {property.ai_analysis.nearby_development.count} structures detected
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
                  </div>
                </div>
              )}

              {/* Owner Information Section */}
              {property.owner_info && property.owner_info.found && (
                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <UserSearch className="h-4 w-4 text-blue-600" />
                    Owner Information
                  </h4>

                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-5 border border-blue-200">
                    {/* Owner Name */}
                    {property.owner_info.name?.full && (
                      <div className="mb-4">
                        <p className="text-sm font-semibold text-blue-900 mb-1">
                          {property.owner_info.name.full}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-blue-700">
                          {property.owner_info.details?.owner_type && (
                            <span className="px-2 py-1 bg-blue-100 rounded">
                              {property.owner_info.details.owner_type}
                            </span>
                          )}
                          {property.owner_info.details?.owner_occupied !== null && (
                            <span className="px-2 py-1 bg-blue-100 rounded">
                              {property.owner_info.details.owner_occupied ? "Owner Occupied" : "Non-Owner Occupied"}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Contact Information */}
                      <div className="space-y-3">
                        {/* Phone Numbers */}
                        {(property.owner_info.contact?.phone_primary ||
                          property.owner_info.contact?.phone_mobile ||
                          property.owner_info.contact?.phone_secondary) && (
                          <div>
                            <p className="text-xs font-medium text-blue-800 mb-2 flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              Phone Numbers
                            </p>
                            <div className="space-y-1">
                              {property.owner_info.contact.phone_primary && (
                                <p className="text-sm text-blue-900 flex items-center gap-2">
                                  <span className="text-xs text-blue-600">Primary:</span>
                                  {property.owner_info.contact.phone_primary}
                                </p>
                              )}
                              {property.owner_info.contact.phone_mobile && (
                                <p className="text-sm text-blue-900 flex items-center gap-2">
                                  <span className="text-xs text-blue-600">Mobile:</span>
                                  {property.owner_info.contact.phone_mobile}
                                </p>
                              )}
                              {property.owner_info.contact.phone_secondary && (
                                <p className="text-sm text-blue-900 flex items-center gap-2">
                                  <span className="text-xs text-blue-600">Other:</span>
                                  {property.owner_info.contact.phone_secondary}
                                </p>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Email Addresses */}
                        {(property.owner_info.contact?.email_primary ||
                          property.owner_info.contact?.email_secondary) && (
                          <div>
                            <p className="text-xs font-medium text-blue-800 mb-2 flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              Email Addresses
                            </p>
                            <div className="space-y-1">
                              {property.owner_info.contact.email_primary && (
                                <p className="text-sm text-blue-900 break-all">
                                  {property.owner_info.contact.email_primary}
                                </p>
                              )}
                              {property.owner_info.contact.email_secondary && (
                                <p className="text-sm text-blue-900 break-all">
                                  {property.owner_info.contact.email_secondary}
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Mailing Address */}
                      {property.owner_info.mailing_address?.full && (
                        <div>
                          <p className="text-xs font-medium text-blue-800 mb-2 flex items-center gap-1">
                            <Home className="h-3 w-3" />
                            Mailing Address
                          </p>
                          <p className="text-sm text-blue-900">
                            {property.owner_info.mailing_address.full}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className="mt-4 pt-3 border-t border-blue-200 flex items-center justify-between text-xs text-blue-700">
                      <div className="flex items-center gap-3">
                        <span>Source: {property.owner_info.metadata?.source || "Unknown"}</span>
                        {property.owner_info.metadata?.confidence !== null && (
                          <span>Confidence: {Math.round(property.owner_info.metadata.confidence * 100)}%</span>
                        )}
                      </div>
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
