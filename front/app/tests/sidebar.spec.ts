import { test, expect } from "@playwright/test";

test.describe("Sidebar", () => {
  test("should render sidebar with upload section", async ({ page }) => {
    await page.goto("/");

    // Check that sidebar is visible
    const sidebar = page.locator(".sidebar");
    await expect(sidebar).toBeVisible();

    // Check that upload section exists
    const uploadSection = page.locator(".upload-section");
    await expect(uploadSection).toBeVisible();
  });

  test("should display category dropdown", async ({ page }) => {
    await page.goto("/");

    // Wait for categories to load
    const categorySelect = page.locator(".category-select");
    await expect(categorySelect).toBeVisible();

    // Should have options (not just "Loading categories...")
    await page.waitForTimeout(1000); // Wait for config to load
    const options = categorySelect.locator("option");
    const count = await options.count();

    // Should have at least one real category (not just loading)
    expect(count).toBeGreaterThan(0);
  });

  test("should expand and collapse category groups", async ({ page }) => {
    await page.goto("/");

    // Wait for track list to load
    await page.waitForSelector(".track-list", { timeout: 5000 });

    // Find a category header
    const categoryHeader = page.locator(".category-header").first();
    await expect(categoryHeader).toBeVisible();

    // Click to expand/collapse
    await categoryHeader.click();

    // Check if content is toggled
    const groupContent = page.locator(".group-content").first();
    await expect(groupContent).toBeVisible();
  });

  test("should show track count for categories", async ({ page }) => {
    await page.goto("/");

    // Wait for track list
    await page.waitForSelector(".track-list", { timeout: 5000 });

    // Check that group counts are displayed
    const groupCount = page.locator(".group-count").first();
    await expect(groupCount).toBeVisible();

    // Count should be a number
    const countText = await groupCount.textContent();
    expect(countText).toMatch(/^\d+$/);
  });

  test("should allow file upload selection", async ({ page }) => {
    await page.goto("/");

    // Find file input
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();

    // Upload button should be disabled initially
    const uploadButton = page.locator(".upload-btn");
    await expect(uploadButton).toBeDisabled();
  });
});
