 ```javascript

import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import os from 'node:os'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import fs from 'node:fs'

// const __filename = fileURLToPath(import.meta.url)

// needed in case process is undefined under Linux
const platform = process.platform || os.platform()

const devBackendPath = path.resolve(process.cwd(), 'backend', 'app.exe')
// Update this path to match where your app.exe is actually located
const prodBackendPath = process.env.PROD
  ? path.join(process.resourcesPath, 'backend', 'app.exe') // Look in the /backend subfolder
  : path.join(__dirname, '..', '..', 'backend', 'app.exe')
let exePath = process.env.DEV ? devBackendPath : prodBackendPath

const currentDir = fileURLToPath(new URL('.', import.meta.url))

let mainWindow
let pythonProcess //Moved to top-level scope

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
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools()
    })
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function startPythonBackend() {
  console.log('Starting backend...')
  console.log('Current directory:', process.cwd())
  console.log('Resources path:', process.resourcesPath)
  console.log('Looking for backend at:', exePath)

  if (!fs.existsSync(exePath)) {
    console.error('Backend executable not found at:', exePath)
    // Try to find it in nearby locations
    const possibleLocations = [
      path.join(process.resourcesPath, 'backend', 'app.exe'),
      path.join(process.resourcesPath, 'app', 'backend', 'app.exe'),
      path.join(process.resourcesPath, 'app.asar.unpacked', 'backend', 'app.exe'),
    ]

    console.log('Checking alternative locations...')
    for (const loc of possibleLocations) {
      console.log('Checking:', loc)
      if (fs.existsSync(loc)) {
        console.log('Found backend at alternative location:', loc)
        // Use this path instead
        exePath = loc
        break
      }
    }

    if (!fs.existsSync(exePath)) {
      console.error('Could not find backend executable anywhere')
      return
    }
  }

  console.log('app.exe found at:', exePath)

  try {
    // For Windows paths with spaces, use this approach
    pythonProcess = spawn(exePath, [], {
      stdio: 'pipe', // Changed from 'inherit' to 'pipe' to allow reading output
      shell: true,
      windowsHide: true,
      cwd: path.dirname(exePath), // Set working directory to executable location
    })

    // Add this to your startPythonBackend function after the spawn call
    console.log('Process environment:', {
      PROD: process.env.PROD,
      DEV: process.env.DEV,
      resourcesPath: process.resourcesPath,
    })

    // Also inspect the pythonProcess object
    console.log('Python process details:', {
      pid: pythonProcess?.pid,
      killed: pythonProcess?.killed,
      connected: pythonProcess?.connected,
    })

    // Check if process was created successfully
    if (!pythonProcess) {
      console.error('Failed to create process')
      return
    }

    console.log('Backend process started with PID:', pythonProcess.pid)

    // Set up error handler
    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process:', err)
    })

    // Set up exit handler
    pythonProcess.on('exit', (code, signal) => {
      console.log(`Python process exited with code ${code} and signal ${signal}`)
    })

    // Set up stdout handler
    if (pythonProcess.stdout) {
      pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data.toString().trim()}`)
      })
    }

    // Set up stderr handler
    if (pythonProcess.stderr) {
      pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data.toString().trim()}`)
      })
    }
  } catch (error) {
    console.error('Error starting Python backend:', error)
  }
}

// Function to stop the Python backend
function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

app.whenReady().then(() => {
  startPythonBackend() // Start the Python backend
  createWindow()
})

app.on('window-all-closed', () => {
  if (pythonProcess) stopPythonBackend()
  if (platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})





// Edited 



import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import os from 'node:os'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import fs from 'node:fs'

// needed in case process is undefined under Linux
const platform = process.platform || os.platform()

const devBackendPath = path.resolve(process.cwd(), 'backend', 'app.exe')
// Update this path to match where your app.exe is actually located
const prodBackendPath = process.env.PROD
  ? path.join(process.resourcesPath, 'backend', 'app.exe') // Look in the /backend subfolder
  : path.join(__dirname, '..', '..', 'backend', 'app.exe')
let exePath = process.env.DEV ? devBackendPath : prodBackendPath

const currentDir = fileURLToPath(new URL('.', import.meta.url))

let mainWindow
let pythonProcess

async function createWindow () {
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
        path.join(process.env.QUASAR_ELECTRON_PRELOAD_FOLDER, 'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION)
      )
    }
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
    pythonProcess.kill()
    pythonProcess = null
    mainWindow = null
  })
}

function startPythonBackend() {
  console.log('Starting backend...')
  console.log('Current directory:', process.cwd())
  console.log('Resources path:', process.resourcesPath)
  console.log('Looking for backend at:', exePath)

  if (!fs.existsSync(exePath)) {
    console.error('Backend executable not found at:', exePath)
    // Try to find it in nearby locations
    const possibleLocations = [
      path.join(process.resourcesPath, 'backend', 'app.exe'),
      path.join(process.resourcesPath, 'app', 'backend', 'app.exe'),
      path.join(process.resourcesPath, 'app.asar.unpacked', 'backend', 'app.exe'),
    ]

    console.log('Checking alternative locations...')
    for (const loc of possibleLocations) {
      console.log('Checking:', loc)
      if (fs.existsSync(loc)) {
        console.log('Found backend at alternative location:', loc)
        // Use this path instead
        exePath = loc
        break
      }
    }

    if (!fs.existsSync(exePath)) {
      console.error('Could not find backend executable anywhere')
      return
    }
  }

  console.log('app.exe found at:', exePath)

  try {
    // For Windows paths with spaces, use this approach
    pythonProcess = spawn(exePath, [], {
      stdio: 'pipe', // Changed from 'inherit' to 'pipe' to allow reading output
      shell: true,
      windowsHide: true,
      cwd: path.dirname(exePath), // Set working directory to executable location
    })

    // Add this to your startPythonBackend function after the spawn call
    console.log('Process environment:', {
      PROD: process.env.PROD,
      DEV: process.env.DEV,
      resourcesPath: process.resourcesPath,
    })

    // Also inspect the pythonProcess object
    console.log('Python process details:', {
      pid: pythonProcess?.pid,
      killed: pythonProcess?.killed,
      connected: pythonProcess?.connected,
    })

    // Check if process was created successfully
    if (!pythonProcess) {
      console.error('Failed to create process')
      return
    }

    console.log('Backend process started with PID:', pythonProcess.pid)

    // Set up error handler
    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process:', err)
    })

    // Set up exit handler
    pythonProcess.on('exit', (code, signal) => {
      console.log(`Python process exited with code ${code} and signal ${signal}`)
    })

    // Set up stdout handler
    if (pythonProcess.stdout) {
      pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data.toString().trim()}`)
      })
    }

    // Set up stderr handler
    if (pythonProcess.stderr) {
      pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data.toString().trim()}`)
      })
    }
  } catch (error) {
    console.error('Error starting Python backend:', error)
  }
}

// Function to stop the Python backend
function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

app.whenReady().then(() => {
  startPythonBackend() // Start the Python backend
  createWindow()
})

app.on('window-all-closed', () => {
  if (platform !== 'darwin') {
    if (pythonProcess) {
      pythonProcess.kill() // Kill the Python backend process
    }
    stopPythonBackend() // Stop the Python backend
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})


app.on('will-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});