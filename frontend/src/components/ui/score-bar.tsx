import { cn } from "@/lib/utils";

interface ScoreBarProps {
  label: string;
  value: number | null | undefined;
  color?: string;
}

export function ScoreBar({ label, value, color = "bg-brand-500" }: ScoreBarProps) {
  const pct = value != null ? Math.round(value * 100) : 0;

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-600">{label}</span>
        <span className="text-xs font-medium text-gray-900">
          {value != null ? pct : "—"}
        </span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
