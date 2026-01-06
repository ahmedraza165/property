import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-US").format(num);
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function getRiskColor(risk: string): string {
  switch (risk?.toUpperCase()) {
    case "LOW":
      return "text-green-700 bg-green-50 border-green-200";
    case "MEDIUM":
      return "text-yellow-700 bg-yellow-50 border-yellow-200";
    case "HIGH":
      return "text-red-700 bg-red-50 border-red-200";
    default:
      return "text-gray-700 bg-gray-50 border-gray-200";
  }
}

export function getRiskBadgeColor(risk: string): { bg: string; text: string; border: string } {
  switch (risk?.toUpperCase()) {
    case "LOW":
      return { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" };
    case "MEDIUM":
      return { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" };
    case "HIGH":
      return { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" };
    default:
      return { bg: "bg-gray-50", text: "text-gray-700", border: "border-gray-200" };
  }
}

export function downloadCSV(data: any[], filename: string, disclaimer?: string) {
  if (!data.length) return;

  const headers = Object.keys(data[0]);
  const rows = [
    headers.join(","),
    ...data.map((row) =>
      headers.map((header) => {
        const value = row[header];
        if (value === null || value === undefined) return "";
        const stringValue = String(value);
        return stringValue.includes(",") ? `"${stringValue}"` : stringValue;
      }).join(",")
    ),
  ];

  // Add disclaimer at the top if provided
  const csvContent = disclaimer
    ? [`"${disclaimer}"\n`, ...rows].join("\n")
    : rows.join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
