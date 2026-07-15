import { Calculator, Settings, TrendingUp } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAuth } from '@/stores/useAuth'

const navigation = [
    { label: 'Evidências ECL', path: '/perda-esperada', icon: Calculator },
    { label: 'Configurações', path: '/settings', icon: Settings },
]

export default function Sidebar() {
    const user = useAuth((state) => state.user)
    return <aside className="flex h-screen w-64 flex-col border-r border-sidebar-border bg-sidebar">
        <div className="flex items-center gap-3 border-b border-sidebar-border px-4 py-5"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10"><TrendingUp className="h-5 w-5 text-primary" /></div><div><h1 className="font-bold">Risco Bancário</h1><p className="text-xs text-muted-foreground">ECL versionado</p></div></div>
        <nav className="flex-1 space-y-1 p-3">{navigation.map((item) => <NavLink key={item.path} to={item.path} className={({ isActive }) => cn('flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-sidebar-accent', isActive && 'bg-sidebar-accent text-primary')}><item.icon className="h-5 w-5" />{item.label}</NavLink>)}</nav>
        <div className="border-t border-sidebar-border p-4 text-xs text-muted-foreground"><p className="truncate">{user?.nome}</p><p>{user?.role}</p></div>
    </aside>
}
