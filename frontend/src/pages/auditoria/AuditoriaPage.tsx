import { useAuth } from '@/stores/useAuth'
import { Shield, Clock, User, Download, Filter } from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

export default function AuditoriaPage() {
    const { auditLogs } = useAuth()

    return (
        <div className="space-y-6">
            {/* Header Actions */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-accent transition-colors text-sm">
                        <Filter className="h-4 w-4" />
                        Filtrar
                    </button>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm">
                    <Download className="h-4 w-4" />
                    Exportar CSV
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Total de Logs</p>
                    <p className="text-2xl font-bold mt-1">{auditLogs.length}</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Atividades Hoje</p>
                    <p className="text-2xl font-bold mt-1">
                        {auditLogs.filter(log =>
                            new Date(log.timestamp).toDateString() === new Date().toDateString()
                        ).length}
                    </p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Usuários Únicos</p>
                    <p className="text-2xl font-bold mt-1">
                        {new Set(auditLogs.map(log => log.usuario)).size}
                    </p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Exportações</p>
                    <p className="text-2xl font-bold mt-1">
                        {auditLogs.filter(log => log.acao.includes('EXPORT')).length}
                    </p>
                </div>
            </div>

            {/* Logs Table */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Trilha de Auditoria</h3>

                {auditLogs.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Nenhum log de auditoria registrado</p>
                        <p className="text-sm mt-1">As atividades do sistema serão registradas aqui</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-4">Timestamp</th>
                                    <th className="text-left py-3 px-4">Usuário</th>
                                    <th className="text-left py-3 px-4">Ação</th>
                                    <th className="text-left py-3 px-4">Recurso</th>
                                    <th className="text-left py-3 px-4">Detalhes</th>
                                </tr>
                            </thead>
                            <tbody>
                                {auditLogs.slice(0, 50).map((log) => (
                                    <tr key={log.id} className="border-b border-border hover:bg-muted/50">
                                        <td className="py-3 px-4 text-muted-foreground">
                                            <div className="flex items-center gap-2">
                                                <Clock className="h-3.5 w-3.5" />
                                                {format(new Date(log.timestamp), "dd/MM/yyyy HH:mm:ss", { locale: ptBR })}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-2">
                                                <User className="h-3.5 w-3.5 text-muted-foreground" />
                                                {log.usuario}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <span className={`status-badge ${log.acao === 'LOGIN' ? 'status-badge-success' :
                                                    log.acao === 'LOGOUT' ? 'status-badge-info' :
                                                        log.acao.includes('EXPORT') ? 'status-badge-warning' :
                                                            'status-badge-info'
                                                }`}>
                                                {log.acao}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 font-medium">{log.recurso}</td>
                                        <td className="py-3 px-4 text-muted-foreground truncate max-w-xs">
                                            {log.detalhes}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
