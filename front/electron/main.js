const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // In dev mode, we might want to use the React dev server (5173) for HMR
    // But for "production-like" testing with the binary, we should use the backend (8000)
    // which serves the built frontend.
    const startUrl = process.env.ELECTRON_START_URL || 'http://localhost:8000';

    const loadWindow = () => {
        mainWindow.loadURL(startUrl).catch(err => {
            console.log(`Server not ready yet, retrying... (${err.code})`);
            setTimeout(loadWindow, 1000);
        });
    };

    loadWindow();

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

function startPythonBackend() {
    // For Phase 1 (Dev Mode), we assume the python environment is set up
    // and we run 'python -m ouffroad' from the root
    const rootDir = path.resolve(__dirname, '../../');

    console.log('Starting Python backend from:', rootDir);

    // Check for PyInstaller binary first (Phase 2 & 3)
    const binaryName = process.platform === 'win32' ? 'ouffroad.exe' : 'ouffroad';

    // Check in resources (Packaged app)
    // In packaged app, resources are in process.resourcesPath
    // We configured extraResources to put it in bin/
    const packagedBinaryPath = path.join(process.resourcesPath, 'bin', binaryName);

    // Check in dist (Dev mode with local binary)
    const devBinaryPath = path.join(rootDir, 'dist', binaryName);

    let binaryPath = null;
    if (require('fs').existsSync(packagedBinaryPath)) {
        binaryPath = packagedBinaryPath;
        console.log('Found packaged binary at:', binaryPath);
    } else if (require('fs').existsSync(devBinaryPath)) {
        binaryPath = devBinaryPath;
        console.log('Found dev binary at:', binaryPath);
    }

    if (binaryPath) {
        pythonProcess = spawn(binaryPath, [], {
            cwd: rootDir, // This might need adjustment for packaged app, but binary should handle it
            stdio: 'inherit',
        });
    } else {
        console.log('Binary not found, falling back to python source');
        // Use the virtual environment python if available, otherwise system python
        const venvPython = path.join(rootDir, '.venv', 'bin', 'python');
        const pythonCmd = require('fs').existsSync(venvPython) ? venvPython : 'python3';

        pythonProcess = spawn(pythonCmd, ['-m', 'ouffroad'], {
            cwd: rootDir,
            env: {
                ...process.env,
                PYTHONPATH: path.join(rootDir, 'src'),
            },
            stdio: 'inherit', // Pipe output to console
        });
    }

    pythonProcess.on('error', (err) => {
        console.error('Failed to start Python process:', err);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });
}

app.on('ready', () => {
    startPythonBackend();
    createWindow();
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

// IPC Handlers
ipcMain.handle('select-repository', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
    });

    if (result.canceled) {
        return null;
    } else {
        return result.filePaths[0];
    }
});
