"use client"

/**
 * Dashboard de Auditoria Aprimorado
 * 
 * Acesso restrito aos perfis AUDITOR e ADMIN
 * 
 * Funcionalidades:
 * - Logs de atividade de usuários
 * - Relatórios de conformidade BACEN 4966
 * - Exportação para evidências regulatórias
 * - Trilha de auditoria completa
 */

import { useState, useMemo, useEffect } from "react"
import { useAuth, AuditLogEntry } from "@/stores/useAuth"
import { RoleGate } from "@/components/auth/PermissionGate"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    ClipboardList,
    Download,
    Search,
    Filter,
    Calendar,
    User,
    Activity,
    Shield,
    FileText,
    AlertCircle,
    CheckCircle,
    TrendingUp,
    Users,
    FileCheck,
    BarChart3,
    Clock,
    FileWarning,
} from "lucide-react"
import { format, subDays, isWithinInterval } from "date-fns"
import { ptBR } from "date-fns/locale"

const ACTION_ICONS: Record<string, any> = {
    LOGIN: User,
    LOGOUT: User,
    CLASSIFY: Activity,
    CALCULATE: Activity,
    EXPORT: FileText,
    VIEW: Shield,
    CREATE_USER: Users,
    UPDATE_USER: Users,
    DELETE_USER: Users,
}

const ACTION_COLORS: Record<string, string> = {
    LOGIN: "text-green-500 bg-green-500/10",
    LOGOUT: "text-orange-500 bg-orange-500/10",
    CLASSIFY: "text-blue-500 bg-blue-500/10",
    CALCULATE: "text-purple-500 bg-purple-500/10",
    EXPORT: "text-cyan-500 bg-cyan-500/10",
    VIEW: "text-slate-500 bg-slate-500/10",
    CREATE_USER: "text-emerald-500 bg-emerald-500/10",
    UPDATE_USER: "text-amber-500 bg-amber-500/10",
    DELETE_USER: "text-red-500 bg-red-500/10",
}

// Mock de relatórios de conformidade
const COMPLIANCE_REPORTS = [
    {
        id: "1",
        titulo: "Relatório de Provisionamento ECL",
        tipo: "CMN 4966 - Art. 36",
        periodo: "Janeiro 2026",
        status: "completo",
        data: "08/01/2026",
    },
    {
        id: "2",
        titulo: "Relatório de Migração de Estágios",
        tipo: "IFRS 9 - Stages",
        periodo: "Janeiro 2026",
        status: "completo",
        data: "08/01/2026",
    },
    {
        id: "3",
        titulo: "Relatório de Write-off e Recuperações",
        tipo: "CMN 4966 - Art. 49",
        periodo: "Janeiro 2026",
        status: "pendente",
        data: "-",
    },
    {
        id: "4",
        titulo: "Relatório Forward Looking",
        tipo: "CMN 4966 - Art. 36 §5º",
        periodo: "Janeiro 2026",
        status: "completo",
        data: "08/01/2026",
    },
]

// Mock de envios BACEN
const BACEN_SUBMISSIONS = [
    {
        id: "ENV-2026-001",
        documento: "Doc3040",
        dataBase: "31/12/2025",
        status: "aceito",
        protocolo: "BCB-2026-00012345",
        dataEnvio: "05/01/2026",
    },
    {
        id: "ENV-2025-012",
        documento: "Doc3040",
        dataBase: "30/11/2025",
        status: "aceito",
        protocolo: "BCB-2025-00098765",
        dataEnvio: "05/12/2025",
    },
    {
        id: "ENV-2025-011",
        documento: "Doc3040",
        dataBase: "31/10/2025",
        status: "aceito",
        protocolo: "BCB-2025-00087654",
        dataEnvio: "05/11/2025",
    },
]

