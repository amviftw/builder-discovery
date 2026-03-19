"use client";

import { PIPELINE_STAGES, STAGE_COLORS, type PipelineStage } from "@/lib/types";

interface PipelineFunnelProps {
  counts: Record<string, number>;
}

export function PipelineFunnel({ counts }: PipelineFunnelProps) {
  const maxCount = Math.max(...PIPELINE_STAGES.map((s) => counts[s] || 0), 1);

  return (
    <div className="space-y-2">
      {PIPELINE_STAGES.map((stage) => {
        const count = counts[stage] || 0;
        const pct = (count / maxCount) * 100;
        return (
          <div key={stage} className="flex items-center gap-3">
            <span className="text-xs text-gray-600 w-20 text-right capitalize">
              {stage}
            </span>
            <div className="flex-1 h-7 bg-gray-50 rounded-md overflow-hidden relative">
              <div
                className="h-full rounded-md transition-all duration-500"
                style={{
                  width: `${Math.max(pct, 2)}%`,
                  backgroundColor: STAGE_COLORS[stage as PipelineStage],
                }}
              />
              <span className="absolute inset-0 flex items-center px-2 text-xs font-medium text-gray-700">
                {count}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
