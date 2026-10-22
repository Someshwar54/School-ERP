import { describe, expect, it } from "vitest";
import { countByStatus, shiftMonth, unmarkedCount, weekdayIndex } from "./attendance";
import { assessmentState } from "./status";
import {
  hasErrors,
  invalidMarks,
  validateComplaint,
  validateEnquiry,
  validateLeave,
  validateLogin,
  validatePasswordChange,
  validatePaymentAmount,
  validateReason,
} from "./validation";

describe("validation", () => {
  it("validates sign-in input", () => {
    expect(validateLogin({ loginId: "", password: "" }, "Student ID")).toEqual({
      loginId: "Enter your Student ID.",
      password: "Enter your password.",
    });
    expect(validateLogin({ loginId: "x' OR 1=1", password: "p" }, "Staff ID").loginId).toMatch(/letters, numbers/);
    expect(hasErrors(validateLogin({ loginId: " STU0181 ", password: "p" }, "Student ID"))).toBe(false);
  });

  it("validates enquiries like the backend", () => {
    const e = validateEnquiry({ parent_name: "A", email: "nope", phone: "12345", grade_sought: "" });
    expect(Object.keys(e).sort()).toEqual(["email", "grade_sought", "parent_name", "phone"]);
    expect(hasErrors(validateEnquiry({ parent_name: "Asha", email: "a@b.in", phone: "9876543210", grade_sought: "Grade 7" }))).toBe(false);
  });

  it("enforces the password policy", () => {
    expect(validatePasswordChange({ current: "x", next: "short1", confirm: "short1" }).next).toMatch(/10 characters/);
    expect(validatePasswordChange({ current: "x", next: "onlyletters", confirm: "onlyletters" }).next).toMatch(/letters and numbers/);
    expect(validatePasswordChange({ current: "x", next: "Better2026x", confirm: "Better2026y" }).confirm).toBeDefined();
    expect(hasErrors(validatePasswordChange({ current: "x", next: "Better2026x", confirm: "Better2026x" }))).toBe(false);
  });

  it("checks leave date order and complaint lengths", () => {
    expect(validateLeave({ starts_on: "2026-11-05", ends_on: "2026-11-04", reason: "Trip" }).ends_on).toBeDefined();
    expect(validateComplaint({ category: "", subject: "Hi", description: "short" })).toHaveProperty("description");
  });

  it("flags out-of-range marks but allows blanks", () => {
    expect(invalidMarks({ a: "10", b: "", c: "-1", d: "26", e: "abc" }, 25).sort()).toEqual(["c", "d", "e"]);
  });

  it("caps payments at the outstanding balance", () => {
    expect(validatePaymentAmount("100.00", "100.00")).toBeNull();
    expect(validatePaymentAmount("100.01", "100.00")).not.toBeNull();
    expect(validatePaymentAmount("0", "100.00")).not.toBeNull();
  });

  it("requires a correction reason of 5+ characters", () => {
    expect(validateReason("oops")).not.toBeNull();
    expect(validateReason("Marked wrongly")).toBeNull();
  });
});

describe("attendance rules", () => {
  it("counts statuses and unmarked students", () => {
    const marks = { s1: "present", s2: "absent", s3: null, s4: "present" } as const;
    expect(countByStatus({ ...marks }).present).toBe(2);
    expect(unmarkedCount({ ...marks })).toBe(1);
  });

  it("shifts months across year boundaries", () => {
    expect(shiftMonth("2026-12", 1)).toBe("2027-01");
    expect(shiftMonth("2026-01", -1)).toBe("2025-12");
  });

  it("uses Monday-first weekdays like the backend", () => {
    expect(weekdayIndex("2026-10-19")).toBe(0); // Monday
    expect(weekdayIndex("2026-10-25")).toBe(6); // Sunday
  });
});

describe("status mapping", () => {
  it("derives assessment publication state", () => {
    expect(assessmentState({ is_published: true, complete: true }).label).toBe("Published");
    expect(assessmentState({ is_published: false, complete: true }).label).toBe("Ready");
    expect(assessmentState({ is_published: false, complete: false }).tone).toBe("warning");
  });
});
