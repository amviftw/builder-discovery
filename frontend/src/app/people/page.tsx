"use client";

import { useState, useCallback, useEffect } from "react";
import { fetchPeople } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { PersonTable } from "@/components/people/person-table";
import { PersonFilters } from "@/components/people/person-filters";
import { LoadingPage, ErrorState, EmptyState } from "@/components/ui/loading";
import type { PersonSummary } from "@/lib/types";

export default function PeoplePage() {
  const [filters, setFilters] = useState({
    search: "",
    pipeline_stage: "",
    builder_type: "",
    founder_fit: "",
    sort_by: "score",
    sort_dir: "desc",
  });
  const [page, setPage] = useState(1);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(filters.search), 300);
    return () => clearTimeout(timer);
  }, [filters.search]);

  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    if (key !== "search") setPage(1);
  }, []);

  const { data, loading, error, refetch } = useApi<{
    items: PersonSummary[];
    total: number;
    page: number;
    pages: number;
  }>(
    () =>
      fetchPeople({
        search: debouncedSearch,
        pipeline_stage: filters.pipeline_stage,
        builder_type: filters.builder_type,
        founder_fit: filters.founder_fit,
        sort_by: filters.sort_by,
        sort_dir: filters.sort_dir,
        page,
        page_size: 25,
      }),
    [debouncedSearch, filters.pipeline_stage, filters.builder_type, filters.founder_fit, filters.sort_by, filters.sort_dir, page]
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Builders</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data ? `${data.total} builders discovered` : "Loading..."}
          </p>
        </div>
        <button
          onClick={() => {
            const blob = new Blob([""], { type: "text/csv" });
            // TODO: implement CSV export
            console.log("Export CSV");
          }}
          className="btn-secondary"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-4">
        <PersonFilters filters={filters} onChange={handleFilterChange} />
      </div>

      {/* Results */}
      <div className="card">
        {loading ? (
          <LoadingPage />
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState message="No builders found. Try adjusting your filters or run the discovery pipeline." />
        ) : (
          <>
            <PersonTable people={data.items} />

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <p className="text-xs text-gray-500">
                  Page {data.page} of {data.pages} ({data.total} total)
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
                    onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
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
