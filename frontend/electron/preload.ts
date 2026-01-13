import { contextBridge, ipcRenderer } from 'electron'

// Expor APIs seguras para o renderer
contextBridge.exposeInMainWorld('electronAPI', {
    // Listener para mudança de tema do sistema
    onSystemThemeChange: (callback: (isDark: boolean) => void) => {
        ipcRenderer.on('system-theme-changed', (_event, isDark) => callback(isDark))
    },

    // Verificar se está rodando no Electron
    isElectron: true,

    // Informações do ambiente
    platform: process.platform,
})

// Type definitions para o objeto window
declare global {
    interface Window {
        electronAPI: {
            onSystemThemeChange: (callback: (isDark: boolean) => void) => void
            isElectron: boolean
            platform: string
        }
    }
}
