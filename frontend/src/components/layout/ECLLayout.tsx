import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
    LayoutDashboard,
    Calculator,
    Layers,
    Users,
    TrendingUp,
    BarChart3,
    HeartPulse,
    FileX2,
    FileOutput,
    Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const subNavigation = [
    { name: 'Dashboard', href: '/perda-esperada', icon: LayoutDashboard, description: 'Visão geral ECL' },
    { name: 'Cálculo ECL', href: '/perda-esperada/calculo', icon: Calculator, description: 'Individual e Portfólio' },
    { name: 'Estágios', href: '/perda-esperada/estagios', icon: Layers, description: 'Triggers IFRS 9' },
    { name: 'Grupos', href: '/perda-esperada/grupos', icon: Users, description: 'Segmentação por PD' },
    { name: 'Forward Looking', href: '/perda-esperada/forward-looking', icon: TrendingUp, description: 'Cenários macro' },
    { name: 'LGD', href: '/perda-esperada/lgd', icon: BarChart3, description: 'Loss Given Default' },
    { name: 'Cura', href: '/perda-esperada/cura', icon: HeartPulse, description: 'Reversão de estágios' },
    { name: 'Write-off', href: '/perda-esperada/writeoff', icon: FileX2, description: 'Baixas e recuperações' },
    { name: 'Pipeline', href: '/perda-esperada/pipeline', icon: Zap, description: 'Execução full ECL' },
    { name: 'Exportação', href: '/perda-esperada/exportacao', icon: FileOutput, description: 'Doc3040 BACEN' },
]

export default function ECLLayout() {
    const location = useLocation()

    return (
        <div className="space-y-6">
            {/* Sub Navigation - Abas horizontais MAIORES E MAIS CHAMATIVAS */}
            <nav className="flex flex-wrap gap-3 p-2 bg-gradient-to-r from-muted/80 to-muted/40 rounded-xl border border-border">
                {subNavigation.map((item) => {
                    const isActive = location.pathname === item.href

                    return (
                        <NavLink
                            key={item.href}
                            to={item.href}
                            className={cn(
                                'flex items-center gap-2 px-5 py-3 text-sm rounded-xl transition-all duration-200 font-semibold',
                                isActive
                                    ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                                    : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                            )}
                            title={item.description}
                        >
                            <item.icon className="h-5 w-5" />
                            <span className="hidden lg:inline">{item.name}</span>
                        </NavLink>
                    )
                })}
            </nav>

            {/* Page Content */}
            <div>
                <Outlet />
            </div>
        </div>
    )
}
