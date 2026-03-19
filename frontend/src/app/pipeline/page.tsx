"use client";

import { useState } from "react";
import { useApi } from "@/hooks/use-api";
import { fetchPeople, fetchPipelineStats, advancePipelineStage } from "@/lib/api";
import { LoadingPage, ErrorState, EmptyState } from "@/components/ui/loading";
import { PersonCard } from "@/components/people/person-card";
import { PIPELINE_STAGES, STAGE_COLORS, type PipelineStage, type PersonSummary } from "@/lib/types";

export default function PipelinePage() {
  const { data: stats, loading: statsLoading, error: statsError, refetch: refetchStats } = useApi(fetchPipelineStats);
  const [selectedStage, setSelectedStage] = useState<PipelineStage>("discovered");

  const { data: stageData, loading: peopleLoading, refetch: refetchPeople } = useApi<{
    items: PersonSummary[];
    total: number;
    page: number;
    pages: number;
  }>(
    () => fetchPeople({ pipeline_stage: selectedStage, sort_by: "score", sort_dir: "desc", page_size: 50 }),
    [selectedStage]
  );

  if (statsLoading) return <LoadingPage />;
  if (statsError) return <ErrorState message={statsError} onRetry={refetchStats} />;

  // Backend returns stages as {discovered: 0, enriched: 0, ...} object
  const stageCounts: Record<string, number> = stats?.stages || {};

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
        <p className="text-sm text-gray-500 mt-1">
          Track builders through the discovery pipeline
        </p>
      </div>

      {/* Stage tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {PIPELINE_STAGES.map((stage) => {
          const count = stageCounts[stage] || 0;
          const isActive = stage === selectedStage;
          return (
            <button
              key={stage}
              onClick={() => setSelectedStage(stage)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                isActive
                  ? "bg-white shadow-sm border border-gray-200"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: STAGE_COLORS[stage] }}
              />
              <span className={isActive ? "text-gray-900" : ""}>
                {stage.charAt(0).toUpperCase() + stage.slice(1)}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  isActive
                    ? "bg-brand-100 text-brand-700"
                    : "bg-gray-100 text-gray-500"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Stage content */}
      <div className="card">
        {peopleLoading ? (
          <LoadingPage />
        ) : !stageData || stageData.items.length === 0 ? (
          <EmptyState message={`No builders in the ${selectedStage} stage.`} />
        ) : (
          <div className="divide-y divide-gray-100">
            {stageData.items.map((person) => (
              <div key={person.id} className="p-4">
                <PersonCard person={person} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pipeline overview bar */}
      <div className="card p-5 mt-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Pipeline Overview</h2>
        <div className="flex gap-1 h-8">
          {PIPELINE_STAGES.map((stage) => {
            const count = stageCounts[stage] || 0;
            const total = stats?.total || 1;
            const pct = Math.max((count / total) * 100, 1);
            return (
              <div
                key={stage}
                className="rounded-md relative group cursor-pointer"
                style={{
                  width: `${pct}%`,
                  backgroundColor: STAGE_COLORS[stage],
                  minWidth: count > 0 ? "24px" : "4px",
                }}
                onClick={() => setSelectedStage(stage)}
              >
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                  <div className="bg-gray-900 text-white text-xs rounded-lg px-2 py-1 whitespace-nowrap">
                    {stage}: {count}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-[10px] text-gray-400">Discovered</span>
          <span className="text-[10px] text-gray-400">Engaged</span>
        </div>
      </div>
    </div>
  );
}
