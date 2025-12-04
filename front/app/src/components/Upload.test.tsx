import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Upload } from "./Upload";
import { ApiService } from "../services/ApiService";

// Mock ApiService
vi.mock("../services/ApiService", () => {
  const mockInstance = {
    ensureConfigLoaded: vi.fn().mockResolvedValue(undefined),
    getCategories: vi.fn().mockReturnValue({
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
      special_events: {
        type: "track",
        extensions: [".gpx"],
        label: "Eventos",
        color: "purple",
      },
    }),
    uploadFiles: vi.fn().mockResolvedValue(undefined),
  };

  return {
    ApiService: {
      getInstance: vi.fn(() => mockInstance),
    },
  };
});

describe("Upload Component", () => {
  const mockOnUploadComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render upload form", () => {
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
  });

  it("should load and display categories", async () => {
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    await waitFor(() => {
      expect(
        screen.getByRole("option", { name: /trail/i }),
      ).toBeInTheDocument();
    });

    expect(screen.getByRole("option", { name: /enduro/i })).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /eventos/i }),
    ).toBeInTheDocument();
  });

  it("should disable upload button when no files selected", () => {
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    const uploadButton = screen.getByRole("button", { name: /upload/i });
    expect(uploadButton).toBeDisabled();
  });

  it("should enable upload button when files are selected", async () => {
    const user = userEvent.setup();
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();

    const file = new File(["dummy content"], "test.gpx", {
      type: "application/gpx+xml",
    });

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, file);

      const uploadButton = screen.getByRole("button", { name: /upload/i });
      expect(uploadButton).not.toBeDisabled();
    }
  });

  it("should show location inputs when video file is selected", async () => {
    const user = userEvent.setup();
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();

    const videoFile = new File(["dummy video"], "test.mp4", {
      type: "video/mp4",
    });

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, videoFile);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/latitud/i)).toBeInTheDocument();
      });

      expect(screen.getByPlaceholderText(/longitud/i)).toBeInTheDocument();
    }
  });

  it("should not show location inputs for non-video files", async () => {
    const user = userEvent.setup();
    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    const fileInput = document.querySelector('input[type="file"]');
    const gpxFile = new File(["dummy gpx"], "test.gpx", {
      type: "application/gpx+xml",
    });

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, gpxFile);

      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText(/latitud/i),
        ).not.toBeInTheDocument();
      });
    }
  });

  it("should call uploadFiles when upload button is clicked", async () => {
    const user = userEvent.setup();
    const mockUploadFiles = vi.fn().mockResolvedValue(undefined);

    // Update mock
    (ApiService.getInstance as any).mockReturnValue({
      ensureConfigLoaded: vi.fn().mockResolvedValue(undefined),
      getCategories: vi.fn().mockReturnValue({
        trail: { type: "track", label: "Trail" },
      }),
      uploadFiles: mockUploadFiles,
    });

    render(<Upload onUploadComplete={mockOnUploadComplete} />);

    const fileInput = document.querySelector('input[type="file"]');
    const file = new File(["dummy"], "test.gpx", {
      type: "application/gpx+xml",
    });

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, file);

      const uploadButton = screen.getByRole("button", { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadFiles).toHaveBeenCalled();
      });
    }
  });
});
