import { EventPlan, PlanRepository } from "./types";
import { EventPlanSchema } from "./schema";

const STORAGE_KEY = "eventpilot_active_plan_v1";

export class LocalStoragePlanRepository implements PlanRepository {
  private recoveryError: string | null = null;

  loadCurrentPlan(): EventPlan | null {
    this.recoveryError = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;

      const parsedJson = JSON.parse(raw);
      const validation = EventPlanSchema.safeParse(parsedJson);

      if (!validation.success) {
        console.warn("Stored plan validation failed:", validation.error.format());
        this.recoveryError = "A previously saved plan contained invalid data and was safely recovered. Please create or generate a fresh plan.";
        // Clear corrupted data so application stays healthy
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }

      return validation.data as EventPlan;
    } catch (err) {
      console.warn("Failed to read localStorage plan:", err);
      this.recoveryError = "Could not parse previously saved plan (malformed JSON). The storage has been reset safely.";
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  }

  saveCurrentPlan(plan: EventPlan): void {
    try {
      // Validate before saving to ensure state integrity
      const validation = EventPlanSchema.safeParse(plan);
      if (validation.success) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(validation.data));
        this.recoveryError = null;
      } else {
        console.error("Attempted to save invalid plan schema:", validation.error.format());
      }
    } catch (err) {
      console.error("Failed to write to localStorage:", err);
    }
  }

  clearPlan(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
      this.recoveryError = null;
    } catch (err) {
      console.error("Failed to clear localStorage:", err);
    }
  }

  getRecoveryError(): string | null {
    return this.recoveryError;
  }
}

export const planRepository = new LocalStoragePlanRepository();
