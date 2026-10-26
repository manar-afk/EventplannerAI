import { useState, useEffect } from "react";
import {
  EventCreateInput,
  EventPlan,
  BudgetItem,
  VendorStatus,
  VendorItem,
} from "./repository/types";
import { planRepository } from "./repository/localStorageRepo";
import { generatePlan, recalculateBudget, recalculateTimeline } from "./api/client";
import { EventForm } from "./components/EventForm";
import { Dashboard } from "./components/Dashboard";
import { ErrorNotice } from "./components/ErrorNotice";

export function App() {
  const [currentPlan, setCurrentPlan] = useState<EventPlan | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRecalculating, setIsRecalculating] = useState<boolean>(false);
  const [reviewItems, setReviewItems] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recoveryNotice, setRecoveryNotice] = useState<string | null>(null);

  // 1. Initial Load: Read from LocalStoragePlanRepository & refresh timeline flags
  useEffect(() => {
    const saved = planRepository.loadCurrentPlan();
    if (saved) {
      setCurrentPlan(saved);
      // Refresh timeline flags against current IST date while preserving task completion
      const completedIds = saved.timeline.milestones
        .filter((m) => m.is_completed)
        .map((m) => m.id);

      recalculateTimeline({
        event_date: saved.event_date,
        event_type: saved.event_type,
        completed_ids: completedIds,
      })
        .then((refreshedTimeline) => {
          setCurrentPlan((prev) => {
            if (!prev) return null;
            const updated = { ...prev, timeline: refreshedTimeline };
            planRepository.saveCurrentPlan(updated);
            return updated;
          });
        })
        .catch((err) => {
          console.warn("Could not refresh timeline flags on initial load:", err);
        });
    }

    const recoveryErr = planRepository.getRecoveryError();
    if (recoveryErr) {
      setRecoveryNotice(recoveryErr);
    }
  }, []);

  // 2. Create event -> generate plan
  const handleCreatePlan = async (input: EventCreateInput) => {
    setIsLoading(true);
    setErrorMessage(null);
    setRecoveryNotice(null);
    setReviewItems([]);

    try {
      const plan = await generatePlan(input);
      setCurrentPlan(plan);
      planRepository.saveCurrentPlan(plan);
    } catch (err: any) {
      setErrorMessage(err.message || "An error occurred while generating the plan.");
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Edit budget item -> recalculate via backend
  const handleUpdateBudgetItems = async (newItems: BudgetItem[]) => {
    if (!currentPlan) return;

    setIsRecalculating(true);
    setErrorMessage(null);

    try {
      const resp = await recalculateBudget({
        total_budget: currentPlan.total_budget,
        guest_count: currentPlan.guest_count,
        items: newItems,
      });

      const updatedPlan: EventPlan = {
        ...currentPlan,
        budget: resp.budget,
        updated_at: new Date().toISOString(),
      };

      setCurrentPlan(updatedPlan);
      planRepository.saveCurrentPlan(updatedPlan);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to recalculate budget.");
    } finally {
      setIsRecalculating(false);
    }
  };

  // 4. Milestone completion toggle (persisted and survives reloads)
  const handleToggleMilestone = (id: string) => {
    if (!currentPlan) return;

    const updatedMilestones = currentPlan.timeline.milestones.map((ms) => {
      if (ms.id === id) {
        const nextCompleted = !ms.is_completed;
        return {
          ...ms,
          is_completed: nextCompleted,
          is_overdue: nextCompleted ? false : ms.is_overdue,
          is_at_risk: nextCompleted ? false : ms.is_at_risk,
        };
      }
      return ms;
    });

    const updatedPlan: EventPlan = {
      ...currentPlan,
      timeline: {
        ...currentPlan.timeline,
        milestones: updatedMilestones,
      },
      updated_at: new Date().toISOString(),
    };

    setCurrentPlan(updatedPlan);
    planRepository.saveCurrentPlan(updatedPlan);
  };

  // 5. Vendor status update
  const handleUpdateVendorStatus = (id: string, newStatus: VendorStatus) => {
    if (!currentPlan) return;

    const updatedVendors = currentPlan.vendors.map((v) => {
      if (v.id === id) {
        return { ...v, status: newStatus };
      }
      return v;
    });

    const updatedPlan: EventPlan = {
      ...currentPlan,
      vendors: updatedVendors,
      updated_at: new Date().toISOString(),
    };

    setCurrentPlan(updatedPlan);
    planRepository.saveCurrentPlan(updatedPlan);
  };

  // 6. Add vendor
  const handleAddVendor = (vendorData: Omit<VendorItem, "id">) => {
    if (!currentPlan) return;

    const newVendor: VendorItem = {
      id: `v-usr-${Date.now()}`,
      ...vendorData,
    };

    const updatedPlan: EventPlan = {
      ...currentPlan,
      vendors: [...currentPlan.vendors, newVendor],
      updated_at: new Date().toISOString(),
    };

    setCurrentPlan(updatedPlan);
    planRepository.saveCurrentPlan(updatedPlan);
  };

  // 7. Update guest count -> per-guest items scale, actuals preserved for review
  const handleUpdateGuestCount = async (newGuests: number) => {
    if (!currentPlan) return;

    setIsRecalculating(true);
    setErrorMessage(null);

    try {
      const resp = await recalculateBudget({
        total_budget: currentPlan.total_budget,
        guest_count: newGuests,
        previous_guest_count: currentPlan.guest_count,
        items: currentPlan.budget.items,
      });

      if (resp.review_items && resp.review_items.length > 0) {
        setReviewItems(resp.review_items);
      } else {
        setReviewItems([]);
      }

      const updatedPlan: EventPlan = {
        ...currentPlan,
        guest_count: newGuests,
        budget: resp.budget,
        updated_at: new Date().toISOString(),
      };

      setCurrentPlan(updatedPlan);
      planRepository.saveCurrentPlan(updatedPlan);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update guest count.");
    } finally {
      setIsRecalculating(false);
    }
  };

  // 8. Regenerate plan
  const handleRegenerate = async () => {
    if (!currentPlan) return;
    await handleCreatePlan({
      name: currentPlan.name,
      event_type: currentPlan.event_type,
      event_date: currentPlan.event_date,
      location: currentPlan.location,
      guest_count: currentPlan.guest_count,
      total_budget: currentPlan.total_budget,
      style: currentPlan.style,
      theme: currentPlan.theme,
      special_requirements: currentPlan.special_requirements,
    });
  };

  // 9. Reset
  const handleReset = () => {
    planRepository.clearPlan();
    setCurrentPlan(null);
    setErrorMessage(null);
    setRecoveryNotice(null);
    setReviewItems([]);
  };

  return (
    <div className="min-h-screen bg-stone-100/60 pb-16">
      <header className="bg-white border-b border-stone-200 sticky top-0 z-40 backdrop-blur-md bg-white/90">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-sm font-bold text-lg">
              ✨
            </div>
            <div>
              <span className="font-extrabold text-stone-900 tracking-tight text-lg">EventPilot</span>
              <span className="text-orange-600 font-extrabold ml-1 text-lg">AI</span>
              <span className="hidden sm:inline-block ml-2 text-xs bg-orange-100 text-orange-800 font-semibold px-2 py-0.5 rounded-full">
                Indian Events & Weddings
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium text-stone-500">
            <span className="hidden md:inline">Timezone: Asia/Kolkata (IST)</span>
            {currentPlan && (
              <button
                onClick={handleReset}
                className="text-stone-600 hover:text-stone-900 font-semibold"
              >
                + New Event
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
        {recoveryNotice && (
          <ErrorNotice
            title="Storage Recovery Notice"
            message={recoveryNotice}
            type="warning"
            onDismiss={() => setRecoveryNotice(null)}
          />
        )}

        {errorMessage && (
          <ErrorNotice
            title="Operation Failed"
            message={errorMessage}
            type="error"
            onDismiss={() => setErrorMessage(null)}
          />
        )}

        {!currentPlan ? (
          <div className="max-w-3xl mx-auto pt-4">
            <EventForm onSubmit={handleCreatePlan} isLoading={isLoading} />
          </div>
        ) : (
          <Dashboard
            plan={currentPlan}
            isRecalculating={isRecalculating}
            reviewItems={reviewItems}
            onUpdateBudgetItems={handleUpdateBudgetItems}
            onToggleMilestone={handleToggleMilestone}
            onUpdateVendorStatus={handleUpdateVendorStatus}
            onAddVendor={handleAddVendor}
            onUpdateGuestCount={handleUpdateGuestCount}
            onRegenerate={handleRegenerate}
            onReset={handleReset}
          />
        )}
      </main>
    </div>
  );
}

export default App;
