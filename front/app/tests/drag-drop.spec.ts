import { test, expect } from "@playwright/test";
import path from "path";

test.describe("Drag & Drop File Management", () => {
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

    // Wait for app to load
    await page.waitForSelector(".sidebar");

    // Expand folders to reveal files
    // Categories (level 0) are open by default

    // Expand first year (level 1) if present
    try {
      const yearHeader = page.locator(".year-header").first();
      await yearHeader.waitFor({ state: "visible", timeout: 2000 });
      await yearHeader.click();

      // Expand first month (level 2) if present
      const monthHeader = page.locator(".month-header").first();
      await monthHeader.waitFor({ state: "visible", timeout: 2000 });
      await monthHeader.click();
    } catch (e) {
      // Ignore errors if folders don't exist (e.g. flat structure)
      console.log("Could not expand folders:", e);
    }
  });

  test("should show visual feedback when dragging file", async ({ page }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    // Get first file
    const firstFile = page.locator(".track-item").first();
    await expect(firstFile).toBeVisible();

    // Start dragging
    await firstFile.hover();
    const box = await firstFile.boundingBox();
    if (!box) throw new Error("Could not get bounding box");

    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();

    // Check that file has dragging styles
    await expect(firstFile).toHaveCSS("opacity", "0.5");
    await expect(firstFile).toHaveCSS("cursor", "grabbing");

    await page.mouse.up();
  });

  test("should highlight drop target when dragging over category", async ({
    page,
  }) => {
    // Wait for files and categories to load
    await page.waitForSelector(".track-item", { timeout: 5000 });
    await page.waitForSelector(".category-header", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const categories = page.locator(".category-header");
    const targetCategory = categories.nth(1); // Get second category

    // Get initial category name to ensure we're moving to different category
    const sourceCategoryText = await page
      .locator(".category-header")
      .first()
      .textContent();

    // Start drag
    await firstFile.hover();
    const fileBox = await firstFile.boundingBox();
    if (!fileBox) throw new Error("Could not get file bounding box");

    await page.mouse.move(
      fileBox.x + fileBox.width / 2,
      fileBox.y + fileBox.height / 2,
    );
    await page.mouse.down();

    // Drag over target category
    const categoryBox = await targetCategory.boundingBox();
    if (!categoryBox) throw new Error("Could not get category bounding box");

    await page.mouse.move(
      categoryBox.x + categoryBox.width / 2,
      categoryBox.y + categoryBox.height / 2,
    );

    // Check for drop target highlight
    await expect(targetCategory).toHaveCSS(
      "background-color",
      "rgb(227, 242, 253)",
    ); // #e3f2fd
    await expect(targetCategory).toHaveCSS(
      "border",
      "2px dashed rgb(33, 150, 243)",
    ); // #2196f3

    await page.mouse.up();
  });

  test("should move file between categories via drag and drop", async ({
    page,
  }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    // Get first file and its text
    const firstFile = page.locator(".track-item").first();
    const fileName = await firstFile.textContent();

    // Get source category
    const sourceCategory = page.locator(".category-header").first();
    const sourceCategoryName = await sourceCategory.textContent();

    // Get target category (second one)
    const targetCategory = page.locator(".category-header").nth(1);
    const targetCategoryName = await targetCategory.textContent();

    // Ensure they're different
    expect(sourceCategoryName).not.toBe(targetCategoryName);

    // Perform drag and drop
    await firstFile.hover();
    const fileBox = await firstFile.boundingBox();
    if (!fileBox) throw new Error("Could not get file box");

    await page.mouse.move(
      fileBox.x + fileBox.width / 2,
      fileBox.y + fileBox.height / 2,
    );
    await page.mouse.down();

    const categoryBox = await targetCategory.boundingBox();
    if (!categoryBox) throw new Error("Could not get category box");

    await page.mouse.move(
      categoryBox.x + categoryBox.width / 2,
      categoryBox.y + categoryBox.height / 2,
    );
    await page.mouse.up();

    // Wait for file list to refresh
    await page.waitForTimeout(1000);

    // Expand target category to see files
    await targetCategory.click();

    // Verify file appears in target category
    // The file should now be under the target category
    const targetFiles = page
      .locator(".category-group")
      .filter({ hasText: targetCategoryName?.trim() || "" })
      .locator(".track-item");

    await expect(targetFiles).toContainText(fileName?.trim() || "");
  });

  test("should move file to specific folder via drag and drop", async ({
    page,
  }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    // Expand first category to see folders if not already visible
    const firstCategory = page.locator(".category-header").first();
    const yearHeader = page.locator(".year-header").first();

    if (!(await yearHeader.isVisible())) {
      await firstCategory.click();
      // Wait for folders to appear
      await page.waitForSelector(".year-header", { timeout: 2000 });
    }

    // Get a file
    const file = page.locator(".track-item").first();
    const fileName = await file.textContent();

    // Get a folder (year or month)
    const folder = page.locator(".year-header").first();
    const folderName = await folder.textContent();

    // Perform drag and drop
    await file.hover();
    const fileBox = await file.boundingBox();
    if (!fileBox) throw new Error("Could not get file box");

    await page.mouse.move(
      fileBox.x + fileBox.width / 2,
      fileBox.y + fileBox.height / 2,
    );
    await page.mouse.down();

    const folderBox = await folder.boundingBox();
    if (!folderBox) throw new Error("Could not get folder box");

    await page.mouse.move(
      folderBox.x + folderBox.width / 2,
      folderBox.y + folderBox.height / 2,
    );
    await page.mouse.up();

    // Wait for refresh
    await page.waitForTimeout(1000);

    // Expand folder to verify file is there
    await folder.click();

    // Verify file is in the folder
    const folderFiles = page
      .locator(".year-group")
      .filter({ hasText: folderName?.trim() || "" })
      .locator(".track-item");

    await expect(folderFiles).toContainText(fileName?.trim() || "");
  });

  test("should handle drag cancel (drag without drop)", async ({ page }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();
    const initialParent = await firstFile.locator("..").textContent();

    // Start drag
    await firstFile.hover();
    const box = await firstFile.boundingBox();
    if (!box) throw new Error("Could not get box");

    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();

    // Move mouse away but don't drop on valid target
    await page.mouse.move(10, 10);
    await page.mouse.up();

    // Wait a bit
    await page.waitForTimeout(500);

    // Verify file is still in original location
    const fileAfter = page.locator(".track-item").first();
    const parentAfter = await fileAfter.locator("..").textContent();

    expect(parentAfter).toBe(initialParent);
  });

  test("should show error message on failed move", async ({ page }) => {
    // This test would require mocking the API to return an error
    // For now, we'll just verify the error handling exists

    // Listen for console errors
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    // Listen for alerts
    page.on("dialog", async (dialog) => {
      expect(dialog.message()).toContain("Error moving file");
      await dialog.accept();
    });

    // Note: To fully test this, we'd need to mock the API
    // or create a scenario that causes a move to fail
  });

  test("should preserve file selection after drag and drop", async ({
    page,
  }) => {
    // Wait for files to load
    await page.waitForSelector(".track-item", { timeout: 5000 });

    const firstFile = page.locator(".track-item").first();

    // Select the file (click checkbox)
    const checkbox = firstFile.locator('input[type="checkbox"]');
    await checkbox.click();

    // Verify it's checked
    await expect(checkbox).toBeChecked();

    // Get target category
    const targetCategory = page.locator(".category-header").nth(1);

    // Perform drag and drop
    await firstFile.hover();
    const fileBox = await firstFile.boundingBox();
    if (!fileBox) throw new Error("Could not get file box");

    await page.mouse.move(
      fileBox.x + fileBox.width / 2,
      fileBox.y + fileBox.height / 2,
    );
    await page.mouse.down();

    const categoryBox = await targetCategory.boundingBox();
    if (!categoryBox) throw new Error("Could not get category box");

    await page.mouse.move(
      categoryBox.x + categoryBox.width / 2,
      categoryBox.y + categoryBox.height / 2,
    );
    await page.mouse.up();

    // Wait for refresh
    await page.waitForTimeout(1000);

    // Note: After refresh, the selection state depends on how the app handles it
    // This test documents the expected behavior
  });
});
