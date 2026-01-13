"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("electronAPI", {
  // Listener para mudança de tema do sistema
  onSystemThemeChange: (callback) => {
    electron.ipcRenderer.on("system-theme-changed", (_event, isDark) => callback(isDark));
  },
  // Verificar se está rodando no Electron
  isElectron: true,
  // Informações do ambiente
  platform: process.platform
});
