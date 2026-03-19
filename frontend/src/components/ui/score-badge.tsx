import { cn, formatScore, scoreBg, scoreColor } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number | null | undefined;
  label?: string;
  size?: "sm" | "md" | "lg";
}

export function ScoreBadge({ score, label, size = "md" }: ScoreBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3 py-1.5 font-semibold",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        scoreBg(score),
        scoreColor(score),
        sizeClasses[size]
      )}
    >
      {label && <span className="text-gray-500 font-normal">{label}</span>}
      {formatScore(score)}
    </span>
  );
}
