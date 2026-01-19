import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '@/stores/useAuth'
import {
    LayoutDashboard,
    Target,
    TrendingUp,
    Calculator,
    FileText,
    Settings,
    Shield,
    Users,
    ChevronDown,
    ChevronRight,
    BarChart3,
    Bot,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface NavItem {
    label: string
    path: string
    icon: React.ComponentType<{ className?: string }>
    permission?: string
    children?: NavItem[]
}

const navigation: NavItem[] = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'PRINAD', path: '/prinad', icon: Target },
    { label: 'Perda Esperada', path: '/perda-esperada', icon: Calculator },
    { label: 'Propensão', path: '/propensao', icon: TrendingUp },
    { label: 'Agente IA', path: '/agent', icon: Bot },
    { label: 'Analytics', path: '/analytics', icon: BarChart3, permission: 'view:analytics' },
    { label: 'Auditoria', path: '/auditoria', icon: Shield, permission: 'view:audit' },
    { label: 'Relatórios', path: '/relatorios', icon: FileText },
    { label: 'Admin', path: '/admin', icon: Users, permission: 'manage:users' },
    { label: 'Configurações', path: '/settings', icon: Settings },
]

function NavItemComponent({ item, level = 0 }: { item: NavItem; level?: number }) {
    const location = useLocation()
    const { checkPermission } = useAuth()
    const [isOpen, setIsOpen] = useState(
        item.children?.some(child => location.pathname === child.path || location.pathname.startsWith(child.path + '/'))
    )

    // Verificar permissão
    if (item.permission && !checkPermission(item.permission)) {
        return null
    }

    const Icon = item.icon
    const hasChildren = item.children && item.children.length > 0
    const isActive = location.pathname === item.path ||
        (hasChildren && location.pathname.startsWith(item.path))

    if (hasChildren) {
        return (
            <div className="space-y-1">
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={cn(
                        'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                        'hover:bg-sidebar-accent',
                        isActive && 'bg-sidebar-accent text-primary'
                    )}
                >
                    <Icon className="h-5 w-5 shrink-0" />
                    <span className="flex-1 text-left">{item.label}</span>
                    {isOpen ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                </button>

                {isOpen && (
                    <div className="ml-4 pl-3 border-l border-sidebar-border space-y-1 animate-slide-in">
                        {item.children.map((child) => (
                            <NavItemComponent key={child.path} item={child} level={level + 1} />
                        ))}
                    </div>
                )}
            </div>
        )
    }

    return (
        <NavLink
            to={item.path}
            className={({ isActive: linkActive }) =>
                cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                    'hover:bg-sidebar-accent',
                    linkActive && 'sidebar-item-active bg-sidebar-accent text-primary'
                )
            }
        >
            <Icon className="h-5 w-5 shrink-0" />
            <span>{item.label}</span>
        </NavLink>
    )
}

export default function Sidebar() {
    const { user } = useAuth()

    return (
        <aside className="flex flex-col h-screen w-64 bg-sidebar border-r border-sidebar-border">
            {/* Logo */}
            <div className="flex items-center gap-3 px-4 py-5 border-b border-sidebar-border">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10">
                    <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <h1 className="font-bold text-lg text-sidebar-foreground">Propensão</h1>
                    <p className="text-xs text-muted-foreground">Gestão de Risco</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto p-3 space-y-1">
                {navigation.map((item) => (
                    <NavItemComponent key={item.path} item={item} />
                ))}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-sidebar-border">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-soft" />
                        Online
                    </span>
                    <span className="mx-1">•</span>
                    <span>v2.5</span>
                </div>
                {user && (
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                        {user.role}
                    </p>
                )}
            </div>
        </aside>
    )
}
