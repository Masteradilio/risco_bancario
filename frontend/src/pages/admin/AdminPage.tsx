import { Users, Shield, Settings, AlertTriangle, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

const mockUsers = [
    { id: '1', nome: 'Maria Silva', email: 'analista@banco.com', role: 'ANALISTA', departamento: 'Crédito', ativo: true },
    { id: '2', nome: 'João Santos', email: 'gestor@banco.com', role: 'GESTOR', departamento: 'Riscos', ativo: true },
    { id: '3', nome: 'Ana Costa', email: 'auditor@banco.com', role: 'AUDITOR', departamento: 'Auditoria', ativo: true },
    { id: '4', nome: 'Carlos Admin', email: 'admin@banco.com', role: 'ADMIN', departamento: 'TI', ativo: true },
]

export default function AdminPage() {
    return (
        <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Usuários Ativos</p>
                            <p className="text-2xl font-bold mt-1">4</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-emerald-500/10">
                            <Users className="h-5 w-5 text-emerald-500" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Analistas</p>
                            <p className="text-2xl font-bold mt-1">1</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-primary/10">
                            <Shield className="h-5 w-5 text-primary" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Gestores</p>
                            <p className="text-2xl font-bold mt-1">1</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-amber-500/10">
                            <Settings className="h-5 w-5 text-amber-500" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">Erros do Sistema</p>
                            <p className="text-2xl font-bold mt-1">0</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-red-500/10">
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Users Table */}
            <div className="chart-container">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Gerenciamento de Usuários</h3>
                    <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm">
                        <Plus className="h-4 w-4" />
                        Novo Usuário
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-3 px-4">Nome</th>
                                <th className="text-left py-3 px-4">Email</th>
                                <th className="text-left py-3 px-4">Perfil</th>
                                <th className="text-left py-3 px-4">Departamento</th>
                                <th className="text-left py-3 px-4">Status</th>
                                <th className="text-left py-3 px-4">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mockUsers.map((user) => (
                                <tr key={user.id} className="border-b border-border hover:bg-muted/50">
                                    <td className="py-3 px-4 font-medium">{user.nome}</td>
                                    <td className="py-3 px-4 text-muted-foreground">{user.email}</td>
                                    <td className="py-3 px-4">
                                        <span className={cn(
                                            'status-badge',
                                            user.role === 'ADMIN' && 'bg-red-500/10 text-red-500',
                                            user.role === 'GESTOR' && 'bg-amber-500/10 text-amber-500',
                                            user.role === 'AUDITOR' && 'bg-blue-500/10 text-blue-500',
                                            user.role === 'ANALISTA' && 'bg-emerald-500/10 text-emerald-500',
                                        )}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4">{user.departamento}</td>
                                    <td className="py-3 px-4">
                                        <span className="status-badge status-badge-success">
                                            Ativo
                                        </span>
                                    </td>
                                    <td className="py-3 px-4">
                                        <button className="text-primary hover:underline text-sm">
                                            Editar
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
