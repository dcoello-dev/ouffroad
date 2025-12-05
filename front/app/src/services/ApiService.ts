import axios from "axios";
import { Track, Media } from "../models/File";
import type { IFile } from "../models/File";
import type { GeoJsonFeatureCollection } from "../models/GeoJson";

export class ApiService {
  private static instance: ApiService;
  private baseUrl: string = "/api";
  private repoBaseUrl: string = "/uploads"; // Default fallback
  private configPromise: Promise<void>;

  private categories: Record<string, any> = {};

  private constructor() {
    this.configPromise = this.fetchConfig();
  }

  private async fetchConfig(): Promise<void> {
    try {
      console.log("[ApiService] Fetching config from /api/config...");
      const response = await axios.get(`${this.baseUrl}/config`);
      console.log("[ApiService] Config response:", response.data);
      if (response.data.repo_base_url) {
        this.repoBaseUrl = response.data.repo_base_url;
        console.log("[ApiService] Set repoBaseUrl to:", this.repoBaseUrl);
      }
      if (response.data.categories) {
        this.categories = response.data.categories;
        console.log("[ApiService] Loaded categories:", this.categories);
        console.log(
          "[ApiService] Categories keys:",
          Object.keys(this.categories),
        );
      } else {
        console.warn(
          "[ApiService] No categories found in config response:",
          response.data,
        );
      }
    } catch (error) {
      console.error("[ApiService] Failed to fetch config", error);
    }
  }

  public async ensureConfigLoaded(): Promise<void> {
    await this.configPromise;
  }

  public getRepoBaseUrl(): string {
    return this.repoBaseUrl;
  }

  public getCategories(): Record<string, any> {
    return this.categories;
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  async getTracks(): Promise<IFile[]> {
    const response = await axios.get(`${this.baseUrl}/tracks`);
    // The backend returns a tree structure or list depending on implementation.
    // Assuming list based on current API analysis, but we might need to parse the tree.
    // Wait, the backend returns `{"tracks": [...]}` where ... is a list of strings.
    // We need to parse these strings into Track/Media objects.

    const files: IFile[] = [];
    const rawPaths: string[] = response.data.tracks;

    rawPaths.forEach((path) => {
      const parts = path.split("/");
      const category = parts[0];
      const isMedia =
        category === "media" || category === "fotos" || category === "videos";

      if (isMedia) {
        files.push(
          new Media({
            filename: path,
            fullPath: path,
            category,
            type: "media",
          }),
        );
      } else {
        files.push(
          new Track({
            filename: path,
            fullPath: path,
            category,
            type: "track",
          }),
        );
      }
    });

    return files;
  }

  async getTrackGeoJSON(filename: string): Promise<GeoJsonFeatureCollection> {
    const response = await axios.get(`${this.baseUrl}/track/${filename}`);
    return response.data;
  }

  async uploadFiles(
    files: FileList,
    category: string,
    location?: { lat: number; lng: number },
  ): Promise<void> {
    const formData = new FormData();
    formData.append("category", category);
    if (location) {
      formData.append("latitude", location.lat.toString());
      formData.append("longitude", location.lng.toString());
    }

    for (let i = 0; i < files.length; i++) {
      formData.append("file", files[i]);
      // We should probably upload one by one or handle batch if API supports it.
      // The current API seems to handle one file per request in the loop in main.js,
      // but the endpoint signature suggests single file upload per request.
      // "file: UploadFile = File(...)"

      // So we need to make multiple requests.
      const singleFormData = new FormData();
      singleFormData.append("file", files[i]);
      singleFormData.append("category", category);
      if (location) {
        singleFormData.append("latitude", location.lat.toString());
        singleFormData.append("longitude", location.lng.toString());
      }
      await axios.post(`${this.baseUrl}/upload`, singleFormData);
    }
  }

  async updateMediaLocation(
    filename: string,
    latitude: number,
    longitude: number,
  ): Promise<void> {
    try {
      console.log(
        "[ApiService] Updating location for:",
        filename,
        "to",
        latitude,
        longitude,
      );
      const response = await axios.post(
        `${this.baseUrl}/media/${filename}/location`,
        {
          latitude,
          longitude,
        },
      );
      console.log("[ApiService] Location update response:", response.data);
    } catch (error: unknown) {
      console.error("[ApiService] Error updating location:", error);
      if (axios.isAxiosError(error)) {
        console.error("[ApiService] Error details:", error.response?.data);
      } else if (error instanceof Error) {
        console.error("[ApiService] Generic Error details:", error.message);
      }
      throw error;
    }
  }

  public getFileUrl(file: IFile): string {
    return `${this.repoBaseUrl}/${file.fullPath}`;
  }
}