// Mock de logs expandido
const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
    { id: "1", timestamp: new Date(Date.now() - 60000).toISOString(), usuario: "João Santos", acao: "EXPORT", recurso: "BACEN_XML", detalhes: "Exportou Doc3040 para BACEN" },
    { id: "2", timestamp: new Date(Date.now() - 120000).toISOString(), usuario: "Maria Silva", acao: "CALCULATE", recurso: "ECL_PIPELINE", detalhes: "Executou pipeline ECL completo" },
    { id: "3", timestamp: new Date(Date.now() - 180000).toISOString(), usuario: "Carlos Admin", acao: "CREATE_USER", recurso: "USUARIOS", detalhes: "Criou usuário Pedro Externo (AUDITOR)" },
    { id: "4", timestamp: new Date(Date.now() - 300000).toISOString(), usuario: "Ana Costa", acao: "VIEW", recurso: "AUDITORIA", detalhes: "Acessou relatórios de conformidade" },
    { id: "5", timestamp: new Date(Date.now() - 600000).toISOString(), usuario: "Maria Silva", acao: "CLASSIFY", recurso: "PRINAD", detalhes: "Classificou lote de 150 clientes" },
    { id: "6", timestamp: new Date(Date.now() - 900000).toISOString(), usuario: "João Santos", acao: "LOGIN", recurso: "SISTEMA", detalhes: "Login via Windows SSO" },
    { id: "7", timestamp: new Date(Date.now() - 3600000).toISOString(), usuario: "Maria Silva", acao: "LOGIN", recurso: "SISTEMA", detalhes: "Login via Windows SSO" },
    { id: "8", timestamp: new Date(Date.now() - 7200000).toISOString(), usuario: "Carlos Admin", acao: "UPDATE_USER", recurso: "USUARIOS", detalhes: "Atualizou permissões de Ana Costa" },
]

