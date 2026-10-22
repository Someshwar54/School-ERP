import { expect, test } from "@playwright/test";
import { signIn, studentPhone } from "./helpers";

async function noHorizontalScroll(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

test("public site works on a phone", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("erp-portal-button")).toBeVisible();
  await noHorizontalScroll(page);
  await page.getByRole("button", { name: "Open menu" }).click();
  await page.getByRole("navigation", { name: "Mobile" }).getByRole("link", { name: "Admissions" }).click();
  await expect(page).toHaveURL(/\/admissions$/);
  await noHorizontalScroll(page);
  for (const path of ["/about", "/facilities", "/contact", "/erp", "/erp/login/student"]) {
    await page.goto(path);
    await noHorizontalScroll(page);
  }
});

test("student workspace navigation works on a phone", async ({ page }) => {
  await signIn(page, "student", "STU0183", studentPhone("STU0183"));
  await expect(page).toHaveURL(/\/erp\/student$/);
  await noHorizontalScroll(page);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Fees & Payments" }).click();
  await expect(page.getByRole("heading", { name: "Fees and payments" })).toBeVisible();
  await noHorizontalScroll(page);
});
