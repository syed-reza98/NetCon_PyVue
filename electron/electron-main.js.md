import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'node:path'
import os from 'node:os'
import { fileURLToPath } from 'node:url'
import fs from 'node:fs'
import { spawn, exec } from 'node:child_process'

// needed in case process is undefined under Linux
const platform = process.platform || os.platform()

const currentDir = fileURLToPath(new URL('.', import.meta.url))

let mainWindow
let pythonProcess = null

// Helper function to get the path to the Python executable
function getPythonBackendPath() {
  const pythonExe = process.env.PYTHON_EXECUTABLE || 'app.exe'
  const pythonArgs = process.env.PYTHON_ARGS || '--headless'

  // During development
  if (process.env.DEV) {
    const devPath = path.join(path.dirname(currentDir), '../backend', pythonExe)
    console.log(`Development backend path: ${devPath}`)
    return {
      execPath: devPath,
      args: pythonArgs.split(' ').filter(arg => arg !== '')
    }
  }

  // In production - use the resources directory
  const prodPath = path.join(process.resourcesPath, '../backend', pythonExe)
  console.log(`Production backend path: ${prodPath}`)
  return {
    execPath: prodPath,
    args: pythonArgs.split(' ').filter(arg => arg !== '')
  }
}

// Start the Python backend process
function startPythonBackend() {
  if (pythonProcess) {
    console.log('Python process already running')
    return
  }

  const { execPath, args } = getPythonBackendPath()

  // Check if the executable exists
  if (!fs.existsSync(execPath)) {
    console.error(`Python executable not found at: ${execPath}`)
    app.exit(1)
    return
  }

  try {
    // Use direct spawn instead of utility process for simplicity
    // const { spawn } = require('child_process')
    pythonProcess = spawn(execPath, args)
    console.log(`Python process started with PID: ${pythonProcess.pid}`)

    // Set up standard I/O handling
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log(`Python stdout: ${output}`)
      // Forward to renderer if needed
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('python-output', output)
      }
    })

    pythonProcess.stderr.on('data', (data) => {
      const output = data.toString()
      console.error(`Python stderr: ${output}`)
      // Forward to renderer if needed
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('python-error', output)
      }
    })

    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`)
      pythonProcess = null
      // 


      // Restart the process if it crashed and we're not shutting down
      if (code !== 0 && !app.isQuitting) {
        setTimeout(() => {
          console.log('Attempting to restart Python process after exit...')
          startPythonBackend()
        }, 5000)
      }
    })

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process:', err)
      pythonProcess = null

      // Try to restart after a delay if we're not shutting down
      if (!app.isQuitting) {
        setTimeout(() => {
          console.log('Attempting to restart Python backend...')
          startPythonBackend()
        }, 5000)
      }
    })
  } catch (error) {
    console.error('Error starting Python backend:', error)
  }
}

// Stop the Python backend process
function stopPythonBackend() {
  // If there's no process to stop, return immediately
  if (!pythonProcess) {
    return Promise.resolve();
  }
  
  console.log('Stopping Python backend...');
  
  // Create a local reference to the process and immediately set the global to null
  // This prevents multiple termination attempts on the same process
  const processToStop = pythonProcess;
  pythonProcess = null;

  // Windows-specific process termination
  if (platform === 'win32') {
    try {
      // First attempt graceful termination
      if (processToStop.stdin) {
        try {
          processToStop.stdin.end();
        } catch (err) {
          console.error('Error ending stdin:', err);
        }
      }
      
      // Create a promise that will resolve when the process exits
      return new Promise((resolve) => {
        // Set a short timeout for graceful exit
        const exitTimeout = setTimeout(() => {
          console.log('Python process did not exit gracefully, forcing termination...');
          
          // Check if the process is still running before using taskkill
          try {
            // Use process.kill with 0 signal to check if process exists
            // This will throw an error if the process doesn't exist
            process.kill(processToStop.pid, 0);
            
            // If we get here, the process exists, so try to kill it
            exec(`taskkill /pid ${processToStop.pid} /T /F`, (error) => {
              if (error) {
                console.error('Error using taskkill:', error);
              }
              resolve();
            });
          } catch (err) {
            // Process doesn't exist anymore
            console.log('Process already terminated', err);
            resolve();
          }
        }, 2000); // Give the process 2 seconds to exit gracefully

        // If the process exits on its own, clear the timeout
        const exitHandler = () => {
          clearTimeout(exitTimeout);
          resolve();
        };
        
        processToStop.once('exit', exitHandler);
        
        // Send SIGTERM first for a graceful exit attempt
        try {
          processToStop.kill('SIGTERM');
        } catch (err) {
          console.error('Error sending SIGTERM:', err);
          clearTimeout(exitTimeout);
          resolve();
        }
      });
    } catch (e) {
      console.error('Error terminating Python process:', e);
      return Promise.resolve();
    }
  } else {
    // For non-Windows platforms
    try {
      processToStop.kill();
    } catch (err) {
      console.error('Error killing process:', err);
    }
    return Promise.resolve();
  }
}

// Communication with Python backend
function sendToPythonBackend(data) {
  if (pythonProcess && pythonProcess.stdin) {
    const message = typeof data === 'string' ? data : JSON.stringify(data)
    pythonProcess.stdin.write(message + '\n')
    return true
  }
  console.error('Cannot send message: Python backend not running or stdin not available')
  return false
}

async function createWindow() {
  /**
   * Initial window options
   */
  mainWindow = new BrowserWindow({
    icon: path.resolve(currentDir, 'icons/icon.png'), // tray icon
    width: 1000,
    height: 600,
    useContentSize: true,
    webPreferences: {
      contextIsolation: true,
      // More info: https://v2.quasar.dev/quasar-cli-vite/developing-electron-apps/electron-preload-script
      preload: path.resolve(
        currentDir,
        path.join(
          process.env.QUASAR_ELECTRON_PRELOAD_FOLDER,
          'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION,
        ),
      ),
    },
  })

  if (process.env.DEV) {
    await mainWindow.loadURL(process.env.APP_URL)
  } else {
    await mainWindow.loadFile('index.html')
  }

  if (process.env.DEBUGGING) {
    // if on DEV or Production with debug enabled
    mainWindow.webContents.openDevTools()
  } else {
    // we're on production; no access to devtools pls
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools()
    })
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// Set up IPC handlers for renderer process to communicate with Python
function setupIpcHandlers() {
  // Handle messages from the renderer process
  ipcMain.handle('python-send', (event, data) => {
    return sendToPythonBackend(data)
  })

  ipcMain.handle('python-restart', () => {
    stopPythonBackend()
    startPythonBackend()
    return true
  })

  // Add status check handler
  ipcMain.handle('python-status', () => {
    return !!pythonProcess
  })
}

// Initialize the app
app.whenReady().then(() => {
  // Set flag to track if we're shutting down
  app.isQuitting = false

  // Set up IPC handlers
  setupIpcHandlers()

  // Create the browser window
  createWindow()

  // Start Python backend after window is created
  startPythonBackend()
})

// Clean up when app is quitting - this should only be triggered once
let isQuitting = false;

app.on('will-quit', (event) => {
  // Prevent multiple quit attempts
  if (isQuitting) return;
  isQuitting = true;
  
  // Set flag indicating we're shutting down
  app.isQuitting = true;
  
  // Prevent the app from quitting until we've stopped the Python process
  event.preventDefault();
  
  // Stop the Python process and then quit the app
  stopPythonBackend().then(() => {
    // Now it's safe to quit
    app.quit();
  }).catch(err => {
    console.error('Error during shutdown:', err);
    app.quit();
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (platform !== 'darwin') {
    // Do not set isQuitting flag here, as will-quit will be triggered next
    app.isQuitting = true;
    app.quit();
  }
});

// Simplified exit handler
process.on('exit', () => {
  console.log('Process exit handler triggered');
  // No need to do anything here as will-quit should have handled cleanup
});

// Handle unhandled exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
})