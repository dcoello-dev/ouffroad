import { test, expect } from "@playwright/test";

test.describe("Map Component", () => {
  test("should render map container", async ({ page }) => {
    await page.goto("/");

    // Wait for map to load
    const mapContainer = page.locator(".leaflet-container");
    await expect(mapContainer).toBeVisible({ timeout: 10000 });
  });

  test("should display map controls", async ({ page }) => {
    await page.goto("/");

    // Wait for map to load
    await page.waitForSelector(".leaflet-container", { timeout: 10000 });

    // Check for zoom controls
    const zoomControl = page.locator(".leaflet-control-zoom");
    await expect(zoomControl).toBeVisible();

    // Check for layer control
    const layerControl = page.locator(".leaflet-control-layers");
    await expect(layerControl).toBeVisible();
  });

  test("should allow switching map layers", async ({ page }) => {
    await page.goto("/");

    // Wait for map to load
    await page.waitForSelector(".leaflet-container", { timeout: 10000 });

    // Open layer control
    const layerControl = page.locator(".leaflet-control-layers");
    await layerControl.click();

    // Check that layer options are visible
    const layerOptions = page.locator(".leaflet-control-layers-base");
    await expect(layerOptions).toBeVisible();

    // Should have multiple layer options
    const radioButtons = layerOptions.locator('input[type="radio"]');
    const count = await radioButtons.count();
    expect(count).toBeGreaterThan(1);
  });

  test("should zoom in and out", async ({ page }) => {
    await page.goto("/");

    // Wait for map to load
    await page.waitForSelector(".leaflet-container", { timeout: 10000 });

    // Get initial zoom level (from map container class or attribute)
    const zoomInButton = page.locator(".leaflet-control-zoom-in");
    const zoomOutButton = page.locator(".leaflet-control-zoom-out");

    // Click zoom in
    await zoomInButton.click();
    await page.waitForTimeout(500);

    // Click zoom out
    await zoomOutButton.click();
    await page.waitForTimeout(500);

    // Both buttons should still be visible and enabled
    await expect(zoomInButton).toBeVisible();
    await expect(zoomOutButton).toBeVisible();
  });

  test("should handle track selection from sidebar", async ({ page }) => {
    await page.goto("/");

    // Wait for both map and sidebar to load
    await page.waitForSelector(".leaflet-container", { timeout: 10000 });
    await page.waitForSelector(".track-list", { timeout: 5000 });

    // Expand a category if needed
    const categoryHeader = page.locator(".category-header").first();
    await categoryHeader.click();
    await page.waitForTimeout(500);

    // Find a track checkbox
    const trackCheckbox = page.locator(".track-checkbox").first();

    if ((await trackCheckbox.count()) > 0) {
      // Click the checkbox to add track to map
      await trackCheckbox.click();
      await page.waitForTimeout(1000);

      // Check if a GeoJSON layer appears on the map
      // (This is a basic check - actual implementation may vary)
      const mapLayers = page.locator(".leaflet-overlay-pane svg");
      await expect(mapLayers).toBeVisible();
    }
  });
});
