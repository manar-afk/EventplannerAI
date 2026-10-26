import { z } from "zod";

export const BudgetItemSchema = z.object({
  id: z.string().max(64),
  name: z.string().min(1).max(100),
  category: z.string().min(1).max(50),
  cost_basis: z.enum(["per_guest", "fixed"]),
  estimated_amount: z.number().int().nonnegative(),
  actual_amount: z.number().int().nonnegative().nullable(),
  notes: z.string().max(300).optional().default(""),
});

export const CategoryBreakdownSchema = z.object({
  category: z.string(),
  planned_amount: z.number().int().nonnegative(),
  actual_amount: z.number().int().nonnegative(),
  effective_amount: z.number().int().nonnegative().default(0),
  item_count: z.number().int().nonnegative(),
});

export const BudgetCalculationResultSchema = z.object({
  total_budget: z.number().int().positive(),
  total_planned: z.number().int().nonnegative(),
  total_actual: z.number().int().nonnegative(),
  total_effective: z.number().int().nonnegative(),
  remaining_budget: z.number().int(),
  is_over_budget: z.boolean(),
  over_budget_amount: z.number().int().nonnegative(),
  categories: z.array(CategoryBreakdownSchema),
  items: z.array(BudgetItemSchema),
});

export const MilestoneSchema = z.object({
  id: z.string().max(64),
  title: z.string().min(1).max(120),
  category: z.string().min(1).max(50),
  target_date: z.string(),
  days_before_event: z.number().int(),
  is_completed: z.boolean().default(false),
  is_overdue: z.boolean().default(false),
  is_at_risk: z.boolean().default(false),
  notes: z.string().max(300).optional().default(""),
});

export const TimelineResultSchema = z.object({
  event_date: z.string(),
  current_ist_date: z.string(),
  days_remaining: z.number().int(),
  is_past_event: z.boolean(),
  has_overdue_milestones: z.boolean(),
  has_at_risk_milestones: z.boolean(),
  alert_banner: z.string().nullable(),
  milestones: z.array(MilestoneSchema),
});

export const VendorItemSchema = z.object({
  id: z.string().max(64),
  budget_item_id: z.string().max(64).nullable().optional(),
  category: z.string().min(1).max(50),
  service_name: z.string().min(1).max(100),
  estimated_cost: z.number().int().nonnegative(),
  status: z.enum(["not_contacted", "contacted", "quoted", "booked"]),
  contact_notes: z.string().max(300).optional().default(""),
});

export const IdeaItemSchema = z.object({
  title: z.string().min(1).max(100),
  description: z.string().min(1).max(500),
  practical_tip: z.string().max(300).optional().default(""),
});

export const GroupedIdeasSchema = z.object({
  decor: z.array(IdeaItemSchema).default([]),
  food: z.array(IdeaItemSchema).default([]),
  activities: z.array(IdeaItemSchema).default([]),
  themes: z.array(IdeaItemSchema).default([]),
  logistics: z.array(IdeaItemSchema).default([]),
});

export const EventPlanSchema = z.object({
  id: z.string().max(64),
  name: z.string().min(1).max(100),
  event_type: z.enum(["wedding", "birthday", "community"]),
  event_date: z.string(),
  location: z.string().min(1).max(120),
  guest_count: z.number().int().min(1).max(10000),
  total_budget: z.number().int().positive(),
  style: z.string().max(100),
  theme: z.string().max(100),
  special_requirements: z.string().max(500),
  source: z.enum(["gemini", "rule-based-fallback"]),
  source_explanation: z.string().max(300).optional(),
  budget: BudgetCalculationResultSchema,
  timeline: TimelineResultSchema,
  vendors: z.array(VendorItemSchema),
  ideas: GroupedIdeasSchema,
  created_at: z.string(),
  updated_at: z.string(),
});
