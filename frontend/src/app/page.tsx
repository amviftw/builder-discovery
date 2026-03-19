"use client";

import { useApi } from "@/hooks/use-api";
import { fetchDashboard } from "@/lib/api";
import { LoadingPage, ErrorState } from "@/components/ui/loading";
import { PipelineFunnel } from "@/components/charts/pipeline-funnel";
import { PersonCard } from "@/components/people/person-card";
import { signalIcon, timeAgo, formatScore, scoreColor } from "@/lib/utils";

// Matches actual backend /dashboard/overview response
interface DashboardResponse {
  total_people: number;
  new_this_week: number;
  pipeline_stats: Record<string, number>;
  top_scored_people: {
    id: string;
    display_name: string | null;
    founder_propensity_score: number | null;
    builder_type: string | null;
    pipeline_stage: string;
    avatar_url: string | null;
  }[];
  recent_signals: {
    id: string;
    signal_type: string;
    signal_strength: number;
    person_id: string;
    detected_at: string | null;
  }[];
}

export default function DashboardPage() {
  const { data, loading, error, refetch } = useApi<DashboardResponse>(
    fetchDashboard
  );

  if (loading) return <LoadingPage />;
  if (error)
    return (
      <ErrorState
        message={error}
        onRetry={refetch}
      />
    );
  if (!data) return null;

  const classifiedCount = data.pipeline_stats?.classified || 0;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Builder discovery pipeline overview
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Builders" value={data.total_people} />
        <KpiCard label="New This Week" value={data.new_this_week} />
        <KpiCard label="Classified" value={classifiedCount} />
        <KpiCard
          label="Active Signals"
          value={data.recent_signals?.length || 0}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Pipeline Funnel */}
        <div className="col-span-5 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Pipeline Funnel
          </h2>
          <PipelineFunnel counts={data.pipeline_stats || {}} />
        </div>

        {/* Top Scored Builders */}
        <div className="col-span-7 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">
            Top Scored Builders
          </h2>
          <div className="space-y-0.5">
            {data.top_scored_people && data.top_scored_people.length > 0 ? (
              data.top_scored_people.slice(0, 8).map((person) => (
                <PersonCard
                  key={person.id}
                  person={{
                    id: person.id,
                    display_name: person.display_name,
                    avatar_url: person.avatar_url,
                    founder_propensity_score: person.founder_propensity_score,
                    pipeline_stage: person.pipeline_stage as any,
                    builder_type: person.builder_type as any,
                    location: null,
                    country: null,
                    builder_experience: null,
                    founder_fit: null,
                    technical_score: null,
                    momentum_score: null,
                    ai_nativeness_score: null,
                    leadership_score: null,
                    departure_signal_score: null,
                    tags: [],
                    created_at: null,
                  }}
                  compact
                />
              ))
            ) : (
              <p className="text-sm text-gray-400 py-4 text-center">
                No scored builders yet. Run the pipeline to discover builders.
              </p>
            )}
          </div>
        </div>

        {/* Recent Signals */}
        <div className="col-span-12 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">
            Recent Signals
          </h2>
          {data.recent_signals && data.recent_signals.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {data.recent_signals.slice(0, 10).map((signal) => (
                <div
                  key={signal.id}
                  className="flex items-center gap-3 py-2.5"
                >
                  <span className="text-lg">
                    {signalIcon(signal.signal_type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 capitalize">
                      {signal.signal_type.replace(/_/g, " ")}
                    </p>
                    <p className="text-xs text-gray-500">
                      Strength: {(signal.signal_strength * 100).toFixed(0)}%
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {timeAgo(signal.detected_at)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-4 text-center">
              No signals detected yet. Run discovery and scoring to generate
              signals.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="card p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
