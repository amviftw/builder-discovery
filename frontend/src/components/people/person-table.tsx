"use client";

import Link from "next/link";
import { type PersonSummary } from "@/lib/types";
import {
  formatScore,
  scoreColor,
  founderFitLabel,
  founderFitColor,
  builderTypeLabel,
  stageColor,
} from "@/lib/utils";

interface PersonTableProps {
  people: PersonSummary[];
}

export function PersonTable({ people }: PersonTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Builder
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Stage
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Founder Fit
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Score
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tech
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Momentum
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
              AI
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {people.map((person) => (
            <tr
              key={person.id}
              className="hover:bg-gray-50 transition-colors"
            >
              <td className="py-3 px-4">
                <Link
                  href={`/people/${person.id}`}
                  className="flex items-center gap-3 group"
                >
                  <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xs font-semibold shrink-0">
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
                  <div>
                    <p className="font-medium text-gray-900 group-hover:text-brand-700">
                      {person.display_name || "Unknown"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {person.location || "—"}
                    </p>
                  </div>
                </Link>
              </td>
              <td className="py-3 px-4">
                <span
                  className={`badge capitalize ${stageColor(person.pipeline_stage)}`}
                >
                  {person.pipeline_stage}
                </span>
              </td>
              <td className="py-3 px-4">
                <span className="text-gray-700">
                  {builderTypeLabel(person.builder_type)}
                </span>
              </td>
              <td className="py-3 px-4">
                <span
                  className={`badge ${founderFitColor(person.founder_fit)}`}
                >
                  {founderFitLabel(person.founder_fit)}
                </span>
              </td>
              <td className="py-3 px-4 text-center">
                <span
                  className={`text-sm font-bold ${scoreColor(person.founder_propensity_score)}`}
                >
                  {formatScore(person.founder_propensity_score)}
                </span>
              </td>
              <td className="py-3 px-4 text-center text-gray-600">
                {formatScore(person.technical_score)}
              </td>
              <td className="py-3 px-4 text-center text-gray-600">
                {formatScore(person.momentum_score)}
              </td>
              <td className="py-3 px-4 text-center text-gray-600">
                {formatScore(person.ai_nativeness_score)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
