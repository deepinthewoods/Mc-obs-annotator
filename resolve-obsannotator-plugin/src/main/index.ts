import { app, BrowserWindow, dialog, ipcMain, powerSaveBlocker } from 'electron';
import { execFile } from 'child_process';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;
let powerSaveBlockerId: number | null = null;
let sleepPreventionInterval: ReturnType<typeof setInterval> | null = null;

/**
 * On Windows, Electron's powerSaveBlocker has a known bug where it fails to
 * prevent sleep when the app loses focus. As a workaround, we periodically
 * call SetThreadExecutionState via PowerShell to reset the system idle timer.
 */
function resetSystemIdleTimer(): void {
  if (process.platform !== 'win32') return;
  execFile('powershell.exe', [
    '-NoProfile', '-NonInteractive', '-Command',
    `Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class SP { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f); }'; [SP]::SetThreadExecutionState(0x00000003)`
  ], (err) => {
    if (err) console.error('Failed to reset idle timer:', err.message);
  });
}

function startSleepPrevention(): void {
  if (sleepPreventionInterval !== null) return;
  // Reset idle timer immediately, then every 30 seconds
  resetSystemIdleTimer();
  sleepPreventionInterval = setInterval(resetSystemIdleTimer, 30000);
}

function stopSleepPrevention(): void {
  if (sleepPreventionInterval !== null) {
    clearInterval(sleepPreventionInterval);
    sleepPreventionInterval = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 900,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    backgroundColor: '#1e1e1e',
    title: 'ObsAnnotator - DaVinci Resolve Companion',
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  ipcMain.handle('select-directory', async () => {
    if (!mainWindow) return undefined;
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
    });
    if (result.canceled || result.filePaths.length === 0) return undefined;
    return result.filePaths[0];
  });

  ipcMain.handle('prevent-sleep', () => {
    if (powerSaveBlockerId === null) {
      powerSaveBlockerId = powerSaveBlocker.start('prevent-display-sleep');
    }
    startSleepPrevention();
    return powerSaveBlockerId;
  });

  ipcMain.handle('allow-sleep', () => {
    if (powerSaveBlockerId !== null && powerSaveBlocker.isStarted(powerSaveBlockerId)) {
      powerSaveBlocker.stop(powerSaveBlockerId);
    }
    powerSaveBlockerId = null;
    stopSleepPrevention();
  });

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
