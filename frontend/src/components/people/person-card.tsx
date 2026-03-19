"use client";

import Link from "next/link";
import { type PersonSummary } from "@/lib/types";
import {
  formatScore,
  scoreColor,
  founderFitLabel,
  founderFitColor,
  builderTypeLabel,
} from "@/lib/utils";
import { StageBadge } from "@/components/ui/stage-badge";
import { ScoreBar } from "@/components/ui/score-bar";

interface PersonCardProps {
  person: PersonSummary;
  compact?: boolean;
}

export function PersonCard({ person, compact = false }: PersonCardProps) {
  if (compact) {
    return (
      <Link
        href={`/people/${person.id}`}
        className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xs font-semibold shrink-0">
          {person.display_name?.[0]?.toUpperCase() || "?"}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {person.display_name || "Unknown"}
          </p>
          <p className="text-xs text-gray-500 truncate">{person.location || "—"}</p>
        </div>
        <span className={`text-sm font-semibold ${scoreColor(person.founder_propensity_score)}`}>
          {formatScore(person.founder_propensity_score)}
        </span>
      </Link>
    );
  }

  return (
    <Link
      href={`/people/${person.id}`}
      className="card p-4 hover:shadow-md transition-shadow block"
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-sm font-semibold shrink-0">
          {person.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={person.avatar_url}
              alt=""
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            person.display_name?.[0]?.toUpperCase() || "?"
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900 truncate">
              {person.display_name || "Unknown"}
            </h3>
            <StageBadge stage={person.pipeline_stage} />
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {person.location || "Unknown location"}
          </p>

          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-2">
            {person.builder_type && (
              <span className="badge bg-blue-50 text-blue-700">
                {builderTypeLabel(person.builder_type)}
              </span>
            )}
            {person.founder_fit && (
              <span className={`badge ${founderFitColor(person.founder_fit)}`}>
                {founderFitLabel(person.founder_fit)}
              </span>
            )}
          </div>
        </div>

        {/* Score */}
        <div className="text-right shrink-0">
          <div
            className={`text-lg font-bold ${scoreColor(person.founder_propensity_score)}`}
          >
            {formatScore(person.founder_propensity_score)}
          </div>
          <p className="text-[10px] text-gray-400">propensity</p>
        </div>
      </div>

      {/* Score bars */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mt-3 pt-3 border-t border-gray-100">
        <ScoreBar label="Technical" value={person.technical_score} color="bg-blue-500" />
        <ScoreBar label="Momentum" value={person.momentum_score} color="bg-green-500" />
        <ScoreBar label="AI-native" value={person.ai_nativeness_score} color="bg-purple-500" />
        <ScoreBar label="Leadership" value={person.leadership_score} color="bg-orange-500" />
      </div>
    </Link>
  );
}
