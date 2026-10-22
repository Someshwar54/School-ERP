import { execFileSync } from "node:child_process";
import { expect, type Page } from "@playwright/test";

/** Reads a fictional student's seeded phone (the prototype's initial password) from the e2e database. */
export function studentPhone(code: string): string {
  const sql = `select set_config('app.school_id',(select id::text from schools where slug='demo'),false); select phone from student_profiles where student_code='${code}'`;
  const out = execFileSync("psql", ["-h", "localhost", "-U", "school_app", "-d", "school_erp_e2e", "-tAc", sql], {
    env: { ...process.env, PGPASSWORD: process.env.E2E_DB_PASSWORD ?? "school_app_dev_password" },
  }).toString();
  return out.trim().split("\n").pop() as string;
}

export async function signIn(page: Page, portal: "student" | "staff" | "director", id: string, password: string) {
  await page.goto(`/erp/login/${portal}`);
  await page.getByRole("textbox", { name: /ID/ }).fill(id);
  await page.locator("input[name=password]").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

/** Signs in and waits until the workspace has loaded (the session cookie is then set). */
export async function signInTo(page: Page, portal: "student" | "staff" | "director", id: string, password: string) {
  await signIn(page, portal, id, password);
  await expect(page).toHaveURL(/\/erp\/(student|staff|management)/);
  await expect(page.getByTestId("signed-in-name")).toBeVisible();
}

export async function expectSignedInAs(page: Page, name: string) {
  await expect(page.getByTestId("signed-in-name")).toHaveText(name);
}
