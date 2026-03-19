import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "—";
  return (score * 100).toFixed(0);
}

export function formatScoreDecimal(score: number | null | undefined): string {
  if (score == null) return "—";
  return score.toFixed(3);
}

export function scoreColor(score: number | null | undefined): string {
  if (score == null) return "text-gray-400";
  if (score >= 0.7) return "text-green-600";
  if (score >= 0.4) return "text-yellow-600";
  return "text-gray-500";
}

export function scoreBg(score: number | null | undefined): string {
  if (score == null) return "bg-gray-100";
  if (score >= 0.7) return "bg-green-50";
  if (score >= 0.4) return "bg-yellow-50";
  return "bg-gray-50";
}

export function stageColor(stage: string): string {
  const colors: Record<string, string> = {
    discovered: "bg-gray-100 text-gray-700",
    enriched: "bg-blue-100 text-blue-700",
    scored: "bg-indigo-100 text-indigo-700",
    classified: "bg-purple-100 text-purple-700",
    verified: "bg-teal-100 text-teal-700",
    outreach: "bg-orange-100 text-orange-700",
    engaged: "bg-green-100 text-green-700",
  };
  return colors[stage] || "bg-gray-100 text-gray-700";
}

export function founderFitLabel(fit: string | null): string {
  const labels: Record<string, string> = {
    good_builder_good_founder: "Strong Founder Fit",
    good_builder_not_founder: "Builder (Not Founder)",
    okay_builder: "Okay Builder",
  };
  return fit ? labels[fit] || fit : "Unclassified";
}

export function founderFitColor(fit: string | null): string {
  const colors: Record<string, string> = {
    good_builder_good_founder: "bg-green-100 text-green-800",
    good_builder_not_founder: "bg-blue-100 text-blue-800",
    okay_builder: "bg-gray-100 text-gray-700",
  };
  return fit ? colors[fit] || "bg-gray-100 text-gray-700" : "bg-gray-50 text-gray-500";
}

export function builderTypeLabel(type: string | null): string {
  const labels: Record<string, string> = {
    generalist: "Generalist",
    product_leader: "Product Leader",
    engineer: "Engineer",
  };
  return type ? labels[type] || type : "Unknown";
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString();
}

export function signalIcon(type: string): string {
  const icons: Record<string, string> = {
    activity_dip: "📉",
    activity_spike: "📈",
    internal_tool_shipped: "🔧",
    vesting_cliff_approaching: "⏰",
    resignation_clump_member: "👥",
    org_departure: "🚪",
    hireable_flag_on: "🏳️",
  };
  return icons[type] || "📌";
}
