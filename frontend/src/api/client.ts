import {
  EventCreateInput,
  EventPlan,
  BudgetItem,
  BudgetCalculationResult,
  TimelineResult,
  EventType,
} from "../repository/types";

export interface RecalculateResponse {
  budget: BudgetCalculationResult;
  changed_items: string[];
  review_items: string[];
}

export class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = "";
const REQUEST_TIMEOUT_MS = 45_000; // 45 seconds timeout

async function fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new ApiError(408, "Request timed out after 45 seconds. The server may still be processing.");
    }
    throw err;
  } finally {
    clearTimeout(id);
  }
}

export async function generatePlan(eventInput: EventCreateInput): Promise<EventPlan> {
  const response = await fetchWithTimeout(`${API_BASE}/api/plans/generate`, {
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
      // Keep default
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
  const response = await fetchWithTimeout(`${API_BASE}/api/plans/recalculate`, {
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
      // Keep default
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export async function recalculateTimeline(payload: {
  event_date: string;
  event_type: EventType;
  completed_ids: string[];
}): Promise<TimelineResult> {
  const response = await fetchWithTimeout(`${API_BASE}/api/plans/timeline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorDetail = "Failed to update timeline.";
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Keep default
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetchWithTimeout(`${API_BASE}/healthz`, { method: "GET" });
  if (!response.ok) {
    throw new ApiError(response.status, "Health check failed");
  }
  return response.json();
}
