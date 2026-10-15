const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const { uIOhook, UiohookKey } = require('uiohook-napi');
const express = require('express');

let mainWindow;

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const catWidth = 300;
  const catHeight = 300;

  mainWindow = new BrowserWindow({
    width: catWidth,
    height: catHeight,
    x: width - catWidth - 50,
    y: height - catHeight - 50,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    hasShadow: false,
    resizable: false,
    skipTaskbar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Make the window click-through, except for areas we explicitly make clickable (the cat)
  // Initially we ignore mouse events, but in IPC we can toggle this based on mouse enter/leave on the cat.
  // Actually, setting ignoreMouseEvents(true, { forward: true }) works great on Windows/Mac
  mainWindow.setIgnoreMouseEvents(true, { forward: true });

  mainWindow.loadFile('index.html');

  // mainWindow.webContents.openDevTools({ mode: 'detach' });
}

function setupGlobalHooks() {
  uIOhook.on('mousemove', (e) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('global-mousemove', e);
    }
  });

  uIOhook.on('keydown', (e) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('global-keydown', e);
    }
  });

  uIOhook.on('wheel', (e) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('global-wheel', e);
    }
  });

  uIOhook.start();
}

function setupLocalServer() {
  const serverApp = express();
  serverApp.use(express.json());

  serverApp.post('/api/status', (req, res) => {
    const { status } = req.body;
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('ai-status', status);
    }
    res.json({ success: true, status });
  });

  serverApp.post('/api/message', (req, res) => {
    const { message } = req.body;
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('ai-message', message);
    }
    res.json({ success: true, message });
  });

  serverApp.listen(3000, () => {
    console.log('DeskCat Local API running on http://localhost:3000');
  });
}

app.whenReady().then(() => {
  createWindow();
  setupGlobalHooks();
  setupLocalServer();

  ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    if (mainWindow) {
      mainWindow.setIgnoreMouseEvents(ignore, options);
    }
  });

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('will-quit', () => {
  uIOhook.stop();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
