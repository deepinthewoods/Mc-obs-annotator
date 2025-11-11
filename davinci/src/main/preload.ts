import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', {
  openFileDialog: (options: any) => ipcRenderer.invoke('open-file-dialog', options),
  fileExists: (filePath: string) => ipcRenderer.invoke('file-exists', filePath),
});
