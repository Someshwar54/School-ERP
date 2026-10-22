import { expect, test } from "@playwright/test";

test("home page loads with school identity and no private data", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Sunrise Valley Public School/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText("fictional demonstration school", { exact: false }).first()).toBeVisible();
  const html = await page.content();
  expect(html).not.toMatch(/STU\d{4}/); // no student IDs on public pages
});

for (const [path, heading] of [
  ["/about", /About Sunrise Valley/],
  ["/academics", /Curriculum and learning/],
  ["/admissions", /Joining our school/],
  ["/facilities", /Facilities/],
  ["/faculty", /Faculty and leadership/],
  ["/news", /News, notices and events/],
  ["/contact", /Contact us/],
] as const) {
  test(`public page ${path} renders`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  });
}

test("ERP Portal button sits top-right and opens the portal entry page", async ({ page }) => {
  await page.goto("/");
  const button = page.getByTestId("erp-portal-button");
  await expect(button).toBeVisible();
  const box = await button.boundingBox();
  expect(box && box.x).toBeGreaterThan(1000); // right side of a 1366px header
  expect(box && box.y).toBeLessThan(60);
  await button.click();
  await expect(page).toHaveURL(/\/erp$/);
  await expect(page.getByRole("heading", { name: /Welcome to the ERP Portal/ })).toBeVisible();
});

test("portal entry offers exactly Student, Staff and Director login", async ({ page }) => {
  await page.goto("/erp");
  for (const [testId, url, heading] of [
    ["portal-student", "/erp/login/student", "Student Login"],
    ["portal-staff", "/erp/login/staff", "Staff Login"],
    ["portal-director", "/erp/login/director", "Director Login"],
  ] as const) {
    await page.goto("/erp");
    await page.getByTestId(testId).click();
    await expect(page).toHaveURL(new RegExp(`${url}$`));
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  }
  await page.goto("/erp");
  await expect(page.getByRole("link", { name: /^(Teacher Login|Non-teaching Staff Login)/i })).toHaveCount(0);
  await page.getByRole("link", { name: /Back to school website/ }).click();
  await expect(page).toHaveURL(/\/$/);
});

test("contact form validates input and records an enquiry honestly", async ({ page }) => {
  await page.goto("/contact");
  await page.getByRole("button", { name: "Send enquiry" }).click();
  await expect(page.getByText("Enter your name.")).toBeVisible();
  await expect(page.getByText("Enter a 10-digit Indian mobile number.")).toBeVisible();
  await page.getByLabel(/Parent \/ guardian name/).fill("E2E Parent");
  await page.getByLabel(/^Email/).fill("e2e@example.com");
  await page.getByLabel(/Mobile number/).fill("9876543210");
  await page.getByLabel(/Grade sought/).selectOption("Grade 7");
  await page.getByRole("button", { name: "Send enquiry" }).click();
  await expect(page.getByText("Enquiry received")).toBeVisible();
  await expect(page.getByText(/not connected in this prototype/)).toBeVisible();
});
