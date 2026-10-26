/**
 * Date utilities for EventPilot AI.
 * Shows days remaining (not a ticking timer) and parses IST calendar dates.
 */

export function formatFriendlyDate(isoDateStr: string): string {
  try {
    const [year, month, day] = isoDateStr.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  } catch {
    return isoDateStr;
  }
}

export function formatDaysRemaining(daysRemaining: number): { text: string; isPast: boolean; isImminent: boolean } {
  if (daysRemaining < 0) {
    return {
      text: `${Math.abs(daysRemaining)} days ago (Past Event)`,
      isPast: true,
      isImminent: false
    };
  }
  if (daysRemaining === 0) {
    return {
      text: "Today is the event day!",
      isPast: false,
      isImminent: true
    };
  }
  if (daysRemaining === 1) {
    return {
      text: "Tomorrow (1 day remaining)",
      isPast: false,
      isImminent: true
    };
  }
  return {
    text: `${daysRemaining} days remaining`,
    isPast: false,
    isImminent: daysRemaining <= 14
  };
}

export function getTodayIsoDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
