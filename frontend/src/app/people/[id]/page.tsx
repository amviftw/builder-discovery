"use client";

import { useParams, useRouter } from "next/navigation";
import { useApi } from "@/hooks/use-api";
import { fetchPerson, updatePerson } from "@/lib/api";
import { LoadingPage, ErrorState } from "@/components/ui/loading";
import { StageBadge } from "@/components/ui/stage-badge";
import { ScoreBar } from "@/components/ui/score-bar";
import { ScoreRadar } from "@/components/charts/score-radar";
import {
  formatScore,
  scoreColor,
  founderFitLabel,
  founderFitColor,
  builderTypeLabel,
  signalIcon,
  timeAgo,
} from "@/lib/utils";
import { PIPELINE_STAGES } from "@/lib/types";
import type { PersonDetail } from "@/lib/types";
import { useState } from "react";

export default function PersonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const personId = params.id as string;

  const { data: person, loading, error, refetch } = useApi<PersonDetail>(
    () => fetchPerson(personId),
    [personId]
  );

  if (loading) return <LoadingPage />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!person) return null;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Back nav */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back
      </button>

      {/* Header */}
      <div className="card p-6 mb-6">
        <div className="flex items-start gap-5">
          {/* Avatar */}
          <div className="w-16 h-16 rounded-xl bg-brand-100 flex items-center justify-center text-brand-700 text-xl font-bold shrink-0">
            {person.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={person.avatar_url}
                alt=""
                className="w-full h-full rounded-xl object-cover"
              />
            ) : (
              person.display_name?.[0]?.toUpperCase() || "?"
            )}
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-gray-900">
                {person.display_name || "Unknown"}
              </h1>
              <StageBadge stage={person.pipeline_stage} />
              {person.founder_fit && (
                <span className={`badge ${founderFitColor(person.founder_fit)}`}>
                  {founderFitLabel(person.founder_fit)}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {person.location || "Unknown location"}
              {person.builder_type && ` · ${builderTypeLabel(person.builder_type)}`}
              {person.builder_experience && ` · ${person.builder_experience.replace(/_/g, " ")}`}
            </p>
            {person.bio && (
              <p className="text-sm text-gray-700 mt-2">{person.bio}</p>
            )}
            {person.one_line_summary && (
              <p className="text-sm text-brand-700 mt-2 italic">
                {person.one_line_summary}
              </p>
            )}

            {/* GitHub links */}
            {person.github_profile && (
              <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                <a
                  href={person.github_profile.profile_url || `https://github.com/${person.github_profile.login}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 hover:text-brand-600"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  @{person.github_profile.login}
                </a>
                <span>{person.github_profile.followers} followers</span>
                <span>{person.github_profile.public_repos} repos</span>
                <span>{person.github_profile.total_stars_received} stars</span>
                {person.github_profile.company && (
                  <span>@ {person.github_profile.company}</span>
                )}
              </div>
            )}
          </div>

          {/* Score */}
          <div className="text-center shrink-0">
            <div
              className={`text-3xl font-bold ${scoreColor(person.founder_propensity_score)}`}
            >
              {formatScore(person.founder_propensity_score)}
            </div>
            <p className="text-xs text-gray-400 mt-1">Propensity Score</p>
          </div>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Score Breakdown */}
        <div className="col-span-4 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Score Breakdown
          </h2>
          <div className="flex justify-center mb-4">
            <ScoreRadar
              technical={person.technical_score || 0}
              momentum={person.momentum_score || 0}
              ai={person.ai_nativeness_score || 0}
              leadership={person.leadership_score || 0}
              departure={person.departure_signal_score || 0}
            />
          </div>
          <div className="space-y-2.5">
            <ScoreBar label="Technical" value={person.technical_score} color="bg-blue-500" />
            <ScoreBar label="Momentum" value={person.momentum_score} color="bg-green-500" />
            <ScoreBar label="AI-nativeness" value={person.ai_nativeness_score} color="bg-purple-500" />
            <ScoreBar label="Leadership" value={person.leadership_score} color="bg-orange-500" />
            <ScoreBar label="Departure Signal" value={person.departure_signal_score} color="bg-red-500" />
          </div>
        </div>

        {/* Signals */}
        <div className="col-span-8 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Active Signals
          </h2>
          {person.signals && person.signals.length > 0 ? (
            <div className="space-y-3">
              {person.signals.map((signal) => (
                <div
                  key={signal.id}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-xl mt-0.5">{signalIcon(signal.signal_type)}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 capitalize">
                        {signal.signal_type.replace(/_/g, " ")}
                      </p>
                      <span className="badge bg-yellow-50 text-yellow-700">
                        {(signal.signal_strength * 100).toFixed(0)}% strength
                      </span>
                    </div>
                    {signal.description && (
                      <p className="text-xs text-gray-600 mt-1">{signal.description}</p>
                    )}
                    <p className="text-[10px] text-gray-400 mt-1">
                      {timeAgo(signal.detected_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-6 text-center">
              No active signals detected for this builder.
            </p>
          )}
        </div>

        {/* Pipeline Stage Manager */}
        <div className="col-span-12 card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Pipeline Stage
          </h2>
          <StageManager personId={person.id} currentStage={person.pipeline_stage} onUpdate={refetch} />
        </div>

        {/* Notes */}
        <div className="col-span-12 card p-5">
          <NotesSection
            personId={person.id}
            notes={person.analyst_notes}
            onUpdate={refetch}
          />
        </div>
      </div>
    </div>
  );
}

function StageManager({
  personId,
  currentStage,
  onUpdate,
}: {
  personId: string;
  currentStage: string;
  onUpdate: () => void;
}) {
  const [updating, setUpdating] = useState(false);
  const currentIdx = PIPELINE_STAGES.indexOf(currentStage as any);

  const advance = async (stage: string) => {
    setUpdating(true);
    try {
      await updatePerson(personId, { pipeline_stage: stage });
      onUpdate();
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STAGES.map((stage, idx) => {
        const isActive = stage === currentStage;
        const isPast = idx < currentIdx;
        const isFuture = idx > currentIdx;

        return (
          <div key={stage} className="flex items-center gap-1 flex-1">
            <button
              onClick={() => advance(stage)}
              disabled={updating || isActive}
              className={`flex-1 py-2 px-2 text-xs font-medium rounded-lg text-center transition-all ${
                isActive
                  ? "bg-brand-600 text-white shadow-sm"
                  : isPast
                  ? "bg-brand-100 text-brand-700 hover:bg-brand-200"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              } ${updating ? "opacity-50" : ""}`}
            >
              {stage.charAt(0).toUpperCase() + stage.slice(1)}
            </button>
            {idx < PIPELINE_STAGES.length - 1 && (
              <svg className="w-3 h-3 text-gray-300 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}

function NotesSection({
  personId,
  notes,
  onUpdate,
}: {
  personId: string;
  notes: string | null;
  onUpdate: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(notes || "");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await updatePerson(personId, { analyst_notes: text });
      setEditing(false);
      onUpdate();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-900">Analyst Notes</h2>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-brand-600 hover:text-brand-700"
          >
            Edit
          </button>
        )}
      </div>
      {editing ? (
        <div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 min-h-[100px]"
            placeholder="Add notes about this builder..."
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={save}
              disabled={saving}
              className="btn-primary text-xs"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setText(notes || "");
              }}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-gray-600">
          {notes || "No notes yet. Click Edit to add observations."}
        </p>
      )}
    </div>
  );
}
