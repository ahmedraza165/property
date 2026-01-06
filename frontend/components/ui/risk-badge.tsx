import { cn } from "@/lib/utils";
import { AlertTriangle, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";

interface RiskBadgeProps {
  risk: string;
  className?: string;
  showIcon?: boolean;
}

export function RiskBadge({ risk, className, showIcon = true }: RiskBadgeProps) {
  const riskUpper = risk?.toUpperCase();

  const riskStyles = {
    LOW: {
      bg: "bg-gradient-to-r from-green-500 to-green-600",
      text: "text-white",
      shadow: "shadow-lg shadow-green-500/30",
      icon: CheckCircle2
    },
    MEDIUM: {
      bg: "bg-gradient-to-r from-yellow-500 to-yellow-600",
      text: "text-white",
      shadow: "shadow-lg shadow-yellow-500/30",
      icon: AlertCircle
    },
    HIGH: {
      bg: "bg-gradient-to-r from-red-500 to-red-600",
      text: "text-white",
      shadow: "shadow-lg shadow-red-500/30",
      icon: AlertTriangle
    },
    UNKNOWN: {
      bg: "bg-gradient-to-r from-slate-500 to-slate-600",
      text: "text-white",
      shadow: "shadow-lg shadow-slate-500/30",
      icon: Sparkles
    }
  };

  const style = riskStyles[riskUpper as keyof typeof riskStyles] || riskStyles.UNKNOWN;
  const Icon = style.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105",
        style.bg,
        style.text,
        style.shadow,
        className
      )}
    >
      {showIcon && Icon && <Icon className="h-4 w-4" />}
      {riskUpper || "UNKNOWN"}
    </span>
  );
}
