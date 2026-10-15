const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onGlobalMouseMove: (callback) => ipcRenderer.on('global-mousemove', (_event, value) => callback(value)),
  onGlobalKeyDown: (callback) => ipcRenderer.on('global-keydown', (_event, value) => callback(value)),
  onGlobalWheel: (callback) => ipcRenderer.on('global-wheel', (_event, value) => callback(value)),
  onAiStatus: (callback) => ipcRenderer.on('ai-status', (_event, value) => callback(value)),
  onAiMessage: (callback) => ipcRenderer.on('ai-message', (_event, value) => callback(value)),
  setIgnoreMouseEvents: (ignore, options) => ipcRenderer.send('set-ignore-mouse-events', ignore, options)
});
