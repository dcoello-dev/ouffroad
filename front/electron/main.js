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
    const rootDir = path.resolve(__dirname, '../../');
    console.log('Starting Python backend from:', rootDir);

    const binaryName = process.platform === 'win32' ? 'ouffroad.exe' : 'ouffroad';
    const packagedBinaryPath = path.join(process.resourcesPath, 'bin', binaryName);
    const devBinaryPath = path.join(rootDir, 'dist', binaryName);

    let binaryPath = null;
    if (require('fs').existsSync(packagedBinaryPath)) {
        binaryPath = packagedBinaryPath;
        console.log('Found packaged binary at:', binaryPath);
    } else if (require('fs').existsSync(devBinaryPath)) {
        binaryPath = devBinaryPath;
        console.log('Found dev binary at:', binaryPath);
    }

    // Setup logging
    const logPath = path.join(app.getPath('userData'), 'ouffroad-backend.log');
    const logStream = require('fs').createWriteStream(logPath, { flags: 'a' });
    console.log('Logging Python output to:', logPath);

    // Write a separator
    logStream.write(`\n\n--- Starting Ouffroad Backend at ${new Date().toISOString()} ---\n`);

    if (binaryPath) {
        // Ensure CWD is valid. In packaged app, rootDir might be inside ASAR or just resources.
        // Safe bet is resourcesPath or userData.
        // Let's use resourcesPath as CWD for the binary.
        const cwd = process.resourcesPath;

        pythonProcess = spawn(binaryPath, [], {
            cwd: cwd,
            stdio: ['ignore', 'pipe', 'pipe'], // Pipe stdout/stderr
            windowsHide: true // Hide console window on Windows
        });
    } else {
        console.log('Binary not found, falling back to python source');
        const venvPython = path.join(rootDir, '.venv', 'bin', 'python');
        const pythonCmd = require('fs').existsSync(venvPython) ? venvPython : 'python3';

        pythonProcess = spawn(pythonCmd, ['-m', 'ouffroad'], {
            cwd: rootDir,
            env: {
                ...process.env,
                PYTHONPATH: path.join(rootDir, 'src'),
            },
            stdio: ['ignore', 'pipe', 'pipe'],
        });
    }

    if (pythonProcess) {
        pythonProcess.stdout.pipe(logStream);
        pythonProcess.stderr.pipe(logStream);

        pythonProcess.on('error', (err) => {
            console.error('Failed to start Python process:', err);
            logStream.write(`Failed to start Python process: ${err}\n`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            logStream.write(`Python process exited with code ${code}\n`);
        });
    }
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
