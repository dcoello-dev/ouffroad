import React, { useState } from "react";
import type { IFile } from "../models/File";
import { Upload } from "./Upload";
import { ApiService } from "../services/ApiService";

interface SidebarProps {
  files: IFile[];
  activeFiles: IFile[];
  onToggle: (file: IFile) => void;
  onUploadComplete: () => void;
  onSetLocationRequest: (filePath: string) => void;
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
  level: number;
}

const TreeNodeComponent: React.FC<TreeNodeProps> = ({
  node,
  activeFiles,
  onToggle,
  onSetLocationRequest,
  level,
}) => {
  const [isOpen, setIsOpen] = useState(level === 0); // Open top level by default

  const toggleOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
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

  return (
    <div className={containerClass}>
      <div className={headerClass} onClick={toggleOpen}>
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
          <span>{node.name.toUpperCase()}</span>
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
                level={level + 1}
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
                onClick={(e) => {
                  e.stopPropagation();
                  onToggle(file);
                }}
                style={{
                  marginLeft: `${(level + 1) * 15}px`,
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <input
                  type="checkbox"
                  checked={isActive}
                  readOnly
                  style={{ marginRight: "10px" }}
                />
                <span style={{ flex: 1 }}>
                  {file.filename.split("/").pop()}
                </span>
                {isMedia && (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        const repoBaseUrl =
                          ApiService.getInstance().getRepoBaseUrl();
                        window.open(
                          `${repoBaseUrl}/${file.fullPath}`,
                          "_blank",
                        );
                      }}
                      title="Open in new tab"
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        opacity: 0.6,
                        padding: "0 5px",
                        fontSize: "14px",
                      }}
                    >
                      🔗
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
}) => {
  const tree = buildTree(files);
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [isResizing, setIsResizing] = useState(false);

  // Custom sort order for categories if needed, or just alphabetical
  const sortedCategories = Object.values(tree).sort((a, b) => {
    const order = ["trail", "enduro", "special_events", "media"];
    const idxA = order.indexOf(a.name.toLowerCase());
    const idxB = order.indexOf(b.name.toLowerCase());
    if (idxA !== -1 && idxB !== -1) return idxA - idxB;
    if (idxA !== -1) return -1;
    if (idxB !== -1) return 1;
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
            level={0}
          />
        ))}
      </div>
    </div>
  );
};
