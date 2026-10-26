import React from "react";
import { TimelineResult, Milestone } from "../repository/types";
import { formatFriendlyDate } from "../utils/dates";

interface TimelineSectionProps {
  timeline: TimelineResult;
  onToggleMilestone: (id: string) => void;
}

export const TimelineSection: React.FC<TimelineSectionProps> = ({
  timeline,
  onToggleMilestone,
}) => {
  const completedCount = timeline.milestones.filter((m) => m.is_completed).length;
  const totalCount = timeline.milestones.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-100 pb-4">
        <div>
          <h2 className="text-xl font-bold text-stone-900">Milestone Timeline (IST)</h2>
          <p className="text-xs text-stone-500 mt-0.5">
            Key planning milestones scheduled backwards from your event date. Dates are strictly computed and never moved silently.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs font-semibold text-stone-600">
              {completedCount} of {totalCount} Completed
            </span>
            <div className="w-28 bg-stone-200 h-2 rounded-full overflow-hidden mt-1">
              <div
                className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Banner for Overdue / Imminent / Past Event */}
      {timeline.alert_banner && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 shadow-sm ${
            timeline.is_past_event
              ? "bg-red-50 border-red-200 text-red-900"
              : timeline.has_overdue_milestones
              ? "bg-amber-50 border-amber-200 text-amber-900"
              : "bg-blue-50 border-blue-200 text-blue-900"
          }`}
          role="alert"
        >
          <span className="text-lg">
            {timeline.is_past_event ? "🛑" : timeline.has_overdue_milestones ? "⚠️" : "ℹ️"}
          </span>
          <div>
            <p className="font-semibold text-sm">
              {timeline.is_past_event
                ? "Past Event Notice"
                : timeline.has_overdue_milestones
                ? "Schedule Risk: Overdue Milestones"
                : "Milestone Notice"}
            </p>
            <p className="text-xs mt-0.5 opacity-90">{timeline.alert_banner}</p>
          </div>
        </div>
      )}

      {/* Milestone List */}
      <div className="space-y-3">
        {timeline.milestones.map((ms: Milestone) => {
          return (
            <div
              key={ms.id}
              className={`p-4 rounded-xl border transition-all flex items-start gap-4 ${
                ms.is_completed
                  ? "bg-stone-50/70 border-stone-200 opacity-70"
                  : ms.is_overdue
                  ? "bg-red-50/40 border-red-200"
                  : ms.is_at_risk
                  ? "bg-amber-50/40 border-amber-200"
                  : "bg-white border-stone-200 hover:border-orange-300"
              }`}
            >
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={ms.is_completed}
                onChange={() => onToggleMilestone(ms.id)}
                className="mt-1 h-5 w-5 rounded border-stone-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
                aria-label={`Mark milestone ${ms.title} as completed`}
              />

              {/* Details */}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h4
                    className={`font-semibold text-sm ${
                      ms.is_completed ? "line-through text-stone-500" : "text-stone-900"
                    }`}
                  >
                    {ms.title}
                  </h4>

                  {/* Status Badges */}
                  {ms.is_completed ? (
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                      Completed
                    </span>
                  ) : ms.is_overdue ? (
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">
                      Overdue
                    </span>
                  ) : ms.is_at_risk ? (
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
                      At Risk
                    </span>
                  ) : null}

                  <span className="px-2 py-0.5 rounded text-xs bg-stone-100 text-stone-600">
                    {ms.category}
                  </span>
                </div>

                <div className="flex items-center gap-4 mt-1 text-xs text-stone-500">
                  <span>Target: {formatFriendlyDate(ms.target_date)}</span>
                  <span>({ms.days_before_event} days before event)</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