export default function AuditoriaPage() {
    const { auditLogs: storeLogs, user, checkPermission, addAuditLog } = useAuth()
    const [search, setSearch] = useState("")
    const [filterAcao, setFilterAcao] = useState("ALL")
    const [filterUsuario, setFilterUsuario] = useState("ALL")
    const [filterPeriodo, setFilterPeriodo] = useState("7")

    // Combinar logs do store com mock
    const allLogs = useMemo(() => {
        return [...storeLogs, ...MOCK_AUDIT_LOGS].sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
    }, [storeLogs])

    // Verificar permissão
    if (!checkPermission('view:audit')) {
        return (
            <RoleGate
                roles={["AUDITOR", "ADMIN"]}
                fallback={
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
                }
            >
                <></>
            </RoleGate>
        )
    }

    // Registrar acesso à página
    useEffect(() => {
        addAuditLog('VIEW', 'AUDITORIA', 'Acessou dashboard de auditoria')
    }, [])

    // Filtrar logs
    const filteredLogs = useMemo(() => {
        const periodoInicio = subDays(new Date(), parseInt(filterPeriodo))

        return allLogs.filter(log => {
            // Filtro de período
            const logDate = new Date(log.timestamp)
            if (!isWithinInterval(logDate, { start: periodoInicio, end: new Date() })) {
                return false
            }

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
    }, [allLogs, search, filterAcao, filterUsuario, filterPeriodo])

    // Estatísticas
    const stats = useMemo(() => {
        const hoje = new Date()
        const semana = subDays(hoje, 7)

        return {
            totalLogs: allLogs.length,
            logsHoje: allLogs.filter(l => new Date(l.timestamp).toDateString() === hoje.toDateString()).length,
            usuariosAtivos: [...new Set(allLogs.filter(l =>
                isWithinInterval(new Date(l.timestamp), { start: semana, end: hoje })
            ).map(l => l.usuario))].length,
            exportacoes: allLogs.filter(l => l.acao === "EXPORT").length,
        }
    }, [allLogs])

    // Dados únicos para filtros
    const uniqueUsers = useMemo(() => [...new Set(allLogs.map(log => log.usuario))], [allLogs])
    const uniqueActions = useMemo(() => [...new Set(allLogs.map(log => log.acao))], [allLogs])

    // Exportar logs para CSV
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

    // Exportar relatório de conformidade
    const exportComplianceReport = (reportId: string) => {
        const report = COMPLIANCE_REPORTS.find(r => r.id === reportId)
        if (report) {
            addAuditLog('EXPORT', 'CONFORMIDADE', `Exportou relatório: ${report.titulo}`)
            // TODO: Implementar exportação real
            alert(`Exportando: ${report.titulo}`)
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <ClipboardList className="h-8 w-8 text-amber-500" />
                        Dashboard de Auditoria
                    </h1>
                    <p className="text-muted-foreground">
                        Trilha de auditoria, conformidade BACEN e relatórios regulatórios
                    </p>
                </div>
                {user?.isExterno && (
                    <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/30">
                        <Clock className="h-3 w-3 mr-1" />
                        Auditor Externo
                    </Badge>
                )}
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Total de Registros</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <BarChart3 className="h-5 w-5 text-blue-500" />
                            <span className="text-2xl font-bold">{stats.totalLogs}</span>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Atividades Hoje</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <Activity className="h-5 w-5 text-green-500" />
                            <span className="text-2xl font-bold">{stats.logsHoje}</span>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Usuários Ativos (7d)</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <Users className="h-5 w-5 text-purple-500" />
                            <span className="text-2xl font-bold">{stats.usuariosAtivos}</span>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Exportações BACEN</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <FileCheck className="h-5 w-5 text-cyan-500" />
                            <span className="text-2xl font-bold">{stats.exportacoes}</span>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="logs" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="logs" className="gap-2">
                        <Activity className="h-4 w-4" />
                        Logs de Atividade
                    </TabsTrigger>
                    <TabsTrigger value="compliance" className="gap-2">
                        <FileCheck className="h-4 w-4" />
                        Conformidade
                    </TabsTrigger>
                    <TabsTrigger value="bacen" className="gap-2">
                        <Shield className="h-4 w-4" />
                        Envios BACEN
                    </TabsTrigger>
                </TabsList>

                {/* Tab: Logs de Atividade */}
                <TabsContent value="logs" className="space-y-4">
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
                                <Select value={filterPeriodo} onValueChange={setFilterPeriodo}>
                                    <SelectTrigger className="w-[120px]">
                                        <SelectValue placeholder="Período" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="1">Hoje</SelectItem>
                                        <SelectItem value="7">7 dias</SelectItem>
                                        <SelectItem value="30">30 dias</SelectItem>
                                        <SelectItem value="90">90 dias</SelectItem>
                                    </SelectContent>
                                </Select>
                                <Select value={filterAcao} onValueChange={setFilterAcao}>
                                    <SelectTrigger className="w-[150px]">
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
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="Usuário" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="ALL">Todos</SelectItem>
                                        {uniqueUsers.map(user => (
                                            <SelectItem key={user} value={user}>{user}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Button onClick={exportLogs} className="gap-2">
                                    <Download className="h-4 w-4" />
                                    Exportar
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Logs Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Trilha de Auditoria</CardTitle>
                            <CardDescription>
                                Exibindo {filteredLogs.length} registros
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
                </TabsContent>

                {/* Tab: Conformidade */}
                <TabsContent value="compliance" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileCheck className="h-5 w-5" />
                                Relatórios de Conformidade
                            </CardTitle>
                            <CardDescription>
                                Relatórios regulatórios conforme CMN 4966 e IFRS 9
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {COMPLIANCE_REPORTS.map(report => (
                                    <div
                                        key={report.id}
                                        className="flex items-center justify-between p-4 rounded-lg border"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`p-2 rounded-lg ${report.status === 'completo'
                                                    ? 'bg-green-500/10'
                                                    : 'bg-amber-500/10'
                                                }`}>
                                                {report.status === 'completo'
                                                    ? <CheckCircle className="h-5 w-5 text-green-500" />
                                                    : <FileWarning className="h-5 w-5 text-amber-500" />
                                                }
                                            </div>
                                            <div>
                                                <h4 className="font-medium">{report.titulo}</h4>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Badge variant="outline">{report.tipo}</Badge>
                                                    <span>•</span>
                                                    <span>{report.periodo}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <span className="text-sm text-muted-foreground">
                                                {report.data}
                                            </span>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => exportComplianceReport(report.id)}
                                                disabled={report.status !== 'completo'}
                                            >
                                                <Download className="h-4 w-4 mr-2" />
                                                Exportar
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Tab: Envios BACEN */}
                <TabsContent value="bacen" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="h-5 w-5" />
                                Histórico de Envios BACEN
                            </CardTitle>
                            <CardDescription>
                                Registro de todas as remessas Doc3040 enviadas
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="border rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-muted">
                                        <tr>
                                            <th className="p-3 text-left">Código</th>
                                            <th className="p-3 text-left">Documento</th>
                                            <th className="p-3 text-left">Data Base</th>
                                            <th className="p-3 text-left">Data Envio</th>
                                            <th className="p-3 text-left">Status</th>
                                            <th className="p-3 text-left">Protocolo</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {BACEN_SUBMISSIONS.map(sub => (
                                            <tr key={sub.id} className="border-t hover:bg-muted/50">
                                                <td className="p-3 font-mono text-sm">{sub.id}</td>
                                                <td className="p-3">{sub.documento}</td>
                                                <td className="p-3">{sub.dataBase}</td>
                                                <td className="p-3">{sub.dataEnvio}</td>
                                                <td className="p-3">
                                                    <Badge variant="outline" className="bg-green-500/10 text-green-600">
                                                        <CheckCircle className="h-3 w-3 mr-1" />
                                                        {sub.status}
                                                    </Badge>
                                                </td>
                                                <td className="p-3 font-mono text-xs">{sub.protocolo}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
