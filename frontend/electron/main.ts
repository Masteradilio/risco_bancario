import { app, BrowserWindow, nativeTheme } from 'electron'
import path from 'path'

let mainWindow: BrowserWindow | null = null

const createWindow = () => {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 700,
        title: 'Propensão - Gestão de Risco Bancário',
        backgroundColor: nativeTheme.shouldUseDarkColors ? '#0a0a14' : '#fafafa',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
        show: false,
        autoHideMenuBar: true,
    })

    // Mostrar janela quando estiver pronta para evitar flash branco
    mainWindow.once('ready-to-show', () => {
        mainWindow?.show()
    })

    // Em desenvolvimento, carregar do servidor Vite
    if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
        mainWindow.loadURL('http://localhost:5173')
        mainWindow.webContents.openDevTools()
    } else {
        // Em produção, carregar o arquivo HTML compilado
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
    }

    mainWindow.on('closed', () => {
        mainWindow = null
    })
}

// Criar janela quando o Electron estiver pronto
app.whenReady().then(() => {
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
})

// Fechar app quando todas as janelas forem fechadas (exceto no macOS)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

// Enviar informação de tema do sistema para o renderer
nativeTheme.on('updated', () => {
    mainWindow?.webContents.send('system-theme-changed', nativeTheme.shouldUseDarkColors)
})
