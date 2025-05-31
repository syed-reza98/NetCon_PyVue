import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import kill from 'tree-kill'

const currentDir = fileURLToPath(new URL('.', import.meta.url))

let mainWindow = null
let pythonProcess = null
const devBackendPath = path.resolve("src-electron/python/app.exe")
const prodBackendPath = path.join(process.resourcesPath, "..", "python", "app.exe")

let exePath = process.env.DEV ? devBackendPath : prodBackendPath

function startPythonProcess() {
  if (pythonProcess) {
    console.log('Python process already running with PID:', pythonProcess.pid);
    return;
  }

  console.log('Starting Python process...');
  // Use detached: false to ensure process is part of parent's process group
  pythonProcess = spawn(exePath, [], {
    detached: false,
    windowsHide: true
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python Output: ${data}`);
  });

  pythonProcess.stderr.on('data', (errorData) => {
    console.error(`Python Error: ${errorData}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    pythonProcess = null;
  });

  console.log(`Python process started with PID: ${pythonProcess.pid}`);
}

function terminatePythonProcess() {
  if (pythonProcess && pythonProcess.pid) {
    console.log(`Terminating Python process tree with PID: ${pythonProcess.pid}`);
    try {
      // Kill the entire process tree
      kill(pythonProcess.pid, 'SIGTERM', (err) => {
        if (err) {
          console.error('Error terminating Python process tree:', err);
          // Fallback to force kill if needed
          try {
            kill(pythonProcess.pid, 'SIGKILL');
          } catch (killError) {
            console.error('Failed to force kill Python process:', killError);
          }
        } else {
          console.log('Python process tree terminated successfully');
        }
      });
    } catch (error) {
      console.error('Exception during Python process termination:', error);
    }
  } else {
    console.log('No Python process to terminate');
  }
}

// Rest of your code remains unchanged

app.on('ready', () => {
  console.log('Electron app ready, creating window...');

  mainWindow = new BrowserWindow({
    icon: path.resolve(currentDir, 'icons/icon.png'), // tray icon
    width: 1000,
    height: 600,
    useContentSize: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.resolve(
        currentDir,
        path.join(process.env.QUASAR_ELECTRON_PRELOAD_FOLDER, 'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION)
      ),
    },
  });

  if (process.env.DEV) {
    mainWindow.loadURL(process.env.APP_URL);
    console.log('Development mode: Loading from', process.env.APP_URL);
  } else {
    mainWindow.loadFile('index.html');
    console.log('Production mode: Loading from index.html');
  }

  if (process.env.DEBUGGING) {
    mainWindow.webContents.openDevTools();
    console.log('Debugging enabled: DevTools opened');
  } else {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
  }

  // Start the Python process only once
  startPythonProcess();

  mainWindow.on('closed', () => {
    console.log('Main window closed');
    mainWindow = null;

    // Don't terminate Python here - wait for app quit
    // This prevents premature termination if the user reopens a window
  });
});

app.on("window-all-closed", () => {
  console.log("All windows closed");
  process.platform !== "darwin" && app.quit();
});

// Make sure will-quit properly handles our termination
app.on('will-quit', (event) => {
  console.log('Application will quit, cleaning up resources...');

  // Use a synchronous approach to ensure termination completes
  if (pythonProcess && pythonProcess.pid) {
    event.preventDefault();
    terminatePythonProcess();

    // Give some time for the process to terminate before quitting
    setTimeout(() => {
      app.quit();
    }, 500);
  }
});

// Remove redundant termination from quit event, as will-quit handles it
app.on('quit', () => {
  console.log('Application quit event triggered');
  // No need to call terminatePythonProcess() again
});

// Keep your uncaughtException handler
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  terminatePythonProcess();
});
