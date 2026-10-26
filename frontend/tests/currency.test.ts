import { describe, it, expect } from "vitest";
import { formatINR, formatCompactINR } from "../src/utils/currency";

describe("Indian Rupee (INR) Currency Utilities", () => {
  it("formats integer amounts with standard Indian Lakh grouping", () => {
    expect(formatINR(1000)).toBe("₹1,000");
    expect(formatINR(50000)).toBe("₹50,000");
    expect(formatINR(100000)).toBe("₹1,00,000");
    expect(formatINR(1500000)).toBe("₹15,00,000");
    expect(formatINR(10000000)).toBe("₹1,00,00,000");
  });

  it("handles negative and zero values cleanly", () => {
    expect(formatINR(0)).toBe("₹0");
    expect(formatINR(-50000)).toBe("₹-50,000");
  });

  it("formats compact denominations in Lakhs and Crores", () => {
    expect(formatCompactINR(500000)).toBe("₹5.00 Lakh");
    expect(formatCompactINR(2500000)).toBe("₹25.00 Lakh");
    expect(formatCompactINR(15000000)).toBe("₹1.50 Cr");
  });
});
