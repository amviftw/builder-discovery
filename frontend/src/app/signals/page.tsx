"use client";

import { useState } from "react";
import { useApi } from "@/hooks/use-api";
import { fetchSignals, fetchSignalSummary } from "@/lib/api";
import { LoadingPage, ErrorState, EmptyState } from "@/components/ui/loading";
import { signalIcon, timeAgo } from "@/lib/utils";
import { SIGNAL_LABELS, type SignalItem, type SignalType } from "@/lib/types";

export default function SignalsPage() {
  const [filterType, setFilterType] = useState("");
  const [page, setPage] = useState(1);

  const { data: summary } = useApi(fetchSignalSummary);

  const { data, loading, error, refetch } = useApi<{
    items: SignalItem[];
    total: number;
    page: number;
    pages: number;
  }>(
    () => fetchSignals({ signal_type: filterType, page, page_size: 30 }),
    [filterType, page]
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Signals</h1>
        <p className="text-sm text-gray-500 mt-1">
          Real-time signal detection across discovered builders
        </p>
      </div>

      {/* Signal type summary cards - backend returns { by_type: { signal_type: count } } */}
      {summary?.by_type && Object.keys(summary.by_type).length > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {Object.entries(summary.by_type as Record<string, number>).map(([signalType, count]) => (
            <button
              key={signalType}
              onClick={() =>
                setFilterType(
                  filterType === signalType ? "" : signalType
                )
              }
              className={`card p-4 text-left transition-all ${
                filterType === signalType
                  ? "ring-2 ring-brand-500 shadow-md"
                  : "hover:shadow-md"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">
                  {signalIcon(signalType)}
                </span>
                <span className="text-xs font-medium text-gray-600">
                  {SIGNAL_LABELS[signalType as SignalType] ||
                    signalType.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{count}</p>
            </button>
          ))}
        </div>
      )}

      {/* Signal list */}
      <div className="card">
        {loading ? (
          <LoadingPage />
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState message="No signals detected yet. Run discovery and scoring to generate signals." />
        ) : (
          <>
            <div className="divide-y divide-gray-100">
              {data.items.map((signal) => (
                <div
                  key={signal.id}
                  className="flex items-start gap-4 p-4 hover:bg-gray-50 transition-colors"
                >
                  <span className="text-2xl mt-0.5">
                    {signalIcon(signal.signal_type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-gray-900 capitalize">
                        {signal.signal_type.replace(/_/g, " ")}
                      </h3>
                      <span className="badge bg-yellow-50 text-yellow-700">
                        {(signal.signal_strength * 100).toFixed(0)}%
                      </span>
                      {signal.is_active && (
                        <span className="badge bg-green-50 text-green-700">
                          Active
                        </span>
                      )}
                    </div>
                    {signal.description && (
                      <p className="text-sm text-gray-600 mt-1">
                        {signal.description}
                      </p>
                    )}
                    {signal.evidence &&
                      Object.keys(signal.evidence).length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {Object.entries(signal.evidence).map(
                            ([key, val]) => (
                              <span
                                key={key}
                                className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                              >
                                {key}: {String(val)}
                              </span>
                            )
                          )}
                        </div>
                      )}
                  </div>
                  <span className="text-xs text-gray-400 shrink-0">
                    {timeAgo(signal.detected_at)}
                  </span>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <p className="text-xs text-gray-500">
                  Page {data.page} of {data.pages} ({data.total} signals)
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-secondary text-xs disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(data.pages, p + 1))
                    }
                    disabled={page >= data.pages}
                    className="btn-secondary text-xs disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
