import {
  EventCreateInput,
  EventPlan,
  BudgetItem,
  BudgetCalculationResult,
} from "../repository/types";

export interface RecalculateResponse {
  budget: BudgetCalculationResult;
  changed_items: string[];
}

export class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = ""; // Uses Vite proxy in development; relative root in Cloud Run production

export async function generatePlan(eventInput: EventCreateInput): Promise<EventPlan> {
  const response = await fetch(`${API_BASE}/api/plans/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(eventInput),
  });

  if (!response.ok) {
    let errorDetail = "Failed to generate plan. Please verify inputs.";
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        errorDetail = typeof errorJson.detail === "string"
          ? errorJson.detail
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Keep default error message
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export async function recalculateBudget(payload: {
  total_budget: number;
  guest_count: number;
  previous_guest_count?: number;
  items: BudgetItem[];
}): Promise<RecalculateResponse> {
  const response = await fetch(`${API_BASE}/api/plans/recalculate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorDetail = "Failed to recalculate budget.";
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Use fallback error message
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export async function checkHealth(): Promise<{ status: string; gemini_model: string }> {
  const response = await fetch(`${API_BASE}/healthz`);
  if (!response.ok) {
    throw new ApiError(response.status, "Health check failed");
  }
  return response.json();
}
