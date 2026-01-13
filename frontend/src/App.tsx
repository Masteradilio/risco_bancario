import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './stores/useAuth'
import { useTheme } from './stores/useTheme'
import { useEffect } from 'react'

// Layout
import MainLayout from './components/layout/MainLayout'
import ECLLayout from './components/layout/ECLLayout'

// Pages
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PrinadPage from './pages/prinad/PrinadPage'
import PropensaoPage from './pages/propensao/PropensaoPage'
import AuditoriaPage from './pages/auditoria/AuditoriaPage'
import AdminPage from './pages/admin/AdminPage'
import SettingsPage from './pages/settings/SettingsPage'
import RelatoriosPage from './pages/relatorios/RelatoriosPage'

// Perda Esperada (ECL)
import ECLDashboardPage from './pages/ecl/ECLDashboardPage'
import ECLCalculoPage from './pages/ecl/ECLCalculoPage'
import ECLEstagiosPage from './pages/ecl/ECLEstagiosPage'
import ECLGruposPage from './pages/ecl/ECLGruposPage'
import ECLForwardLookingPage from './pages/ecl/ECLForwardLookingPage'
import ECLLGDPage from './pages/ecl/ECLLGDPage'
import ECLCuraPage from './pages/ecl/ECLCuraPage'
import ECLWriteoffPage from './pages/ecl/ECLWriteoffPage'
import ECLExportacaoPage from './pages/ecl/ECLExportacaoPage'
import ECLPipelinePage from './pages/ecl/ECLPipelinePage'

// Componente de rota protegida
function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const isAuthenticated = useAuth((state) => state.isAuthenticated)

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return <>{children}</>
}

function App() {
    const { theme, resolvedTheme } = useTheme()

    // Aplicar tema ao documento
    useEffect(() => {
        const root = document.documentElement

        // Remover temas anteriores
        root.removeAttribute('data-theme')
        root.classList.remove('dark', 'light')

        if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
            root.setAttribute('data-theme', `${systemTheme}-ocean`)
            root.classList.add(systemTheme)
        } else {
            root.setAttribute('data-theme', theme)
            root.classList.add(resolvedTheme)
        }
    }, [theme, resolvedTheme])

    // Listener para mudança de tema do sistema (no Electron)
    useEffect(() => {
        if (window.electronAPI) {
            window.electronAPI.onSystemThemeChange((isDark) => {
                if (useTheme.getState().theme === 'system') {
                    const root = document.documentElement
                    root.setAttribute('data-theme', isDark ? 'dark-ocean' : 'light-snow')
                    root.classList.toggle('dark', isDark)
                    root.classList.toggle('light', !isDark)
                }
            })
        }
    }, [])

    return (
        <BrowserRouter>
            <Routes>
                {/* Rota pública */}
                <Route path="/login" element={<LoginPage />} />

                {/* Rotas protegidas com layout principal */}
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <MainLayout />
                        </ProtectedRoute>
                    }
                >
                    <Route index element={<DashboardPage />} />
                    <Route path="prinad" element={<PrinadPage />} />
                    <Route path="propensao" element={<PropensaoPage />} />
                    <Route path="auditoria" element={<AuditoriaPage />} />
                    <Route path="admin" element={<AdminPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                    <Route path="relatorios" element={<RelatoriosPage />} />

                    {/* Perda Esperada (ECL) - com layout de abas horizontais */}
                    <Route path="perda-esperada" element={<ECLLayout />}>
                        <Route index element={<ECLDashboardPage />} />
                        <Route path="calculo" element={<ECLCalculoPage />} />
                        <Route path="estagios" element={<ECLEstagiosPage />} />
                        <Route path="grupos" element={<ECLGruposPage />} />
                        <Route path="forward-looking" element={<ECLForwardLookingPage />} />
                        <Route path="lgd" element={<ECLLGDPage />} />
                        <Route path="cura" element={<ECLCuraPage />} />
                        <Route path="writeoff" element={<ECLWriteoffPage />} />
                        <Route path="exportacao" element={<ECLExportacaoPage />} />
                        <Route path="pipeline" element={<ECLPipelinePage />} />
                    </Route>
                </Route>

                {/* Redirect para login se rota não encontrada */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
