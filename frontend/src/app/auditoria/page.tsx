"use client"

import { useState, useMemo } from "react"
import { useAuth } from "@/stores/useAuth"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
    ClipboardList,
    Download,
    Search,
    Filter,
    Calendar,
    User,
    Activity,
    Shield,
    FileText
} from "lucide-react"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"

const ACTION_ICONS: Record<string, any> = {
    LOGIN: User,
    LOGOUT: User,
    CLASSIFY: Activity,
    CALCULATE: Activity,
    EXPORT: FileText,
    VIEW: Shield,
}

const ACTION_COLORS: Record<string, string> = {
    LOGIN: "text-green-500 bg-green-500/10",
    LOGOUT: "text-orange-500 bg-orange-500/10",
    CLASSIFY: "text-blue-500 bg-blue-500/10",
    CALCULATE: "text-purple-500 bg-purple-500/10",
    EXPORT: "text-cyan-500 bg-cyan-500/10",
    VIEW: "text-slate-500 bg-slate-500/10",
}

export default function AuditoriaPage() {
    const { auditLogs, user, checkPermission, addAuditLog } = useAuth()
    const [search, setSearch] = useState("")
    const [filterAcao, setFilterAcao] = useState("ALL")
    const [filterUsuario, setFilterUsuario] = useState("ALL")

    // Verificar permissão
    if (!checkPermission('view:audit')) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="w-full max-w-md text-center">
                    <CardContent className="pt-6">
                        <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                        <h2 className="text-xl font-semibold mb-2">Acesso Restrito</h2>
                        <p className="text-muted-foreground">
                            Você não tem permissão para acessar os logs de auditoria.
                            Contate o administrador do sistema.
                        </p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    // Registrar acesso à página de auditoria
    useMemo(() => {
        addAuditLog('VIEW', 'AUDITORIA', 'Acessou logs de auditoria')
    }, [])

    // Filtrar logs
    const filteredLogs = useMemo(() => {
        return auditLogs.filter(log => {
            // Filtro de busca
            if (search) {
                const searchLower = search.toLowerCase()
                if (!log.usuario.toLowerCase().includes(searchLower) &&
                    !log.acao.toLowerCase().includes(searchLower) &&
                    !log.recurso.toLowerCase().includes(searchLower) &&
                    !log.detalhes.toLowerCase().includes(searchLower)) {
                    return false
                }
            }

            // Filtro de ação
            if (filterAcao !== "ALL" && log.acao !== filterAcao) {
                return false
            }

            // Filtro de usuário
            if (filterUsuario !== "ALL" && log.usuario !== filterUsuario) {
                return false
            }

            return true
        })
    }, [auditLogs, search, filterAcao, filterUsuario])

    // Usuários únicos
    const uniqueUsers = useMemo(() => {
        return [...new Set(auditLogs.map(log => log.usuario))]
    }, [auditLogs])

    // Ações únicas
    const uniqueActions = useMemo(() => {
        return [...new Set(auditLogs.map(log => log.acao))]
    }, [auditLogs])

    // Exportar logs
    const exportLogs = () => {
        const csv = [
            'ID,Timestamp,Usuário,Ação,Recurso,Detalhes',
            ...filteredLogs.map(log =>
                `"${log.id}","${log.timestamp}","${log.usuario}","${log.acao}","${log.recurso}","${log.detalhes.replace(/"/g, '""')}"`
            )
        ].join('\n')

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `audit_logs_${format(new Date(), 'yyyy-MM-dd_HHmmss')}.csv`
        a.click()
        URL.revokeObjectURL(url)

        addAuditLog('EXPORT', 'AUDITORIA', `Exportou ${filteredLogs.length} logs de auditoria`)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <ClipboardList className="h-8 w-8" />
                        Logs de Auditoria
                    </h1>
                    <p className="text-muted-foreground">
                        Registro de todas as ações realizadas no sistema
                    </p>
                </div>
                <Button onClick={exportLogs} className="gap-2">
                    <Download className="h-4 w-4" />
                    Exportar CSV
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Total de Registros
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <span className="text-2xl font-bold">{auditLogs.length}</span>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Filtrados
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <span className="text-2xl font-bold">{filteredLogs.length}</span>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Usuários Ativos
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <span className="text-2xl font-bold">{uniqueUsers.length}</span>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Tipos de Ação
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <span className="text-2xl font-bold">{uniqueActions.length}</span>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-sm flex items-center gap-2">
                        <Filter className="h-4 w-4" />
                        Filtros
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Buscar por usuário, ação, recurso..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                        </div>
                        <Select value={filterAcao} onValueChange={setFilterAcao}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Ação" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="ALL">Todas as ações</SelectItem>
                                {uniqueActions.map(action => (
                                    <SelectItem key={action} value={action}>{action}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <Select value={filterUsuario} onValueChange={setFilterUsuario}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Usuário" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="ALL">Todos os usuários</SelectItem>
                                {uniqueUsers.map(user => (
                                    <SelectItem key={user} value={user}>{user}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            {/* Logs Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Registros</CardTitle>
                    <CardDescription>
                        Exibindo {filteredLogs.length} de {auditLogs.length} registros
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="max-h-[500px] overflow-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-muted sticky top-0">
                                <tr>
                                    <th className="p-3 text-left">Data/Hora</th>
                                    <th className="p-3 text-left">Usuário</th>
                                    <th className="p-3 text-left">Ação</th>
                                    <th className="p-3 text-left">Recurso</th>
                                    <th className="p-3 text-left">Detalhes</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredLogs.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted-foreground">
                                            Nenhum registro encontrado
                                        </td>
                                    </tr>
                                ) : (
                                    filteredLogs.map((log) => {
                                        const IconComponent = ACTION_ICONS[log.acao] || Activity
                                        const colorClass = ACTION_COLORS[log.acao] || ACTION_COLORS.VIEW

                                        return (
                                            <tr key={log.id} className="border-t hover:bg-muted/50">
                                                <td className="p-3">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="h-4 w-4 text-muted-foreground" />
                                                        <span>
                                                            {format(new Date(log.timestamp), "dd/MM/yyyy HH:mm:ss", { locale: ptBR })}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="p-3 font-medium">{log.usuario}</td>
                                                <td className="p-3">
                                                    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
                                                        <IconComponent className="h-3 w-3" />
                                                        {log.acao}
                                                    </span>
                                                </td>
                                                <td className="p-3">
                                                    <code className="text-xs bg-muted px-2 py-1 rounded">{log.recurso}</code>
                                                </td>
                                                <td className="p-3 max-w-xs truncate" title={log.detalhes}>
                                                    {log.detalhes}
                                                </td>
                                            </tr>
                                        )
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
