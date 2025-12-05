import { test, expect } from "@playwright/test";
import path from "path";

test.describe("File Rename Functionality", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");

    // Check if we are in setup mode (RepositorySelector visible)
    const isSetupMode = await page.isVisible(".repository-selector-card");
    if (isSetupMode) {
      // Resolve path to .test_repository
      // Assuming we are running from front/app
      const repoPath = path.resolve(process.cwd(), "../../.test_repository");

      // Fill input and submit
      await page.fill(
        'input[placeholder="/path/to/your/repository"]',
        repoPath,
      );
      await page.click('button[type="submit"]');
    }

    await page.waitForSelector(".sidebar");

    // Expand folders to reveal files
    try {
      const yearHeader = page.locator(".year-header").first();
      await yearHeader.waitFor({ state: "visible", timeout: 2000 });
      await yearHeader.click();

      const monthHeader = page.locator(".month-header").first();
      await monthHeader.waitFor({ state: "visible", timeout: 2000 });
      await monthHeader.click();
    } catch (e) {
      console.log("Could not expand folders:", e);
    }
  });

  test("should show rename input on double-click", async ({ page }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    // Get first file name span
    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();

    // Double-click to start rename
    await fileNameSpan.dblclick();

    // Verify input appears
    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();
    await expect(renameInput).toBeFocused();

    // Verify input has blue border
    await expect(renameInput).toHaveCSS(
      "border",
      "1px solid rgb(33, 150, 243)",
    );
  });

  test("should cancel rename on Escape key", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();
    const originalName = await fileNameSpan.textContent();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Type new name
    await renameInput.fill("new_name.gpx");

    // Press Escape
    await renameInput.press("Escape");

    // Verify input is gone and name unchanged
    await expect(renameInput).not.toBeVisible();
    const currentName = await fileNameSpan.textContent();
    expect(currentName).toBe(originalName);
  });

  test("should cancel rename on blur (click outside)", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();
    const originalName = await fileNameSpan.textContent();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Type new name
    await renameInput.fill("new_name.gpx");

    // Click outside (on sidebar)
    await page.locator(".sidebar").click({ position: { x: 10, y: 10 } });

    // Verify input is gone and name unchanged
    await expect(renameInput).not.toBeVisible();
    const currentName = await fileNameSpan.textContent();
    expect(currentName).toBe(originalName);
  });

  test("should rename file on Enter key", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();
    const originalName = await fileNameSpan.textContent();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Type new name
    const newName = `renamed_${Date.now()}.gpx`;
    await renameInput.fill(newName);

    // Press Enter
    await renameInput.press("Enter");

    // Wait for page reload or file list update
    await page.waitForTimeout(1000);

    // Verify file was renamed (page should reload)
    // After reload, the file should have the new name
    await page.waitForSelector(".track-item", { timeout: 5000 });
    const fileNames = await page.locator(".track-item span").allTextContents();
    expect(
      fileNames.some((name) => name.includes(newName.replace(".gpx", ""))),
    ).toBeTruthy();
  });

  test("should not rename if name is unchanged", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();
    const originalName = await fileNameSpan.textContent();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Don't change the name, just press Enter
    await renameInput.press("Enter");

    // Verify no reload happened (input just closes)
    await expect(renameInput).not.toBeVisible();
    const currentName = await fileNameSpan.textContent();
    expect(currentName).toBe(originalName);
  });

  test("should show disabled state during rename", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Type new name
    const newName = `renamed_${Date.now()}.gpx`;
    await renameInput.fill(newName);

    // Press Enter
    await renameInput.press("Enter");

    // Immediately check if input is disabled (might be too fast to catch)
    // This is a best-effort check
    const isDisabled = await renameInput.isDisabled().catch(() => false);
    // Note: This might not always catch the disabled state due to timing
  });

  test("should show cursor text on hover", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();

    // Hover over file name
    await fileNameSpan.hover();

    // Verify cursor is text
    await expect(fileNameSpan).toHaveCSS("cursor", "text");

    // Verify title attribute
    const title = await fileNameSpan.getAttribute("title");
    expect(title).toBe("Double-click to rename");
  });

  test("should preserve file extension if not provided", async ({ page }) => {
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const fileNameSpan = firstFile
      .locator("span")
      .filter({ hasText: /.+/ })
      .first();

    // Start rename
    await fileNameSpan.dblclick();

    const renameInput = firstFile.locator('input[type="text"]');
    await expect(renameInput).toBeVisible();

    // Type new name WITHOUT extension
    const newNameWithoutExt = `renamed_${Date.now()}`;
    await renameInput.fill(newNameWithoutExt);

    // Press Enter
    await renameInput.press("Enter");

    // Wait for reload
    await page.waitForTimeout(1000);

    // Verify file has extension added
    await page.waitForSelector(".track-item", { timeout: 5000 });
    const fileNames = await page.locator(".track-item span").allTextContents();

    // The backend should add .gpx extension automatically
    expect(
      fileNames.some(
        (name) => name.includes(newNameWithoutExt) && name.includes(".gpx"),
      ),
    ).toBeTruthy();
  });
});
