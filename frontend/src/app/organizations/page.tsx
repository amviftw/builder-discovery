"use client";

import { useApi } from "@/hooks/use-api";
import { fetchOrganizations } from "@/lib/api";
import { LoadingPage, ErrorState, EmptyState } from "@/components/ui/loading";
import type { Organization } from "@/lib/types";

export default function OrganizationsPage() {
  const { data, loading, error, refetch } = useApi<{
    items: Organization[];
    total: number;
  }>(fetchOrganizations);

  if (loading) return <LoadingPage />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data || data.items.length === 0) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Organizations</h1>
        <EmptyState message="No organizations tracked yet. Seed the database to get started." />
      </div>
    );
  }

  const grouped = {
    big_tech: data.items.filter((o) => o.company_type === "big_tech"),
    unicorn: data.items.filter((o) => o.company_type === "unicorn"),
    startup: data.items.filter((o) => o.company_type === "startup"),
    other: data.items.filter(
      (o) => !["big_tech", "unicorn", "startup"].includes(o.company_type || "")
    ),
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data.total} tracked companies for builder discovery
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <OrgCountCard label="Big Tech" count={grouped.big_tech.length} color="bg-blue-500" />
        <OrgCountCard label="Unicorns" count={grouped.unicorn.length} color="bg-purple-500" />
        <OrgCountCard label="Startups" count={grouped.startup.length} color="bg-green-500" />
        <OrgCountCard label="Total" count={data.total} color="bg-gray-500" />
      </div>

      {/* Org groups */}
      {Object.entries(grouped).map(([type, orgs]) => {
        if (orgs.length === 0) return null;
        const label =
          type === "big_tech"
            ? "Big Tech / Public"
            : type === "unicorn"
            ? "Unicorns"
            : type === "startup"
            ? "Startups"
            : "Other";
        return (
          <div key={type} className="mb-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">
              {label}
            </h2>
            <div className="grid grid-cols-3 gap-3">
              {orgs.map((org) => (
                <div key={org.id} className="card p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500 text-sm font-bold">
                      {org.name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900 truncate">
                        {org.name}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {org.location || "India"}
                      </p>
                    </div>
                    {org.is_tracked && (
                      <span className="badge bg-green-50 text-green-700">
                        Tracked
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
                    <a
                      href={`https://github.com/${org.github_org_login}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-brand-600"
                    >
                      github.com/{org.github_org_login}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function OrgCountCard({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-2.5 h-2.5 rounded-full ${color}`} />
        <p className="text-xs text-gray-500">{label}</p>
      </div>
      <p className="text-2xl font-bold text-gray-900">{count}</p>
    </div>
  );
}
