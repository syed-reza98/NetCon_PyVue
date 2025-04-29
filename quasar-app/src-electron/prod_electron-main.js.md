// import{app as t,BrowserWindow as a}from"electron";import r from"node:path";import{spawn as d}from"node:child_process";import{fileURLToPath as h}from"node:url";import s from"tree-kill";var l=h(new URL(".",import.meta.url)),n=null,o=null,v=r.resolve("src-electron/python/app.exe"),u=r.join(process.resourcesPath,"..","python","app.exe"),i=u;function P(){if(o){console.log("Python process already running with PID:",o.pid);return}console.log("Python executable path:",i),console.log("Starting Python process..."),o=d(i,[],{detached:!1,windowsHide:!0}),o.stdout.on("data",e=>{console.log(`Python Output: ${e}`)}),o.stderr.on("data",e=>{console.error(`Python Error: ${e}`)}),o.on("close",e=>{console.log(`Python process exited with code ${e}`),o=null}),console.log(`Python process started with PID: ${o.pid}`)}function c(){if(o&&o.pid){console.log(`Terminating Python process tree with PID: ${o.pid}`);try{s(o.pid,"SIGTERM",e=>{if(e){console.error("Error terminating Python process tree:",e);try{s(o.pid,"SIGKILL")}catch(p){console.error("Failed to force kill Python process:",p)}}else console.log("Python process tree terminated successfully")})}catch(e){console.error("Exception during Python process termination:",e)}}else console.log("No Python process to terminate")}t.on("ready",()=>{console.log("Electron app ready, creating window..."),n=new a({icon:r.resolve(l,"icons/icon.png"),width:1e3,height:600,useContentSize:!0,webPreferences:{contextIsolation:!0,preload:r.resolve(l,r.join("preload","electron-preload.cjs"))}}),n.loadFile("index.html"),console.log("Production mode: Loading from index.html"),n.webContents.on("devtools-opened",()=>{n.webContents.closeDevTools()}),P(),n.on("closed",()=>{console.log("Main window closed"),n=null})});t.on("window-all-closed",()=>{console.log("All windows closed"),process.platform!=="darwin"&&t.quit()});t.on("will-quit",e=>{console.log("Application will quit, cleaning up resources..."),o&&o.pid&&(e.preventDefault(),c(),setTimeout(()=>{t.quit()},500))});t.on("quit",()=>{console.log("Application quit event triggered")});process.on("uncaughtException",e=>{console.error("Uncaught exception:",e),c()});


import { app, BrowserWindow } from "electron";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import treeKill from "tree-kill";

var currentDir = fileURLToPath(new URL(".", import.meta.url)),
    mainWindow = null,
    pythonProcess = null,
    devPythonPath = path.resolve("src-electron/python/app.exe"),
    prodPythonPath = path.join(process.resourcesPath, "..", "python", "app.exe"),
    pythonExePath = prodPythonPath;

function startPythonProcess() {
    if (pythonProcess) {
        console.log("Python process already running with PID:", pythonProcess.pid);
        return;
    }
    console.log("Python executable path:", pythonExePath);
    console.log("Starting Python process...");
    pythonProcess = spawn(pythonExePath, [], {
        detached: false,
        windowsHide: true
    });
    pythonProcess.stdout.on("data", data => {
        console.log(`Python Output: ${data}`);
    });
    pythonProcess.stderr.on("data", errorData => {
        console.error(`Python Error: ${errorData}`);
    });
    pythonProcess.on("close", exitCode => {
        console.log(`Python process exited with code ${exitCode}`);
        pythonProcess = null;
    });
    console.log(`Python process started with PID: ${pythonProcess.pid}`);
}

function terminatePythonProcess() {
    if (pythonProcess && pythonProcess.pid) {
        console.log(`Terminating Python process tree with PID: ${pythonProcess.pid}`);
        try {
            treeKill(pythonProcess.pid, "SIGTERM", error => {
                if (error) {
                    console.error("Error terminating Python process tree:", error);
                    try {
                        treeKill(pythonProcess.pid, "SIGKILL");
                    } catch (killError) {
                        console.error("Failed to force kill Python process:", killError);
                    }
                } else {
                    console.log("Python process tree terminated successfully");
                }
            });
        } catch (terminationError) {
            console.error("Exception during Python process termination:", terminationError);
        }
    } else {
        console.log("No Python process to terminate");
    }
}

app.on("ready", () => {
    console.log("Electron app ready, creating window...");
    mainWindow = new BrowserWindow({
        icon: path.resolve(currentDir, "icons/icon.png"),
        width: 1000,
        height: 600,
        useContentSize: true,
        webPreferences: {
            contextIsolation: true,
            preload: path.resolve(currentDir, path.join("preload", "electron-preload.cjs"))
        }
    });
    mainWindow.loadFile("index.html");
    console.log("Production mode: Loading from index.html");
    mainWindow.webContents.on("devtools-opened", () => {
        mainWindow.webContents.closeDevTools();
    });
    startPythonProcess();
    mainWindow.on("closed", () => {
        console.log("Main window closed");
        mainWindow = null;
    });
});

app.on("window-all-closed", () => {
    console.log("All windows closed");
    process.platform !== "darwin" && app.quit();
});

app.on("will-quit", event => {
    console.log("Application will quit, cleaning up resources...");
    if (pythonProcess && pythonProcess.pid) {
        event.preventDefault();
        terminatePythonProcess();
        setTimeout(() => {
            app.quit();
        }, 500);
    }
});

app.on("quit", () => {
    console.log("Application quit event triggered");
});

process.on("uncaughtException", error => {
    console.error("Uncaught exception:", error);
    terminatePythonProcess();
});
