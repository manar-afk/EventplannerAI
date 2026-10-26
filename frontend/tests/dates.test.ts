import { describe, it, expect } from "vitest";
import { formatDaysRemaining, formatFriendlyDate } from "../src/utils/dates";

describe("Date and Days Remaining Utilities", () => {
  it("formats positive days remaining as days to go (not a ticking timer)", () => {
    const res = formatDaysRemaining(45);
    expect(res.text).toBe("45 days remaining");
    expect(res.isPast).toBe(false);
    expect(res.isImminent).toBe(false);
  });

  it("marks events within 14 days as imminent", () => {
    const res = formatDaysRemaining(7);
    expect(res.text).toBe("7 days remaining");
    expect(res.isPast).toBe(false);
    expect(res.isImminent).toBe(true);
  });

  it("flags past event dates explicitly", () => {
    const res = formatDaysRemaining(-10);
    expect(res.text).toContain("10 days ago (Past Event)");
    expect(res.isPast).toBe(true);
  });

  it("formats ISO date string into Indian friendly date", () => {
    expect(formatFriendlyDate("2026-12-25")).toContain("Dec");
    expect(formatFriendlyDate("2026-12-25")).toContain("2026");
  });
});
