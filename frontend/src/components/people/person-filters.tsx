"use client";

import { PIPELINE_STAGES } from "@/lib/types";

interface FiltersProps {
  filters: {
    search: string;
    pipeline_stage: string;
    builder_type: string;
    founder_fit: string;
    sort_by: string;
    sort_dir: string;
  };
  onChange: (key: string, value: string) => void;
}

export function PersonFilters({ filters, onChange }: FiltersProps) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Search builders..."
          value={filters.search}
          onChange={(e) => onChange("search", e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      {/* Stage filter */}
      <select
        value={filters.pipeline_stage}
        onChange={(e) => onChange("pipeline_stage", e.target.value)}
        className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <option value="">All stages</option>
        {PIPELINE_STAGES.map((s) => (
          <option key={s} value={s}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </option>
        ))}
      </select>

      {/* Builder Type */}
      <select
        value={filters.builder_type}
        onChange={(e) => onChange("builder_type", e.target.value)}
        className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <option value="">All types</option>
        <option value="generalist">Generalist</option>
        <option value="product_leader">Product Leader</option>
        <option value="engineer">Engineer</option>
      </select>

      {/* Founder Fit */}
      <select
        value={filters.founder_fit}
        onChange={(e) => onChange("founder_fit", e.target.value)}
        className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <option value="">All fit levels</option>
        <option value="good_builder_good_founder">Strong Founder Fit</option>
        <option value="good_builder_not_founder">Builder (Not Founder)</option>
        <option value="okay_builder">Okay Builder</option>
      </select>

      {/* Sort */}
      <select
        value={`${filters.sort_by}:${filters.sort_dir}`}
        onChange={(e) => {
          const [by, dir] = e.target.value.split(":");
          onChange("sort_by", by);
          onChange("sort_dir", dir);
        }}
        className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <option value="score:desc">Score (High first)</option>
        <option value="score:asc">Score (Low first)</option>
        <option value="recent:desc">Newest first</option>
        <option value="recent:asc">Oldest first</option>
        <option value="name:asc">Name A-Z</option>
        <option value="name:desc">Name Z-A</option>
        <option value="momentum:desc">Momentum (High)</option>
      </select>
    </div>
  );
}
