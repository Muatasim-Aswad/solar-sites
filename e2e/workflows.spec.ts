import { expect, test, type Page } from "@playwright/test";

const password = "Assessment-test-password-123!";

async function register(page: Page, email: string) {
  await page.goto("/register");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Client sites", exact: true })).toBeVisible();
}

test("an advisor can manage a site and compare battery self-consumption", async ({ page }) => {
  await register(page, "sites@example.com");
  await page.getByRole("link", { name: "Add a site", exact: true }).click();
  await page.getByLabel("Client name", { exact: true }).fill("Sample household");
  await page.getByLabel("Site address").fill("Example street 10");
  await page.getByLabel("Latitude", { exact: true }).fill("52.08");
  await page.getByLabel("Longitude", { exact: true }).fill("4.31");
  await page.getByLabel("Panel capacity (kWp)").fill("0");
  await page.getByRole("button", { name: "Create site", exact: true }).click();
  await expect(page.getByText("Panel capacity must be greater than zero.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Add a client site" })).toBeVisible();

  await page.getByLabel("Panel capacity (kWp)").fill("5");
  await page.getByRole("button", { name: "Create site", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sample household", exact: true })).toBeVisible();
  await expect(page.getByRole("row", { name: "Yearly total 8,760" })).toBeVisible();

  const comparison = page.getByRole("region", { name: "What does a battery add?" });
  await comparison.getByLabel("Yearly electricity use (kWh)").fill("8760");
  await comparison.getByLabel("Battery capacity (kWh)").fill("1");
  await comparison.getByRole("button", { name: "Compare battery", exact: true }).click();
  await expect(comparison).toContainText("1 kWh battery · 8,760 kWh yearly use");
  await expect(comparison).toContainText(/Without a battery\s*4,380 kWh/);
  await expect(comparison).toContainText(/With a battery\s*8,760 kWh/);
  await expect(comparison.getByText("+4,380 kWh", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Edit site", exact: true }).click();
  await page.getByLabel("Client name", { exact: true }).fill("Updated household");
  await page.getByLabel("Panel capacity (kWp)").fill("8");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Updated household", exact: true })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Updated household", exact: true })).toBeVisible();
  await expect(page.getByText("8 kWp", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "All client sites", exact: true }).click();
  await page.getByRole("link", { name: "Updated household", exact: true }).click();
  await page.getByRole("button", { name: "Delete site", exact: true }).click();
  await page.getByRole("button", { name: "Delete site permanently", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your first roof starts here." })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Your first roof starts here." })).toBeVisible();
});

test("an advisor sees login errors and cannot open protected pages after logout", async ({
  page,
}) => {
  const email = "sessions@example.com";
  await register(page, email);
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("Incorrect-test-password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Email or password is incorrect.");
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Client sites", exact: true })).toBeVisible();
  await expect(page.getByText(email, { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/sites/new");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Welcome back", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Add a site", exact: true })).toHaveCount(0);
});
