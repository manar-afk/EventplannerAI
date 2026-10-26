export type EventType = "wedding" | "birthday" | "community";
export type CostBasis = "per_guest" | "fixed";
export type PlanSource = "gemini" | "rule-based-fallback";
export type VendorStatus = "not_contacted" | "contacted" | "quoted" | "booked";

export interface BudgetItem {
  id: string;
  name: string;
  category: string;
  cost_basis: CostBasis;
  estimated_amount: number;
  actual_amount: number | null;
  notes?: string;
}

export interface CategoryBreakdown {
  category: string;
  planned_amount: number;
  actual_amount: number;
  item_count: number;
}

export interface BudgetCalculationResult {
  total_budget: number;
  total_planned: number;
  total_actual: number;
  total_effective: number;
  remaining_budget: number;
  is_over_budget: boolean;
  over_budget_amount: number;
  categories: CategoryBreakdown[];
  items: BudgetItem[];
}

export interface Milestone {
  id: string;
  title: string;
  category: string;
  target_date: string;
  days_before_event: number;
  is_completed: boolean;
  is_overdue: boolean;
  is_at_risk: boolean;
  notes?: string;
}

export interface TimelineResult {
  event_date: string;
  current_ist_date: string;
  days_remaining: number;
  is_past_event: boolean;
  has_overdue_milestones: boolean;
  has_at_risk_milestones: boolean;
  alert_banner: string | null;
  milestones: Milestone[];
}

export interface VendorItem {
  id: string;
  category: string;
  service_name: string;
  estimated_cost: number;
  status: VendorStatus;
  contact_notes?: string;
}

export interface IdeaItem {
  title: string;
  description: string;
  practical_tip?: string;
}

export interface GroupedIdeas {
  decor: IdeaItem[];
  food: IdeaItem[];
  activities: IdeaItem[];
  themes: IdeaItem[];
  logistics: IdeaItem[];
}

export interface EventPlan {
  id: string;
  name: string;
  event_type: EventType;
  event_date: string;
  location: string;
  guest_count: number;
  total_budget: number;
  style: string;
  theme: string;
  special_requirements: string;
  source: PlanSource;
  source_explanation?: string;
  budget: BudgetCalculationResult;
  timeline: TimelineResult;
  vendors: VendorItem[];
  ideas: GroupedIdeas;
  created_at: string;
  updated_at: string;
}

export interface EventCreateInput {
  name: string;
  event_type: EventType;
  event_date: string;
  location: string;
  guest_count: number;
  total_budget: number;
  style: string;
  theme: string;
  special_requirements: string;
}

export interface PlanRepository {
  loadCurrentPlan(): EventPlan | null;
  saveCurrentPlan(plan: EventPlan): void;
  clearPlan(): void;
  getRecoveryError(): string | null;
}
