import { expect, test } from "@playwright/test";
import { signInTo as signIn } from "./helpers";

test("teacher who is also a class teacher gets both workspaces from one account", async ({ page }) => {
  await signIn(page, "staff", "EMP1001", "Staff@1001");
  await expect(page.getByRole("heading", { name: "Teacher dashboard" })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Workspace" });
  await expect(nav.getByRole("link", { name: "Assessments & Marks" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "My Class (Class Teacher)" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Fees & Finance" })).toHaveCount(0);
});

test("closing the completion prompt never completes a topic", async ({ page }) => {
  await signIn(page, "staff", "EMP1001", "Staff@1001");
  await page.goto("/erp/staff/topics");
  await expect(page.getByLabel("Class and subject")).toBeVisible();
  const row = page.locator("[data-testid^=topic-]", { has: page.getByText(/^In progress$/i) }).first();
  await expect(row).toBeVisible();
  const title = (await row.locator("p.font-medium").first().innerText()).trim();
  await row.getByRole("button", { name: "Mark complete…" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("button", { name: "Confirm completion" })).toBeDisabled();
  await dialog.getByRole("button", { name: "Cancel — keep in progress" }).click();
  await page.reload();
  const same = page.locator("[data-testid^=topic-]", { hasText: title });
  await expect(same.getByText(/^In progress$/i)).toBeVisible();
});

test("non-teaching staff see only their permitted modules", async ({ page }) => {
  await signIn(page, "staff", "EMP2005", "Staff@2005");
  const nav = page.getByRole("navigation", { name: "Workspace" });
  await expect(nav.getByRole("link", { name: "Leave Requests" })).toBeVisible();
  for (const hidden of ["Student Attendance", "Assessments & Marks", "Fees & Finance", "HR"]) {
    await expect(nav.getByRole("link", { name: hidden, exact: true })).toHaveCount(0);
  }
  expect((await page.request.get("/api/v1/finance/summary")).status()).toBe(403);
});

test("board member sees aggregates but not salaries", async ({ page }) => {
  await signIn(page, "director", "DIR003", "Mgmt@DIR003");
  await expect(page.getByRole("heading", { name: "Executive overview" })).toBeVisible();
  await expect(page.getByText("Fictional demonstration data").first()).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Workspace" });
  await expect(nav.getByRole("link", { name: "Payroll & HR" })).toHaveCount(0);
  expect((await page.request.get("/api/v1/hr/payroll")).status()).toBe(403);
});

test("director sees Plotly analytics with table fallbacks", async ({ page }) => {
  await signIn(page, "director", "DIR001", "Mgmt@DIR001");
  await expect(page.getByRole("heading", { name: "Executive overview" })).toBeVisible();
  await expect(page.locator(".js-plotly-plot").first()).toBeVisible({ timeout: 20_000 });
  await page.getByText("View as table").first().click();
  await expect(page.getByRole("columnheader", { name: "Attendance" }).first()).toBeVisible();
});
