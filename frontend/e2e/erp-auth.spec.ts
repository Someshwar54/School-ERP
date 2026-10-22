import { expect, test } from "@playwright/test";
import { expectSignedInAs, signIn, studentPhone } from "./helpers";

test("login form validates empty input and toggles password visibility", async ({ page }) => {
  await page.goto("/erp/login/student");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Enter your Student ID.")).toBeVisible();
  await expect(page.getByText("Enter your password.")).toBeVisible();
  const pw = page.locator("input[name=password]");
  await pw.fill("secret");
  await expect(pw).toHaveAttribute("type", "password");
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(pw).toHaveAttribute("type", "text");
});

test("invalid login shows a generic error and stays on the page", async ({ page }) => {
  await signIn(page, "student", "STU0100", "not-the-password");
  await expect(page.getByText("The ID or password is incorrect.")).toBeVisible();
  await expect(page).toHaveURL(/\/erp\/login\/student$/);
  await signIn(page, "student", "STU9999", "whatever");
  await expect(page.getByText("The ID or password is incorrect.")).toBeVisible();
});

test("student signs in and sees only their own workspace", async ({ page }) => {
  await signIn(page, "student", "STU0181", studentPhone("STU0181"));
  await expect(page).toHaveURL(/\/erp\/student$/);
  await expectSignedInAs(page, "Shreya Chopra");
  await expect(page.getByRole("heading", { name: "Hello, Shreya" })).toBeVisible();
  await expect(page.getByText("You are using an initial password")).toBeVisible();
  await page.getByRole("link", { name: "Attendance" }).click();
  await expect(page.getByRole("heading", { name: "Attendance" })).toBeVisible();
  await expect(page.getByRole("grid")).toBeVisible();
});

test("protected ERP URLs redirect visitors without a session", async ({ page }) => {
  await page.goto("/erp/management/hr");
  await expect(page).toHaveURL(/\/erp\/login\/director$/);
  await page.goto("/erp/student/fees");
  await expect(page).toHaveURL(/\/erp\/login\/student$/);
});

test("a student visiting the management URL is blocked by the backend, not just the menu", async ({ page }) => {
  await signIn(page, "student", "STU0182", studentPhone("STU0182"));
  await expect(page).toHaveURL(/\/erp\/student$/);
  const api = await page.request.get("/api/v1/management/overview");
  expect(api.status()).toBe(403);
  await page.goto("/erp/management");
  await expect(page.getByText("This workspace is not available for your account")).toBeVisible();
  await expect(page.getByText("Fees collected")).toHaveCount(0);
});

test("director portal requires a management role", async ({ page }) => {
  await signIn(page, "director", "EMP1001", "Staff@1001");
  await expect(page.getByText("The ID or password is incorrect.")).toBeVisible();
  await signIn(page, "director", "DIR009", "Mgmt@DIR009");
  await expect(page.getByText("The ID or password is incorrect.")).toBeVisible();
});

test("forgot-password page is honest that recovery is not connected", async ({ page }) => {
  await page.goto("/erp/login/staff");
  await page.getByRole("link", { name: "Forgot password?" }).click();
  await expect(page.getByText("Self-service recovery is not connected yet")).toBeVisible();
});

test("sign out ends the session", async ({ page }) => {
  await signIn(page, "staff", "EMP2005", "Staff@2005");
  await expect(page).toHaveURL(/\/erp\/staff$/);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/erp\/login\/staff$/);
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
});
