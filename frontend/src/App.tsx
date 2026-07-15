import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import ECLDashboardPage from '@/pages/ecl/ECLDashboardPage'
import LoginPage from '@/pages/LoginPage'
import SettingsPage from '@/pages/settings/SettingsPage'
import { useAuth } from '@/stores/useAuth'
import { useTheme } from '@/stores/useTheme'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    return useAuth((state) => state.isAuthenticated) ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
    const { theme, resolvedTheme } = useTheme()

    useEffect(() => {
        const root = document.documentElement
        root.removeAttribute('data-theme')
        root.classList.remove('dark', 'light')
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        const activeTheme = theme === 'system' ? systemTheme : resolvedTheme
        root.setAttribute('data-theme', theme === 'system' ? `${systemTheme}-ocean` : theme)
        root.classList.add(activeTheme)
    }, [theme, resolvedTheme])

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
                    <Route index element={<Navigate to="/perda-esperada" replace />} />
                    <Route path="perda-esperada" element={<ECLDashboardPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    )
}
