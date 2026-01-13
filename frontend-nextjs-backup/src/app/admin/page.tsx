"use client"

/**
 * Dashboard de Administração do Sistema
 * 
 * Acesso restrito ao perfil ADMIN
 * 
 * Funcionalidades:
 * - CRUD de usuários
 * - Logs de erros do sistema
 * - Configurações do sistema
 */

import { useState, useMemo } from "react"
import { useAuth, UserRole, User } from "@/stores/useAuth"
import { RoleGate } from "@/components/auth/PermissionGate"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
    Shield,
    Users,
    AlertTriangle,
    Settings,
    Plus,
    Pencil,
    Trash2,
    Search,
    RefreshCw,
    CheckCircle,
    XCircle,
    Clock,
    ServerCrash,
    UserPlus,
    UserCheck,
    UserX,
} from "lucide-react"

// Mock de usuários para demonstração
const MOCK_USERS_DATA: User[] = [
    {
        id: "1",
        nome: "Maria Silva",
        email: "maria.silva@banco.local",
        matricula: "A12345",
        loginWindows: "maria.silva",
        role: "ANALISTA",
        departamento: "Crédito",
        cargo: "Analista de Crédito Jr",
        isExterno: false,
        lastLogin: new Date().toISOString(),
    },
    {
        id: "2",
        nome: "João Santos",
        email: "joao.santos@banco.local",
        matricula: "G54321",
        loginWindows: "joao.santos",
        role: "GESTOR",
        departamento: "Riscos",
        cargo: "Gerente de Riscos",
        isExterno: false,
        lastLogin: new Date(Date.now() - 3600000).toISOString(),
    },
    {
        id: "3",
        nome: "Ana Costa",
        email: "ana.costa@banco.local",
        matricula: "AU9999",
        loginWindows: "ana.costa",
        role: "AUDITOR",
        departamento: "Auditoria Interna",
        cargo: "Auditora Sênior",
        isExterno: false,
        lastLogin: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "4",
        nome: "Carlos Admin",
        email: "carlos.admin@banco.local",
        matricula: "ADM001",
        loginWindows: "carlos.admin",
        role: "ADMIN",
        departamento: "TI",
        cargo: "Administrador de Sistemas",
        isExterno: false,
        lastLogin: new Date().toISOString(),
    },
    {
        id: "5",
        nome: "Pedro Externo",
        email: "pedro.bacen@bcb.gov.br",
        matricula: "EXT001",
        loginWindows: "pedro.externo",
        role: "AUDITOR",
        departamento: "BACEN",
        cargo: "Auditor Externo",
        isExterno: true,
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        lastLogin: new Date(Date.now() - 7200000).toISOString(),
    },
]

// Mock de erros do sistema
const MOCK_SYSTEM_ERRORS = [
    { id: 1, nivel: "ERROR", modulo: "prinad", mensagem: "Timeout ao consultar SCR BACEN", timestamp: new Date(Date.now() - 300000).toISOString() },
    { id: 2, nivel: "WARNING", modulo: "ecl", mensagem: "Cache de cenários expirado, recalculando", timestamp: new Date(Date.now() - 600000).toISOString() },
    { id: 3, nivel: "ERROR", modulo: "auth", mensagem: "Falha na validação de token JWT", timestamp: new Date(Date.now() - 900000).toISOString() },
    { id: 4, nivel: "CRITICAL", modulo: "propensao", mensagem: "Modelo XGBoost não encontrado em /models", timestamp: new Date(Date.now() - 1800000).toISOString() },
    { id: 5, nivel: "INFO", modulo: "ecl", mensagem: "Pipeline ECL concluído com sucesso", timestamp: new Date(Date.now() - 3600000).toISOString() },
]

const ROLE_COLORS: Record<UserRole, string> = {
    ANALISTA: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    GESTOR: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    AUDITOR: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    ADMIN: "bg-red-500/10 text-red-500 border-red-500/20",
}

