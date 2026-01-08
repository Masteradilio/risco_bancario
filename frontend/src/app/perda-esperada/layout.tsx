"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
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
    ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface SubNavItem {
    name: string
    href: string
    icon: any
    description: string
}

const subNavigation: SubNavItem[] = [
    {
        name: "Dashboard",
        href: "/perda-esperada",
        icon: LayoutDashboard,
        description: "Visão geral ECL"
    },
    {
        name: "Cálculo ECL",
        href: "/perda-esperada/calculo",
        icon: Calculator,
        description: "Individual e Portfólio"
    },
    {
        name: "Classificação de Estágios",
        href: "/perda-esperada/estagios",
        icon: Layers,
        description: "Triggers e migrações IFRS 9"
    },
    {
        name: "Grupos Homogêneos",
        href: "/perda-esperada/grupos-homogeneos",
        icon: Users,
        description: "Segmentação por PD"
    },
    {
        name: "Forward Looking",
        href: "/perda-esperada/forward-looking",
        icon: TrendingUp,
        description: "Cenários macroeconômicos"
    },
    {
        name: "LGD Segmentado",
        href: "/perda-esperada/lgd",
        icon: BarChart3,
        description: "Loss Given Default por produto"
    },
    {
        name: "Sistema de Cura",
        href: "/perda-esperada/cura",
        icon: HeartPulse,
        description: "Reversão de estágios"
    },
    {
        name: "Write-off",
        href: "/perda-esperada/writeoff",
        icon: FileX2,
        description: "Baixas e recuperações"
    },
    {
        name: "Pipeline Completo",
        href: "/perda-esperada/pipeline",
        icon: Zap,
        description: "Execução full ECL"
    },
    {
        name: "Exportação BACEN",
        href: "/perda-esperada/exportacao",
        icon: FileOutput,
        description: "Doc3040 XML"
    },
]

export default function PerdaEsperadaLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Perda Esperada (ECL)</h1>
                <p className="text-muted-foreground">
                    Expected Credit Loss - Resolução CMN 4966/2021 / IFRS 9
                </p>
            </div>

            {/* Sub Navigation */}
            <nav className="flex flex-wrap gap-2 p-1 bg-muted/50 rounded-lg">
                {subNavigation.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== "/perda-esperada" && pathname.startsWith(item.href))

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-all",
                                isActive
                                    ? "bg-background text-primary shadow-sm font-medium"
                                    : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                            )}
                            title={item.description}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="hidden md:inline">{item.name}</span>
                        </Link>
                    )
                })}
            </nav>

            {/* Page Content */}
            <div>
                {children}
            </div>
        </div>
    )
}
