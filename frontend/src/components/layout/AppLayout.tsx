"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
    ChartPie,
    Calculator,
    TrendingUp,
    Settings,
    Bot,
    Moon,
    Sun,
    Menu,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"
import { useTheme, applyTheme } from "@/stores/useTheme"

const navigation = [
    { name: "PRINAD", href: "/prinad", icon: ChartPie, description: "Probabilidade de Inadimplência" },
    { name: "ECL", href: "/ecl", icon: Calculator, description: "Perda Esperada" },
    { name: "Propensão", href: "/propensao", icon: TrendingUp, description: "Otimização de Limites" },
    { name: "Assistente IA", href: "/ai", icon: Bot, description: "Agente Inteligente" },
    { name: "Configurações", href: "/settings", icon: Settings, description: "Configurações do Sistema" },
]

function NavItem({ item, pathname, mobile = false }: { item: typeof navigation[0], pathname: string, mobile?: boolean }) {
    const isActive = pathname.startsWith(item.href)

    return (
        <Link
            href={item.href}
            className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                isActive
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted",
                mobile && "w-full"
            )}
        >
            <item.icon className="h-5 w-5" />
            <span>{item.name}</span>
        </Link>
    )
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname()
    const { theme, setTheme } = useTheme()
    const [mounted, setMounted] = React.useState(false)

    React.useEffect(() => {
        setMounted(true)
        applyTheme(theme)
    }, [theme])

    const toggleTheme = () => {
        const next = theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark'
        setTheme(next)
        applyTheme(next)
    }

    return (
        <div className="flex min-h-screen">
            {/* Desktop Sidebar */}
            <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:border-r lg:bg-background">
                <div className="flex h-16 items-center gap-2 border-b px-6">
                    <ChartPie className="h-6 w-6 text-primary" />
                    <span className="text-xl font-bold">Risco Bancário</span>
                </div>
                <nav className="flex-1 space-y-1 p-4">
                    {navigation.map((item) => (
                        <NavItem key={item.name} item={item} pathname={pathname} />
                    ))}
                </nav>
                <div className="border-t p-4">
                    <p className="text-xs text-muted-foreground">Sistema v2.0 - BACEN 4966</p>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
                {/* Header */}
                <header className="flex h-16 items-center gap-4 border-b bg-background px-6">
                    {/* Mobile Menu */}
                    <Sheet>
                        <SheetTrigger asChild className="lg:hidden">
                            <Button variant="ghost" size="icon">
                                <Menu className="h-5 w-5" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="w-64 p-0">
                            <div className="flex h-16 items-center gap-2 border-b px-6">
                                <ChartPie className="h-6 w-6 text-primary" />
                                <span className="text-xl font-bold">Risco Bancário</span>
                            </div>
                            <nav className="space-y-1 p-4">
                                {navigation.map((item) => (
                                    <NavItem key={item.name} item={item} pathname={pathname} mobile />
                                ))}
                            </nav>
                        </SheetContent>
                    </Sheet>

                    <div className="flex-1" />

                    {/* Theme Toggle */}
                    {mounted && (
                        <Button variant="ghost" size="icon" onClick={toggleTheme}>
                            {theme === 'dark' ? (
                                <Moon className="h-5 w-5" />
                            ) : theme === 'light' ? (
                                <Sun className="h-5 w-5" />
                            ) : (
                                <div className="h-5 w-5 flex items-center justify-center text-xs font-bold">A</div>
                            )}
                        </Button>
                    )}
                </header>

                {/* Page Content */}
                <div className="flex-1 p-6">
                    {children}
                </div>
            </main>
        </div>
    )
}
