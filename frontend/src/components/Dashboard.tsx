import React, { useState } from "react";
import {
  EventPlan,
  BudgetItem,
  VendorStatus,
  VendorItem,
} from "../repository/types";
import { formatFriendlyDate, formatDaysRemaining } from "../utils/dates";
import { SourceBadge } from "./SourceBadge";
import { BudgetSection } from "./BudgetSection";
import { TimelineSection } from "./TimelineSection";
import { VendorSection } from "./VendorSection";
import { IdeasSection } from "./IdeasSection";

interface DashboardProps {
  plan: EventPlan;
  isRecalculating: boolean;
  onUpdateBudgetItems: (items: BudgetItem[]) => Promise<void>;
  onToggleMilestone: (id: string) => void;
  onUpdateVendorStatus: (id: string, status: VendorStatus) => void;
  onAddVendor: (vendor: Omit<VendorItem, "id">) => void;
  onUpdateGuestCount: (newGuests: number) => Promise<void>;
  onRegenerate: () => Promise<void>;
  onReset: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  plan,
  isRecalculating,
  onUpdateBudgetItems,
  onToggleMilestone,
  onUpdateVendorStatus,
  onAddVendor,
  onUpdateGuestCount,
  onRegenerate,
  onReset,
}) => {
  const [activeTab, setActiveTab] = useState<"budget" | "timeline" | "vendors" | "ideas">("budget");
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [showEditGuests, setShowEditGuests] = useState(false);
  const [newGuestCountInput, setNewGuestCountInput] = useState(plan.guest_count);

  const countdown = formatDaysRemaining(plan.timeline.days_remaining);

  const handleGuestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newGuestCountInput >= 1 && newGuestCountInput <= 10000) {
      setShowEditGuests(false);
      await onUpdateGuestCount(newGuestCountInput);
    }
  };

  return (
    <div className="space-y-6">
      {/* Event Header Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-orange-100 text-orange-800">
                {plan.event_type}
              </span>
              <SourceBadge source={plan.source} explanation={plan.source_explanation} />
              {countdown.isPast && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                  Past Event
                </span>
              )}
            </div>

            <h1 className="text-2xl md:text-3xl font-extrabold text-stone-900 tracking-tight">
              {plan.name}
            </h1>

            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-stone-600">
              <span className="flex items-center gap-1.5">
                <span>📍</span>
                <span className="font-medium text-stone-800">{plan.location}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span>📅</span>
                <span>{formatFriendlyDate(plan.event_date)}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span>👥</span>
                <span className="font-semibold text-stone-800">{plan.guest_count.toLocaleString("en-IN")} Guests</span>
                <button
                  onClick={() => {
                    setNewGuestCountInput(plan.guest_count);
                    setShowEditGuests(true);
                  }}
                  className="text-xs text-orange-600 hover:text-orange-800 font-semibold underline ml-1"
                >
                  Edit
                </button>
              </span>
              {plan.theme && (
                <span className="flex items-center gap-1.5">
                  <span>🎨</span>
                  <span>{plan.theme}</span>
                </span>
              )}
            </div>
          </div>

          {/* Days Remaining & Actions */}
          <div className="flex flex-col items-start md:items-end gap-3 self-stretch md:self-auto border-t md:border-t-0 pt-4 md:pt-0">
            <div className={`px-4 py-2 rounded-xl text-center border ${
              countdown.isPast
                ? "bg-red-50 border-red-200 text-red-900"
                : countdown.isImminent
                ? "bg-amber-50 border-amber-200 text-amber-900 font-bold"
                : "bg-stone-50 border-stone-200 text-stone-800 font-semibold"
            }`}>
              <p className="text-xs uppercase tracking-wider opacity-75 font-medium">Event Horizon</p>
              <p className="text-sm md:text-base mt-0.5">{countdown.text}</p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowRegenerateConfirm(true)}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-xl border border-stone-300 text-stone-700 hover:bg-stone-50 transition-colors"
                title="Regenerate plan with Gemini (requires confirmation)"
              >
                🔄 Regenerate
              </button>
              <button
                onClick={onReset}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-xl border border-stone-200 text-stone-500 hover:text-stone-800 hover:bg-stone-50 transition-colors"
                title="Start a new event plan"
              >
                + New Event
              </button>
            </div>
          </div>
        </div>

        {/* Requirements snippet if present */}
        {plan.special_requirements && (
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs text-stone-600 flex items-start gap-2 bg-stone-50/50 p-2.5 rounded-lg">
            <span className="font-semibold text-stone-700 shrink-0">Special Requirements:</span>
            <span>{plan.special_requirements}</span>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-stone-200 space-x-2 sm:space-x-4">
        {[
          { key: "budget", label: "Budget & Items", icon: "💰" },
          { key: "timeline", label: "Timeline Milestones", icon: "📅" },
          { key: "vendors", label: "Vendor Checklist", icon: "🤝" },
          { key: "ideas", label: "Ideas & Themes", icon: "💡" },
        ].map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 py-3 px-3 sm:px-5 font-semibold text-sm border-b-2 transition-all ${
                isActive
                  ? "border-orange-600 text-orange-600 bg-white rounded-t-xl"
                  : "border-transparent text-stone-500 hover:text-stone-800"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Tab Content */}
      <div>
        {activeTab === "budget" && (
          <BudgetSection
            budget={plan.budget}
            isRecalculating={isRecalculating}
            onUpdateItems={onUpdateBudgetItems}
          />
        )}

        {activeTab === "timeline" && (
          <TimelineSection
            timeline={plan.timeline}
            onToggleMilestone={onToggleMilestone}
          />
        )}

        {activeTab === "vendors" && (
          <VendorSection
            vendors={plan.vendors}
            onUpdateVendorStatus={onUpdateVendorStatus}
            onAddVendor={onAddVendor}
          />
        )}

        {activeTab === "ideas" && (
          <IdeasSection ideas={plan.ideas} />
        )}
      </div>

      {/* Guest Count Edit Modal */}
      {showEditGuests && (
        <div className="fixed inset-0 bg-stone-900/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 space-y-4">
            <h3 className="text-lg font-bold text-stone-900">Update Guest Count</h3>
            <p className="text-xs text-stone-600">
              Per architectural invariant, modifying guest count will recalculate <strong>only per-guest budget items</strong> (e.g. catering, invitations, return favors). Fixed costs (venue, decor, DJ) remain untouched.
            </p>
            <form onSubmit={handleGuestSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  New Guest Count (1 – 10,000)
                </label>
                <input
                  type="number"
                  min={1}
                  max={10000}
                  required
                  value={newGuestCountInput}
                  onChange={(e) => setNewGuestCountInput(Number(e.target.value))}
                  className="w-full px-3 py-2 border rounded-xl font-mono text-stone-800 focus:ring-2 focus:ring-orange-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditGuests(false)}
                  className="px-4 py-2 text-xs font-semibold text-stone-600 hover:text-stone-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRecalculating}
                  className="px-5 py-2 text-xs font-semibold bg-orange-600 hover:bg-orange-700 text-white rounded-xl shadow-sm"
                >
                  Apply & Recalculate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Regeneration */}
      {showRegenerateConfirm && (
        <div className="fixed inset-0 bg-stone-900/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200 space-y-4">
            <h3 className="text-lg font-bold text-stone-900">Regenerate Event Plan?</h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              This will request a fresh planning proposal from the model based on your event inputs. Any customized edits you made to budget line items or actuals will be replaced.
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowRegenerateConfirm(false)}
                className="px-4 py-2 text-xs font-semibold text-stone-600 hover:text-stone-900"
              >
                Keep Current Plan
              </button>
              <button
                type="button"
                onClick={async () => {
                  setShowRegenerateConfirm(false);
                  await onRegenerate();
                }}
                className="px-5 py-2 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white rounded-xl shadow-sm"
              >
                Confirm & Regenerate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
