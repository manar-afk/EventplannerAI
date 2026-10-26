/**
 * Currency formatting utilities for Indian Rupees (INR).
 * Follows the Indian numbering system (Lakhs and Crores grouping).
 *
 * NOTE: As per system architecture, the frontend performs ZERO money arithmetic.
 * Arithmetic is handled exclusively by the Python backend budget engine.
 */

export function formatINR(amount: number): string {
  if (isNaN(amount) || !isFinite(amount)) return "₹0";
  // Format as integer rupees using Indian numbering system
  const formatted = Math.round(amount).toLocaleString("en-IN");
  return `₹${formatted}`;
}

export function formatCompactINR(amount: number): string {
  if (isNaN(amount) || !isFinite(amount)) return "₹0";
  const abs = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";

  if (abs >= 10_000_000) {
    // 1 Crore = 100 Lakhs = 10,000,000
    const cr = (abs / 10_000_000).toFixed(2);
    return `${sign}₹${cr} Cr`;
  }
  if (abs >= 100_000) {
    // 1 Lakh = 100,000
    const lakh = (abs / 100_000).toFixed(2);
    return `${sign}₹${lakh} Lakh`;
  }
  return `${sign}₹${Math.round(abs).toLocaleString("en-IN")}`;
}
