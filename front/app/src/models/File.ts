export interface IFile {
  filename: string;
  fullPath: string;
  type: "track" | "media" | "zone";
  category?: string;
}

export class Track implements IFile {
  filename: string;
  fullPath: string;
  readonly type = "track";
  category?: string;

  constructor(data: IFile) {
    this.filename = data.filename;
    this.fullPath = data.fullPath;
    this.category = data.category;
  }

  // Encapsulated logic for tracks can go here
  getDisplayName(): string {
    return this.filename.split("/").pop() || this.filename;
  }
}

export class Media implements IFile {
  filename: string;
  fullPath: string;
  readonly type = "media";
  category?: string;

  constructor(data: IFile) {
    this.filename = data.filename;
    this.fullPath = data.fullPath;
    this.category = data.category;
  }

  getDisplayName(): string {
    return this.filename.split("/").pop() || this.filename;
  }

  isVideo(): boolean {
    const ext = this.filename.split(".").pop()?.toLowerCase();
    return ["mp4", "mov", "avi", "mkv"].includes(ext || "");
  }
}

export class Zone implements IFile {
  filename: string;
  fullPath: string;
  readonly type = "zone";
  category?: string;

  constructor(data: IFile) {
    this.filename = data.filename;
    this.fullPath = data.fullPath;
    this.category = data.category;
  }

  getDisplayName(): string {
    return this.filename.split("/").pop() || this.filename;
  }
}
