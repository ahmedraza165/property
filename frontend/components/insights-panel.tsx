"use client";

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Droplets,
  Mountain,
  Car,
  Shield,
  MapPin,
  CheckCircle2
} from "lucide-react";
import { JobSummary } from "@/lib/api";
import { formatNumber, formatPercentage } from "@/lib/utils";

interface InsightsPanelProps {
  summary: JobSummary;
}

export function InsightsPanel({ summary }: InsightsPanelProps) {
  const totalProps = summary.total_properties;
  const riskFactors = summary.risk_factors;

  const insights = [
    {
      title: "Wetlands Present",
      value: riskFactors.wetlands,
      percentage: (riskFactors.wetlands / totalProps) * 100,
      icon: Droplets,
      color: "blue",
      severity: riskFactors.wetlands > totalProps * 0.3 ? "high" : "medium",
      description: "Properties with wetland features detected"
    },
    {
      title: "High Flood Risk",
      value: riskFactors.high_flood_zone,
      percentage: (riskFactors.high_flood_zone / totalProps) * 100,
      icon: AlertTriangle,
      color: "red",
      severity: riskFactors.high_flood_zone > totalProps * 0.2 ? "high" : "low",
      description: "Properties in high-risk flood zones"
    },
    {
      title: "Landlocked Parcels",
      value: riskFactors.landlocked,
      percentage: (riskFactors.landlocked / totalProps) * 100,
      icon: MapPin,
      color: "orange",
      severity: riskFactors.landlocked > totalProps * 0.1 ? "high" : "low",
      description: "Properties without direct road access"
    },
    {
      title: "Protected Land",
      value: riskFactors.protected_land,
      percentage: (riskFactors.protected_land / totalProps) * 100,
      icon: Shield,
      color: "green",
      severity: riskFactors.protected_land > totalProps * 0.15 ? "high" : "low",
      description: "Properties on conservation/protected land"
    }
  ];

  const riskDistribution = [
    {
      label: "Low Risk",
      value: summary.risk_distribution.low,
      percentage: summary.percentages.low_risk,
      color: "bg-green-500",
      icon: CheckCircle2
    },
    {
      label: "Medium Risk",
      value: summary.risk_distribution.medium,
      percentage: summary.percentages.medium_risk,
      color: "bg-yellow-500",
      icon: AlertTriangle
    },
    {
      label: "High Risk",
      value: summary.risk_distribution.high,
      percentage: summary.percentages.high_risk,
      color: "bg-red-500",
      icon: AlertTriangle
    }
  ];

  return (
    <div className="space-y-6">
      {/* Risk Distribution Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Distribution Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskDistribution.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${item.label === "Low Risk" ? "text-green-600" : item.label === "Medium Risk" ? "text-yellow-600" : "text-red-600"}`} />
                      <span className="text-sm font-medium text-slate-700">{item.label}</span>
                    </div>
                    <span className="text-sm font-semibold text-slate-900">
                      {formatNumber(item.value)} ({item.percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="relative h-3 bg-slate-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percentage}%` }}
                      transition={{ duration: 0.8, delay: index * 0.1 }}
                      className={`absolute inset-y-0 left-0 ${item.color} rounded-full`}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Risk Factors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, index) => {
          const Icon = insight.icon;
          const colorClasses = {
            blue: "bg-blue-50 text-blue-600 border-blue-200",
            red: "bg-red-50 text-red-600 border-red-200",
            orange: "bg-orange-50 text-orange-600 border-orange-200",
            green: "bg-green-50 text-green-600 border-green-200"
          };

          return (
            <motion.div
              key={insight.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card hover className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-xl border ${colorClasses[insight.color as keyof typeof colorClasses]}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-slate-900">{formatNumber(insight.value)}</p>
                      <p className="text-sm text-muted-foreground">{insight.percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-1">{insight.title}</h3>
                  <p className="text-sm text-muted-foreground">{insight.description}</p>

                  {insight.severity === "high" && (
                    <div className="mt-3 flex items-center gap-2 text-xs font-medium text-orange-700 bg-orange-50 px-3 py-1.5 rounded-lg border border-orange-200">
                      <AlertTriangle className="h-3 w-3" />
                      High concentration detected
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Key Insights Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {summary.percentages.high_risk > 20 && (
              <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <p className="font-medium text-red-900">High Risk Alert</p>
                  <p className="text-sm text-red-700">
                    {summary.percentages.high_risk.toFixed(1)}% of properties have high risk factors.
                    Review flood zones, wetlands, and access issues carefully.
                  </p>
                </div>
              </div>
            )}

            {riskFactors.landlocked > 0 && (
              <div className="flex items-start gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <Car className="h-5 w-5 text-orange-600 mt-0.5" />
                <div>
                  <p className="font-medium text-orange-900">Access Concerns</p>
                  <p className="text-sm text-orange-700">
                    {formatNumber(riskFactors.landlocked)} properties may be landlocked or have limited road access.
                    Verify access rights before purchase.
                  </p>
                </div>
              </div>
            )}

            {riskFactors.wetlands > totalProps * 0.3 && (
              <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <Droplets className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-900">Wetland Concentration</p>
                  <p className="text-sm text-blue-700">
                    {((riskFactors.wetlands / totalProps) * 100).toFixed(1)}% of properties have wetlands.
                    Development restrictions may apply.
                  </p>
                </div>
              </div>
            )}

            {summary.percentages.low_risk > 60 && (
              <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-green-900">Strong Portfolio</p>
                  <p className="text-sm text-green-700">
                    {summary.percentages.low_risk.toFixed(1)}% of properties are low risk.
                    Good fundamentals for investment.
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
