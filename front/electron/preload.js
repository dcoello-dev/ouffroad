const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    selectRepository: () => ipcRenderer.invoke('select-repository'),
});
