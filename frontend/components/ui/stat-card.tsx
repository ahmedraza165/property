"use client";

import { Card } from "./card";
import { cn, formatNumber } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface StatCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  description?: string;
  trend?: {
    value: number;
    positive: boolean;
  };
  color?: "blue" | "green" | "yellow" | "red" | "gray";
  delay?: number;
}

export function StatCard({ title, value, icon: Icon, description, trend, color = "blue", delay = 0 }: StatCardProps) {
  const colors = {
    blue: {
      bg: "bg-gradient-to-br from-blue-500 to-blue-600",
      text: "text-blue-600",
      glow: "shadow-blue-500/20"
    },
    green: {
      bg: "bg-gradient-to-br from-green-500 to-green-600",
      text: "text-green-600",
      glow: "shadow-green-500/20"
    },
    yellow: {
      bg: "bg-gradient-to-br from-yellow-500 to-yellow-600",
      text: "text-yellow-600",
      glow: "shadow-yellow-500/20"
    },
    red: {
      bg: "bg-gradient-to-br from-red-500 to-red-600",
      text: "text-red-600",
      glow: "shadow-red-500/20"
    },
    gray: {
      bg: "bg-gradient-to-br from-slate-600 to-slate-700",
      text: "text-slate-600",
      glow: "shadow-slate-500/20"
    },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -5 }}
    >
      <Card hover gradient className="overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-600 uppercase tracking-wide">{title}</p>
              <p className={cn("text-4xl font-extrabold mt-3", colors[color].text)}>
                {typeof value === "number" ? formatNumber(value) : value}
              </p>
              {description && <p className="text-xs text-muted-foreground mt-2">{description}</p>}
              {trend && (
                <div className="flex items-center gap-1 mt-3">
                  <span
                    className={cn(
                      "text-sm font-bold px-2 py-1 rounded-lg",
                      trend.positive ? "text-green-700 bg-green-50" : "text-red-700 bg-red-50"
                    )}
                  >
                    {trend.positive ? "↑" : "↓"} {Math.abs(trend.value)}%
                  </span>
                  <span className="text-xs text-muted-foreground">vs last upload</span>
                </div>
              )}
            </div>
            <div className={cn("p-4 rounded-2xl shadow-xl", colors[color].bg, colors[color].glow)}>
              <Icon className="h-8 w-8 text-white" />
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
