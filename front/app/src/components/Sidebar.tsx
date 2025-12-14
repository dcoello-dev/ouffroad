import React, { useState } from "react";
import type { IFile } from "../models/File";
import { Upload } from "./Upload";
import { ApiService } from "../services/ApiService";
import { MediaViewer } from "./MediaViewer";

interface SidebarProps {
  files: IFile[];
  activeFiles: IFile[];
  onToggle: (file: IFile) => void;
  onUploadComplete: () => void;
  onSetLocationRequest: (filePath: string) => void;
  onHover: (ids: string[]) => void;
  onChangeRepository: () => void;
}

interface DragState {
  draggedFile: IFile | null;
  dropTarget: string | null;
}

interface TreeNode {
  name: string;
  path: string;
  children: Record<string, TreeNode>;
  files: IFile[];
  isOpen: boolean;
}

const buildTree = (files: IFile[]): Record<string, TreeNode> => {
  const root: Record<string, TreeNode> = {};

  files.forEach((file) => {
    const parts = file.fullPath.split("/");
    // Remove filename from parts to get directories
    const dirs = parts.slice(0, -1);

    let currentLevel = root;
    let currentPath = "";

    // Handle root level files (if any)
    if (dirs.length === 0) {
      const category = "Uncategorized";
      if (!root[category]) {
        root[category] = {
          name: category,
          path: category,
          children: {},
          files: [],
          isOpen: true,
        };
      }
      root[category].files.push(file);
      return;
    }

    // Build directory tree
    dirs.forEach((dir, index) => {
      currentPath = currentPath ? `${currentPath}/${dir}` : dir;

      if (!currentLevel[dir]) {
        currentLevel[dir] = {
          name: dir,
          path: currentPath,
          children: {},
          files: [],
          isOpen: false, // Default closed except top level?
        };
      }

      // If it's the last directory, add the file
      if (index === dirs.length - 1) {
        currentLevel[dir].files.push(file);
      }

      currentLevel = currentLevel[dir].children;
    });
  });

  return root;
};

interface TreeNodeProps {
  node: TreeNode;
  activeFiles: IFile[];
  onToggle: (file: IFile) => void;
  onSetLocationRequest: (filePath: string) => void;
  onHover: (ids: string[]) => void;
  level: number;
  onDragStart: (file: IFile) => void;
  onDragOver: (targetPath: string) => void;
  onDragLeave: () => void;
  onDrop: (targetPath: string) => void;
  dragState: DragState;
  onViewMedia: (file: IFile) => void;
}

