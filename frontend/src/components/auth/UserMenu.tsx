"use client"

import { useAuth } from "@/stores/useAuth"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { User, LogOut, Shield, Settings, ClipboardList } from "lucide-react"
import Link from "next/link"

const ROLE_COLORS: Record<string, string> = {
    ANALISTA: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    GESTOR: "bg-green-500/20 text-green-400 border-green-500/30",
    AUDITOR: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    ADMIN: "bg-red-500/20 text-red-400 border-red-500/30",
}

export function UserMenu() {
    const { user, logout, checkPermission } = useAuth()

    if (!user) return null

    const roleColor = ROLE_COLORS[user.role] || ROLE_COLORS.ANALISTA

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 h-auto py-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-sm">
                        {user.nome.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                    </div>
                    <div className="hidden md:flex flex-col items-start">
                        <span className="text-sm font-medium">{user.nome}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded border ${roleColor}`}>
                            {user.role}
                        </span>
                    </div>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                    <div className="flex flex-col">
                        <span>{user.nome}</span>
                        <span className="text-xs text-muted-foreground font-normal">{user.email}</span>
                        <span className="text-xs text-muted-foreground font-normal">Matrícula: {user.matricula}</span>
                    </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />

                <DropdownMenuItem asChild>
                    <Link href="/settings" className="cursor-pointer">
                        <Settings className="mr-2 h-4 w-4" />
                        Configurações
                    </Link>
                </DropdownMenuItem>

                {checkPermission('view:audit') && (
                    <DropdownMenuItem asChild>
                        <Link href="/auditoria" className="cursor-pointer">
                            <ClipboardList className="mr-2 h-4 w-4" />
                            Logs de Auditoria
                        </Link>
                    </DropdownMenuItem>
                )}

                <DropdownMenuSeparator />

                <DropdownMenuItem
                    onClick={logout}
                    className="text-red-500 focus:text-red-500 cursor-pointer"
                >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sair
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