const NIVEL_COLORS: Record<string, string> = {
    DEBUG: "bg-slate-500/10 text-slate-500",
    INFO: "bg-blue-500/10 text-blue-500",
    WARNING: "bg-amber-500/10 text-amber-500",
    ERROR: "bg-red-500/10 text-red-500",
    CRITICAL: "bg-red-700/20 text-red-600 font-bold",
}

export default function AdminPage() {
    const { user, checkPermission, addAuditLog } = useAuth()
    const [users, setUsers] = useState<User[]>(MOCK_USERS_DATA)
    const [errors] = useState(MOCK_SYSTEM_ERRORS)
    const [search, setSearch] = useState("")
    const [filterRole, setFilterRole] = useState<string>("ALL")
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [editingUser, setEditingUser] = useState<User | null>(null)
    const [activeTab, setActiveTab] = useState<"users" | "errors" | "settings">("users")

    // Form state
    const [formData, setFormData] = useState({
        nome: "",
        email: "",
        matricula: "",
        loginWindows: "",
        role: "ANALISTA" as UserRole,
        departamento: "",
        cargo: "",
        isExterno: false,
    })

    // Filtrar usuários
    const filteredUsers = useMemo(() => {
        return users.filter(u => {
            if (search) {
                const searchLower = search.toLowerCase()
                if (!u.nome.toLowerCase().includes(searchLower) &&
                    !u.email.toLowerCase().includes(searchLower) &&
                    !u.matricula.toLowerCase().includes(searchLower)) {
                    return false
                }
            }
            if (filterRole !== "ALL" && u.role !== filterRole) {
                return false
            }
            return true
        })
    }, [users, search, filterRole])

    // Estatísticas
    const stats = useMemo(() => ({
        total: users.length,
        ativos: users.filter(u => !u.expiresAt || new Date(u.expiresAt) > new Date()).length,
        externos: users.filter(u => u.isExterno).length,
        errorsCount: errors.filter(e => e.nivel === "ERROR" || e.nivel === "CRITICAL").length,
    }), [users, errors])

    // Handlers
    const handleCreateUser = () => {
        setEditingUser(null)
        setFormData({
            nome: "",
            email: "",
            matricula: "",
            loginWindows: "",
            role: "ANALISTA",
            departamento: "",
            cargo: "",
            isExterno: false,
        })
        setIsDialogOpen(true)
    }

    const handleEditUser = (userToEdit: User) => {
        setEditingUser(userToEdit)
        setFormData({
            nome: userToEdit.nome,
            email: userToEdit.email,
            matricula: userToEdit.matricula,
            loginWindows: userToEdit.loginWindows || "",
            role: userToEdit.role,
            departamento: userToEdit.departamento,
            cargo: userToEdit.cargo || "",
            isExterno: userToEdit.isExterno || false,
        })
        setIsDialogOpen(true)
    }

    const handleSaveUser = () => {
        if (editingUser) {
            // Atualizar
            setUsers(prev => prev.map(u =>
                u.id === editingUser.id
                    ? { ...u, ...formData, lastLogin: u.lastLogin }
                    : u
            ))
            addAuditLog("UPDATE_USER", `/admin/usuarios/${editingUser.id}`, `Atualizou usuário ${formData.nome}`)
        } else {
            // Criar
            const newUser: User = {
                id: String(Date.now()),
                ...formData,
                lastLogin: new Date().toISOString(),
                expiresAt: formData.isExterno
                    ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
                    : undefined,
            }
            setUsers(prev => [...prev, newUser])
            addAuditLog("CREATE_USER", "/admin/usuarios", `Criou usuário ${formData.nome} (${formData.role})`)
        }
        setIsDialogOpen(false)
    }

    const handleDeleteUser = (userToDelete: User) => {
        if (userToDelete.id === user?.id) {
            alert("Você não pode desativar sua própria conta!")
            return
        }
        if (confirm(`Deseja desativar o usuário ${userToDelete.nome}?`)) {
            setUsers(prev => prev.filter(u => u.id !== userToDelete.id))
            addAuditLog("DELETE_USER", `/admin/usuarios/${userToDelete.id}`, `Desativou usuário ${userToDelete.nome}`)
        }
    }

    // Verificação de permissão usando RoleGate
    return (
        <RoleGate
            roles={["ADMIN"]}
            fallback={
                <div className="flex items-center justify-center min-h-[60vh]">
                    <Card className="w-full max-w-md text-center">
                        <CardContent className="pt-6">
                            <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                            <h2 className="text-xl font-semibold mb-2">Acesso Restrito</h2>
                            <p className="text-muted-foreground">
                                Esta área é restrita para Administradores do sistema.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            }
        >
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <Shield className="h-8 w-8 text-red-500" />
                        Administração do Sistema
                    </h1>
                    <p className="text-muted-foreground">
                        Gerenciamento de usuários, logs e configurações
                    </p>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                    <Card className="cursor-pointer hover:bg-accent/50" onClick={() => setActiveTab("users")}>
                        <CardHeader className="pb-2">
                            <CardDescription>Total de Usuários</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-2">
                                <Users className="h-5 w-5 text-blue-500" />
                                <span className="text-2xl font-bold">{stats.total}</span>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="cursor-pointer hover:bg-accent/50" onClick={() => setActiveTab("users")}>
                        <CardHeader className="pb-2">
                            <CardDescription>Usuários Ativos</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-2">
                                <UserCheck className="h-5 w-5 text-green-500" />
                                <span className="text-2xl font-bold">{stats.ativos}</span>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="cursor-pointer hover:bg-accent/50" onClick={() => setActiveTab("users")}>
                        <CardHeader className="pb-2">
                            <CardDescription>Auditores Externos</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-2">
                                <UserX className="h-5 w-5 text-amber-500" />
                                <span className="text-2xl font-bold">{stats.externos}</span>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="cursor-pointer hover:bg-accent/50" onClick={() => setActiveTab("errors")}>
                        <CardHeader className="pb-2">
                            <CardDescription>Erros do Sistema</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5 text-red-500" />
                                <span className="text-2xl font-bold">{stats.errorsCount}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 border-b">
                    <Button
                        variant={activeTab === "users" ? "default" : "ghost"}
                        onClick={() => setActiveTab("users")}
                        className="gap-2"
                    >
                        <Users className="h-4 w-4" />
                        Usuários
                    </Button>
                    <Button
                        variant={activeTab === "errors" ? "default" : "ghost"}
                        onClick={() => setActiveTab("errors")}
                        className="gap-2"
                    >
                        <ServerCrash className="h-4 w-4" />
                        Erros do Sistema
                    </Button>
                    <Button
                        variant={activeTab === "settings" ? "default" : "ghost"}
                        onClick={() => setActiveTab("settings")}
                        className="gap-2"
                    >
                        <Settings className="h-4 w-4" />
                        Configurações
                    </Button>
                </div>

                {/* Tab Content: Users */}
                {activeTab === "users" && (
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Gerenciamento de Usuários</CardTitle>
                                <CardDescription>
                                    Crie, edite e gerencie os usuários do sistema
                                </CardDescription>
                            </div>
                            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                                <DialogTrigger asChild>
                                    <Button onClick={handleCreateUser} className="gap-2">
                                        <UserPlus className="h-4 w-4" />
                                        Novo Usuário
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[500px]">
                                    <DialogHeader>
                                        <DialogTitle>
                                            {editingUser ? "Editar Usuário" : "Novo Usuário"}
                                        </DialogTitle>
                                        <DialogDescription>
                                            {editingUser
                                                ? "Atualize os dados do usuário"
                                                : "Preencha os dados para criar um novo usuário"}
                                        </DialogDescription>
                                    </DialogHeader>
                                    <div className="grid gap-4 py-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="nome">Nome Completo</Label>
                                                <Input
                                                    id="nome"
                                                    value={formData.nome}
                                                    onChange={e => setFormData({ ...formData, nome: e.target.value })}
                                                    placeholder="Maria Silva"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="email">Email</Label>
                                                <Input
                                                    id="email"
                                                    type="email"
                                                    value={formData.email}
                                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                                    placeholder="maria@banco.local"
                                                />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="matricula">Matrícula</Label>
                                                <Input
                                                    id="matricula"
                                                    value={formData.matricula}
                                                    onChange={e => setFormData({ ...formData, matricula: e.target.value })}
                                                    placeholder="A12345"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="loginWindows">Login Windows</Label>
                                                <Input
                                                    id="loginWindows"
                                                    value={formData.loginWindows}
                                                    onChange={e => setFormData({ ...formData, loginWindows: e.target.value })}
                                                    placeholder="maria.silva"
                                                />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="role">Perfil de Acesso</Label>
                                                <Select
                                                    value={formData.role}
                                                    onValueChange={(v) => setFormData({ ...formData, role: v as UserRole })}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="ANALISTA">Analista</SelectItem>
                                                        <SelectItem value="GESTOR">Gestor</SelectItem>
                                                        <SelectItem value="AUDITOR">Auditor</SelectItem>
                                                        <SelectItem value="ADMIN">Admin</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="departamento">Departamento</Label>
                                                <Input
                                                    id="departamento"
                                                    value={formData.departamento}
                                                    onChange={e => setFormData({ ...formData, departamento: e.target.value })}
                                                    placeholder="Crédito"
                                                />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="cargo">Cargo</Label>
                                            <Input
                                                id="cargo"
                                                value={formData.cargo}
                                                onChange={e => setFormData({ ...formData, cargo: e.target.value })}
                                                placeholder="Analista de Crédito Jr"
                                            />
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <Switch
                                                id="isExterno"
                                                checked={formData.isExterno}
                                                onCheckedChange={checked => setFormData({ ...formData, isExterno: checked })}
                                            />
                                            <Label htmlFor="isExterno">
                                                Auditor Externo (expira em 30 dias)
                                            </Label>
                                        </div>
                                    </div>
                                    <DialogFooter>
                                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                                            Cancelar
                                        </Button>
                                        <Button onClick={handleSaveUser}>
                                            {editingUser ? "Salvar Alterações" : "Criar Usuário"}
                                        </Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        </CardHeader>
                        <CardContent>
                            {/* Filters */}
                            <div className="flex gap-4 mb-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Buscar por nome, email ou matrícula..."
                                        value={search}
                                        onChange={e => setSearch(e.target.value)}
                                        className="pl-10"
                                    />
                                </div>
                                <Select value={filterRole} onValueChange={setFilterRole}>
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="Perfil" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="ALL">Todos</SelectItem>
                                        <SelectItem value="ANALISTA">Analista</SelectItem>
                                        <SelectItem value="GESTOR">Gestor</SelectItem>
                                        <SelectItem value="AUDITOR">Auditor</SelectItem>
                                        <SelectItem value="ADMIN">Admin</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Users Table */}
                            <div className="border rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-muted">
                                        <tr>
                                            <th className="p-3 text-left">Nome</th>
                                            <th className="p-3 text-left">Email</th>
                                            <th className="p-3 text-left">Matrícula</th>
                                            <th className="p-3 text-left">Perfil</th>
                                            <th className="p-3 text-left">Departamento</th>
                                            <th className="p-3 text-left">Status</th>
                                            <th className="p-3 text-center">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredUsers.map(u => (
                                            <tr key={u.id} className="border-t hover:bg-muted/50">
                                                <td className="p-3">
                                                    <div className="font-medium">{u.nome}</div>
                                                    {u.cargo && <div className="text-xs text-muted-foreground">{u.cargo}</div>}
                                                </td>
                                                <td className="p-3">{u.email}</td>
                                                <td className="p-3">{u.matricula}</td>
                                                <td className="p-3">
                                                    <Badge variant="outline" className={ROLE_COLORS[u.role]}>
                                                        {u.role}
                                                    </Badge>
                                                </td>
                                                <td className="p-3">{u.departamento}</td>
                                                <td className="p-3">
                                                    {u.isExterno ? (
                                                        <Badge variant="outline" className="bg-amber-500/10 text-amber-500">
                                                            <Clock className="h-3 w-3 mr-1" />
                                                            Externo
                                                        </Badge>
                                                    ) : (
                                                        <Badge variant="outline" className="bg-green-500/10 text-green-500">
                                                            <CheckCircle className="h-3 w-3 mr-1" />
                                                            Ativo
                                                        </Badge>
                                                    )}
                                                </td>
                                                <td className="p-3">
                                                    <div className="flex items-center justify-center gap-2">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => handleEditUser(u)}
                                                        >
                                                            <Pencil className="h-4 w-4" />
                                                        </Button>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => handleDeleteUser(u)}
                                                            disabled={u.id === user?.id}
                                                        >
                                                            <Trash2 className="h-4 w-4 text-red-500" />
                                                        </Button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Tab Content: Errors */}
                {activeTab === "errors" && (
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <ServerCrash className="h-5 w-5" />
                                    Logs de Erros do Sistema
                                </CardTitle>
                                <CardDescription>
                                    Monitore erros e problemas do sistema
                                </CardDescription>
                            </div>
                            <Button variant="outline" className="gap-2">
                                <RefreshCw className="h-4 w-4" />
                                Atualizar
                            </Button>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {errors.map(error => (
                                    <div
                                        key={error.id}
                                        className={`p-4 rounded-lg border ${error.nivel === 'CRITICAL' ? 'border-red-500/50 bg-red-500/5' :
                                                error.nivel === 'ERROR' ? 'border-red-500/30 bg-red-500/5' :
                                                    error.nivel === 'WARNING' ? 'border-amber-500/30 bg-amber-500/5' :
                                                        'border-border'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <Badge className={NIVEL_COLORS[error.nivel]}>
                                                    {error.nivel}
                                                </Badge>
                                                <code className="text-xs bg-muted px-2 py-1 rounded">
                                                    {error.modulo}
                                                </code>
                                            </div>
                                            <span className="text-xs text-muted-foreground">
                                                {new Date(error.timestamp).toLocaleString('pt-BR')}
                                            </span>
                                        </div>
                                        <p className="mt-2 text-sm">{error.mensagem}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Tab Content: Settings */}
                {activeTab === "settings" && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                Configurações do Sistema
                            </CardTitle>
                            <CardDescription>
                                Ajuste configurações globais do sistema
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-4 rounded-lg border">
                                    <div>
                                        <h4 className="font-medium">Timeout de Sessão</h4>
                                        <p className="text-sm text-muted-foreground">
                                            Tempo de inatividade para encerrar sessão
                                        </p>
                                    </div>
                                    <Select defaultValue="30">
                                        <SelectTrigger className="w-[100px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="15">15 min</SelectItem>
                                            <SelectItem value="30">30 min</SelectItem>
                                            <SelectItem value="60">60 min</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-lg border">
                                    <div>
                                        <h4 className="font-medium">Validade de Usuários Externos</h4>
                                        <p className="text-sm text-muted-foreground">
                                            Dias até expiração de contas externas
                                        </p>
                                    </div>
                                    <Select defaultValue="30">
                                        <SelectTrigger className="w-[100px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="7">7 dias</SelectItem>
                                            <SelectItem value="15">15 dias</SelectItem>
                                            <SelectItem value="30">30 dias</SelectItem>
                                            <SelectItem value="60">60 dias</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex items-center justify-between p-4 rounded-lg border">
                                    <div>
                                        <h4 className="font-medium">Logs de Auditoria</h4>
                                        <p className="text-sm text-muted-foreground">
                                            Retenção de logs de atividade
                                        </p>
                                    </div>
                                    <Select defaultValue="90">
                                        <SelectTrigger className="w-[100px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="30">30 dias</SelectItem>
                                            <SelectItem value="60">60 dias</SelectItem>
                                            <SelectItem value="90">90 dias</SelectItem>
                                            <SelectItem value="365">1 ano</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </RoleGate>
    )
}
