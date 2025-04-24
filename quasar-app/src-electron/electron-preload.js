/**
 * This file is used specifically for security reasons.
 * Here you can access Nodejs stuff and inject functionality into
 * the renderer thread (accessible there through the "window" object)
 *
 * WARNING!
 * If you import anything from node_modules, then make sure that the package is specified
 * in package.json > dependencies and NOT in devDependencies
 *
 * Example (injects window.myAPI.doAThing() into renderer thread):
 *
 *   import { contextBridge } from 'electron'
 *
 *   contextBridge.exposeInMainWorld('myAPI', {
 *     doAThing: () => {}
 *   })
 *
 * WARNING!
 * If accessing Node functionality (like importing @electron/remote) then in your
 * electron-main.js you will need to set the following when you instantiate BrowserWindow:
 *
 * mainWindow = new BrowserWindow({
 *   // ...
 *   webPreferences: {
 *     // ...
 *     sandbox: false // <-- to be able to import @electron/remote in preload script
 *   }
 * }
 */

// import { app, BrowserWindow, ipcMain, utilityProcess } from 'electron'
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
    sendToPython: (data) => ipcRenderer.invoke('python-send', data),
    restartPython: () => ipcRenderer.invoke('python-restart'),
    onPythonOutput: (callback) => {
        ipcRenderer.on('python-output', (event, data) => callback(data));
        return () => ipcRenderer.removeAllListeners('python-output');
    },
    onPythonError: (callback) => {
        ipcRenderer.on('python-error', (event, data) => callback(data));
        return () => ipcRenderer.removeAllListeners('python-error');
    }
})