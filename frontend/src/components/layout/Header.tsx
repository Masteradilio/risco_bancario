import { LogOut, Moon, Palette, Sun } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/stores/useAuth'
import { THEME_LABELS, useTheme } from '@/stores/useTheme'

export default function Header() {
    const location = useLocation()
    const navigate = useNavigate()
    const { user, logout } = useAuth()
    const { theme, resolvedTheme, setTheme } = useTheme()
    const title = location.pathname === '/settings' ? 'Configurações' : 'Evidências ECL'

    const cycleTheme = () => setTheme(resolvedTheme === 'dark' ? 'light-snow' : 'dark-ocean')
    const signOut = async () => { await logout(); navigate('/login') }

    return <header className="flex items-center justify-between border-b border-border bg-background/80 px-6 py-4 backdrop-blur-sm">
        <div><h2 className="text-xl font-semibold">{title}</h2><p className="text-sm text-muted-foreground">Fonte persistida, autorizada e versionada</p></div>
        <div className="flex items-center gap-3">
            <button onClick={cycleTheme} title={THEME_LABELS[theme]} className="flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm"><Palette className="h-4 w-4" />{resolvedTheme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}</button>
            <div className="text-right"><p className="text-sm font-medium">{user?.nome}</p><p className="text-xs text-muted-foreground">{user?.role}</p></div>
            <button onClick={signOut} aria-label="Sair" className="rounded-lg p-2 text-destructive hover:bg-destructive/10"><LogOut className="h-5 w-5" /></button>
        </div>
    </header>
}