const TreeNodeComponent: React.FC<TreeNodeProps> = ({
  node,
  activeFiles,
  onToggle,
  onSetLocationRequest,
  onHover,
  level,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  dragState,
  onViewMedia,
}) => {
  const [isOpen, setIsOpen] = useState(level === 0); // Open top level by default
  const [editingFile, setEditingFile] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);

  const toggleOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleRenameStart = (file: IFile, e: React.MouseEvent) => {
    e.stopPropagation();
    const filename = file.filename.split("/").pop() || "";
    setEditingFile(file.fullPath);
    setEditingName(filename);
  };

  const handleRenameCancel = () => {
    setEditingFile(null);
    setEditingName("");
  };

  const handleRenameSave = async (file: IFile) => {
    if (!editingName.trim() || editingName === file.filename.split("/").pop()) {
      handleRenameCancel();
      return;
    }

    setIsRenaming(true);
    try {
      await ApiService.getInstance().updateFile(file.fullPath, {
        new_filename: editingName.trim(),
      });

      // Refresh file list
      window.location.reload(); // Simple refresh, could be optimized
    } catch (error) {
      console.error("[Sidebar] Error renaming file:", error);
      alert("Error renaming file. Please try again.");
    } finally {
      setIsRenaming(false);
      handleRenameCancel();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, file: IFile) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleRenameSave(file);
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleRenameCancel();
    }
  };

  const isCategory = level === 0;
  const headerClass = isCategory
    ? "category-header"
    : level === 1
      ? "year-header"
      : "month-header";
  const containerClass = isCategory
    ? "category-group"
    : level === 1
      ? "year-group"
      : "month-group";

  // Calculate total files in this node and children
  const countFiles = (n: TreeNode): number => {
    let count = n.files.length;
    Object.values(n.children).forEach((child) => (count += countFiles(child)));
    return count;
  };
  const totalFiles = countFiles(node);

  // Helper to collect all files recursively
  const collectFiles = (n: TreeNode): IFile[] => {
    const files = [...n.files];
    Object.values(n.children).forEach((child) =>
      files.push(...collectFiles(child)),
    );
    return files;
  };

  const allNodeFiles = collectFiles(node);
  const allActive = allNodeFiles.every((f) =>
    activeFiles.some((af) => af.fullPath === f.fullPath),
  );
  const someActive = allNodeFiles.some((f) =>
    activeFiles.some((af) => af.fullPath === f.fullPath),
  );

  const toggleGroup = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    const shouldActivate = !allActive;

    allNodeFiles.forEach((file) => {
      const isActive = activeFiles.some((af) => af.fullPath === file.fullPath);
      if (shouldActivate && !isActive) {
        onToggle(file);
      } else if (!shouldActivate && isActive) {
        onToggle(file);
      }
    });
  };

  const isDropTarget = dragState.dropTarget === node.path;

  return (
    <div className={containerClass}>
      <div
        className={headerClass}
        onClick={toggleOpen}
        onMouseEnter={() => {
          const ids = allNodeFiles.map((f) => f.fullPath);
          onHover(ids);
        }}
        onMouseLeave={() => onHover([])}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (dragState.draggedFile) {
            onDragOver(node.path);
          }
        }}
        onDragLeave={(e) => {
          e.stopPropagation();
          onDragLeave();
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onDrop(node.path);
        }}
        style={{
          backgroundColor: isDropTarget ? "#e3f2fd" : undefined,
          border: isDropTarget ? "2px dashed #2196f3" : undefined,
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <span className={`chevron ${!isOpen ? "collapsed" : ""}`}>▼</span>
          <input
            type="checkbox"
            checked={allActive}
            ref={(input) => {
              if (input) {
                input.indeterminate = someActive && !allActive;
              }
            }}
            onChange={toggleGroup}
            onClick={(e) => e.stopPropagation()}
            style={{ margin: "0 10px", cursor: "pointer" }}
          />
          <span>
            {(() => {
              const categories = ApiService.getInstance().getCategories();
              const config = categories[node.name];
              if (config && config.label) {
                return config.label;
              }
              // Fallback to formatted folder name
              return (
                node.name.charAt(0).toUpperCase() +
                node.name.slice(1).replace(/_/g, " ")
              );
            })()}
          </span>
        </div>
        <span className="group-count">{totalFiles}</span>
      </div>

      {isOpen && (
        <div className="group-content">
          {/* Render Children Directories */}
          {Object.values(node.children)
            .sort((a, b) => b.name.localeCompare(a.name))
            .map((child) => (
              <TreeNodeComponent
                key={child.path}
                node={child}
                activeFiles={activeFiles}
                onToggle={onToggle}
                onSetLocationRequest={onSetLocationRequest}
                onHover={onHover}
                level={level + 1}
                onDragStart={onDragStart}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                dragState={dragState}
                onViewMedia={onViewMedia}
              />
            ))}

          {/* Render Files in this directory */}
          {node.files.map((file) => {
            const isActive = activeFiles.some(
              (f) => f.fullPath === file.fullPath,
            );
            const isMedia = file.type === "media";

            const handleSetLocation = async (e: React.MouseEvent) => {
              e.stopPropagation();
              onSetLocationRequest(file.fullPath);
            };

            return (
              <div
                key={file.fullPath}
                className={`track-item ${isActive ? "active" : ""}`}
                onClick={() => onToggle(file)}
                draggable
                onDragStart={(e) => {
                  e.stopPropagation();
                  onDragStart(file);
                }}
                onDragEnd={(e) => {
                  e.stopPropagation();
                  onDragLeave();
                }}
                style={{
                  marginLeft: `${(level + 1) * 15}px`,
                  display: "flex",
                  alignItems: "center",
                  cursor: dragState.draggedFile === file ? "grabbing" : "grab",
                  opacity: dragState.draggedFile === file ? 0.5 : 1,
                }}
                onMouseEnter={() => onHover([file.fullPath])}
                onMouseLeave={() => onHover([])}
              >
                <input
                  type="checkbox"
                  checked={isActive}
                  readOnly
                  style={{ marginRight: "10px" }}
                />
                {editingFile === file.fullPath ? (
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, file)}
                    onBlur={handleRenameCancel}
                    autoFocus
                    disabled={isRenaming}
                    style={{
                      flex: 1,
                      padding: "2px 4px",
                      border: "1px solid #2196f3",
                      borderRadius: "2px",
                      outline: "none",
                      fontSize: "inherit",
                      fontFamily: "inherit",
                      backgroundColor: isRenaming ? "#f0f0f0" : "white",
                    }}
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <span
                    style={{ flex: 1, cursor: "text" }}
                    onDoubleClick={(e) => handleRenameStart(file, e)}
                    title="Double-click to rename"
                  >
                    {file.filename.split("/").pop()}
                  </span>
                )}
                <a
                  href={ApiService.getInstance().getFileUrl(file)}
                  download
                  onClick={(e) => e.stopPropagation()}
                  title="Download"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    opacity: 0.6,
                    padding: "0 5px",
                    fontSize: "14px",
                    textDecoration: "none",
                  }}
                >
                  ⬇️
                </a>
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    if (
                      window.confirm(
                        `Are you sure you want to delete ${file.filename
                          .split("/")
                          .pop()}?`,
                      )
                    ) {
                      try {
                        await ApiService.getInstance().deleteFile(
                          file.fullPath,
                        );
                        // Refresh file list
                        window.location.reload();
                      } catch (error) {
                        console.error("Error deleting file:", error);
                        alert("Failed to delete file.");
                      }
                    }
                  }}
                  title="Delete"
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    opacity: 0.6,
                    padding: "0 5px",
                    fontSize: "14px",
                  }}
                >
                  🗑️
                </button>
                {isMedia && (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewMedia(file);
                      }}
                      title="View media"
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        opacity: 0.6,
                        padding: "0 5px",
                        fontSize: "14px",
                      }}
                    >
                      👁️
                    </button>
                    <button
                      onClick={handleSetLocation}
                      title="Set Location"
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        opacity: 0.6,
                        padding: "0 5px",
                        fontSize: "14px",
                      }}
                    >
                      📍
                    </button>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  files,
  activeFiles,
  onToggle,
  onUploadComplete,
  onSetLocationRequest,
  onHover,
  onChangeRepository,
}) => {
  const tree = buildTree(files);
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [isResizing, setIsResizing] = useState(false);
  const [dragState, setDragState] = useState<DragState>({
    draggedFile: null,
    dropTarget: null,
  });
  const [viewingMedia, setViewingMedia] = useState<IFile | null>(null);

  const handleDragStart = (file: IFile) => {
    setDragState({ draggedFile: file, dropTarget: null });
  };

  const handleDragOver = (targetPath: string) => {
    setDragState((prev) => ({ ...prev, dropTarget: targetPath }));
  };

  const handleDragLeave = () => {
    setDragState((prev) => ({ ...prev, dropTarget: null }));
  };

  const handleDrop = async (targetPath: string) => {
    const { draggedFile } = dragState;
    if (!draggedFile) return;

    try {
      // Extract target category from path (first part)
      const targetCategory = targetPath.split("/")[0];

      // Extract target folder (everything after category)
      const pathParts = targetPath.split("/");
      const targetFolder =
        pathParts.length > 1 ? pathParts.slice(1).join("/") : undefined;

      console.log(
        `[Sidebar] Moving ${draggedFile.fullPath} to category: ${targetCategory}, folder: ${targetFolder}`,
      );

      await ApiService.getInstance().updateFile(draggedFile.fullPath, {
        target_category: targetCategory,
        target_folder: targetFolder,
      });

      // Refresh file list
      onUploadComplete();
    } catch (error) {
      console.error("[Sidebar] Error moving file:", error);
      alert("Error moving file. Please try again.");
    } finally {
      setDragState({ draggedFile: null, dropTarget: null });
    }
  };

  // Sort categories: Tracks first, then Media, then alphabetical
  const sortedCategories = Object.values(tree).sort((a, b) => {
    const categories = ApiService.getInstance().getCategories();
    const catA = categories[a.name];
    const catB = categories[b.name];

    // If both have config, sort by type
    if (catA && catB) {
      if (catA.type !== catB.type) {
        return catA.type === "track" ? -1 : 1;
      }
    }

    // If one has config and other doesn't (shouldn't happen for top level), prioritize config
    if (catA && !catB) return -1;
    if (!catA && catB) return 1;

    // Default to alphabetical
    return a.name.localeCompare(b.name);
  });

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  };

  React.useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = e.clientX;
      // Constrain width between 200px and 600px
      if (newWidth >= 200 && newWidth <= 600) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing]);

  return (
    <div className="sidebar" style={{ width: `${sidebarWidth}px` }}>
      <div
        className={`resizer ${isResizing ? "resizing" : ""}`}
        onMouseDown={handleMouseDown}
      />
      <div className="logo-container">
        <h2>Ouffroad</h2>
        <button
          onClick={onChangeRepository}
          className="switch-repo-btn"
          title="Switch Repository"
        >
          🔄
        </button>
      </div>
      <Upload onUploadComplete={onUploadComplete} />
      <div className="track-list">
        {sortedCategories.map((node) => (
          <TreeNodeComponent
            key={node.path}
            node={node}
            activeFiles={activeFiles}
            onToggle={onToggle}
            onSetLocationRequest={onSetLocationRequest}
            onHover={onHover}
            level={0}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            dragState={dragState}
            onViewMedia={(file) => setViewingMedia(file)}
          />
        ))}
      </div>

      {/* Media Viewer Modal */}
      {viewingMedia && (
        <MediaViewer
          file={viewingMedia}
          allMediaFiles={files.filter((f) => f.type === "media")}
          onClose={() => setViewingMedia(null)}
          onNavigate={(file) => setViewingMedia(file)}
        />
      )}
    </div>
  );
};
