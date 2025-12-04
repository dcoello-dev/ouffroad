import { describe, it, expect, beforeEach, vi } from "vitest";
import axios from "axios";
import { ApiService } from "./ApiService";

// Mock axios
vi.mock("axios");

describe("ApiService", () => {
  beforeEach(() => {
    // Reset singleton instance before each test
    (ApiService as any).instance = null;
    vi.clearAllMocks();
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      // Mock axios for constructor
      vi.mocked(axios.get).mockResolvedValue({ data: { categories: {} } });

      const instance1 = ApiService.getInstance();
      const instance2 = ApiService.getInstance();

      expect(instance1).toBe(instance2);
    });

    it("should create only one instance", () => {
      vi.mocked(axios.get).mockResolvedValue({ data: { categories: {} } });

      const instance1 = ApiService.getInstance();
      const instance2 = ApiService.getInstance();
      const instance3 = ApiService.getInstance();

      expect(instance1).toBe(instance2);
      expect(instance2).toBe(instance3);
    });
  });

  describe("Configuration Loading", () => {
    it("should load config from API", async () => {
      const mockConfig = {
        repo_base_url: "https://example.com/uploads",
        categories: {
          trail: {
            type: "track",
            extensions: [".gpx"],
            label: "Trail",
            color: "gold",
          },
          enduro: {
            type: "track",
            extensions: [".gpx"],
            label: "Enduro",
            color: "red",
          },
        },
      };

      vi.mocked(axios.get).mockResolvedValue({ data: mockConfig });

      const service = ApiService.getInstance();
      await service.ensureConfigLoaded();

      expect(axios.get).toHaveBeenCalledWith("/api/config");
      expect(service.getRepoBaseUrl()).toBe("https://example.com/uploads");
    });

    it("should cache config after first load", async () => {
      const mockConfig = {
        repo_base_url: "https://example.com/uploads",
        categories: {},
      };

      vi.mocked(axios.get).mockResolvedValue({ data: mockConfig });

      const service = ApiService.getInstance();

      await service.ensureConfigLoaded();
      await service.ensureConfigLoaded();
      await service.ensureConfigLoaded();

      // Should only fetch once (called in constructor)
      expect(axios.get).toHaveBeenCalledTimes(1);
    });
  });

  describe("Category Management", () => {
    it("should return categories from config", async () => {
      const mockConfig = {
        repo_base_url: "https://example.com/uploads",
        categories: {
          trail: {
            type: "track",
            extensions: [".gpx"],
            label: "Trail",
            color: "gold",
          },
          enduro: {
            type: "track",
            extensions: [".gpx"],
            label: "Enduro",
            color: "red",
          },
        },
      };

      vi.mocked(axios.get).mockResolvedValue({ data: mockConfig });

      const service = ApiService.getInstance();
      await service.ensureConfigLoaded();

      const categories = service.getCategories();

      expect(categories).toHaveProperty("trail");
      expect(categories).toHaveProperty("enduro");
      expect(categories.trail.color).toBe("gold");
      expect(categories.enduro.color).toBe("red");
    });

    it("should return empty object if config not loaded yet", () => {
      // Mock axios to never resolve
      vi.mocked(axios.get).mockImplementation(() => new Promise(() => {}));

      const service = ApiService.getInstance();
      const categories = service.getCategories();

      expect(categories).toEqual({});
    });
  });

  describe("Error Handling", () => {
    it("should handle config fetch errors gracefully", async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error("Network error"));

      const service = ApiService.getInstance();

      // ensureConfigLoaded should not throw, but log error
      await expect(service.ensureConfigLoaded()).resolves.toBeUndefined();
    });

    it("should use default repo URL if config fails", async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error("Network error"));

      const service = ApiService.getInstance();
      await service.ensureConfigLoaded();

      // Should use default fallback
      expect(service.getRepoBaseUrl()).toBe("/uploads");
    });
  });
});
