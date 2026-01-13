/**
 * Store de Autenticação e RBAC
 * 
 * Implementa controle de acesso baseado em perfis:
 * - ANALISTA: Consultas e classificações
 * - GESTOR: Analista + Exportações + Dashboard completo
 * - AUDITOR: Analista + Logs de auditoria
 * - ADMIN: Acesso total
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'ANALISTA' | 'GESTOR' | 'AUDITOR' | 'ADMIN'

export interface User {
    id: string
    nome: string
    email: string
    matricula: string
    loginWindows?: string
    role: UserRole
    departamento: string
    cargo?: string
    avatar?: string
    isExterno?: boolean
    expiresAt?: string
    lastLogin: string
}

export interface AuditLogEntry {
    id: string
    timestamp: string
    usuario: string
    acao: string
    recurso: string
    detalhes: string
    ip?: string
}

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    auditLogs: AuditLogEntry[]
    login: (email: string, senha: string) => Promise<boolean>
    logout: () => void
    checkPermission: (permission: string) => boolean
    addAuditLog: (acao: string, recurso: string, detalhes: string) => void
    getAuditLogs: () => AuditLogEntry[]
}

const PERMISSIONS: Record<UserRole, string[]> = {
    ANALISTA: [
        'view:prinad',
        'view:ecl',
        'view:propensao',
        'classify:individual',
        'classify:batch',
        'calculate:ecl',
    ],
    GESTOR: [
        'view:prinad',
        'view:ecl',
        'view:propensao',
        'view:dashboard',
        'view:analytics',
        'classify:individual',
        'classify:batch',
        'calculate:ecl',
        'export:pdf',
        'export:csv',
        'export:bacen',
        'generate:xml',
    ],
    AUDITOR: [
        'view:prinad',
        'view:ecl',
        'view:propensao',
        'view:dashboard',
        'view:audit',
        'view:user_activity_logs',
        'export:audit_reports',
        'export:compliance_reports',
    ],
    ADMIN: [
        '*',
        'manage:users',
        'view:system_errors',
        'manage:system_config',
    ],
}

const MOCK_USERS: Record<string, { senha: string; user: User }> = {
    'analista@banco.com': {
        senha: 'analista123',
        user: {
            id: '1',
            nome: 'Maria Silva',
            email: 'analista@banco.com',
            matricula: 'A12345',
            role: 'ANALISTA',
            departamento: 'Crédito',
            lastLogin: new Date().toISOString(),
        },
    },
    'gestor@banco.com': {
        senha: 'gestor123',
        user: {
            id: '2',
            nome: 'João Santos',
            email: 'gestor@banco.com',
            matricula: 'G54321',
            role: 'GESTOR',
            departamento: 'Riscos',
            lastLogin: new Date().toISOString(),
        },
    },
    'auditor@banco.com': {
        senha: 'auditor123',
        user: {
            id: '3',
            nome: 'Ana Costa',
            email: 'auditor@banco.com',
            matricula: 'AU9999',
            role: 'AUDITOR',
            departamento: 'Auditoria Interna',
            lastLogin: new Date().toISOString(),
        },
    },
    'admin@banco.com': {
        senha: 'admin123',
        user: {
            id: '4',
            nome: 'Carlos Admin',
            email: 'admin@banco.com',
            matricula: 'ADM001',
            role: 'ADMIN',
            departamento: 'TI',
            lastLogin: new Date().toISOString(),
        },
    },
}

export const useAuth = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            auditLogs: [],

            login: async (email: string, senha: string) => {
                set({ isLoading: true })
                await new Promise(resolve => setTimeout(resolve, 500))

                const mockUser = MOCK_USERS[email.toLowerCase()]

                if (mockUser && mockUser.senha === senha) {
                    const user = {
                        ...mockUser.user,
                        lastLogin: new Date().toISOString(),
                    }

                    set({
                        user,
                        isAuthenticated: true,
                        isLoading: false
                    })

                    get().addAuditLog('LOGIN', 'SISTEMA', `Usuário ${user.nome} (${user.role}) autenticado`)
                    return true
                }

                set({ isLoading: false })
                return false
            },

            logout: () => {
                const user = get().user
                if (user) {
                    get().addAuditLog('LOGOUT', 'SISTEMA', `Usuário ${user.nome} desconectado`)
                }
                set({ user: null, isAuthenticated: false })
            },

            checkPermission: (permission: string) => {
                const user = get().user
                if (!user) return false

                const userPermissions = PERMISSIONS[user.role]
                if (userPermissions.includes('*')) return true
                return userPermissions.includes(permission)
            },

            addAuditLog: (acao: string, recurso: string, detalhes: string) => {
                const user = get().user
                const newLog: AuditLogEntry = {
                    id: crypto.randomUUID(),
                    timestamp: new Date().toISOString(),
                    usuario: user?.nome || 'Sistema',
                    acao,
                    recurso,
                    detalhes,
                }

                set(state => ({
                    auditLogs: [newLog, ...state.auditLogs].slice(0, 1000)
                }))
            },

            getAuditLogs: () => get().auditLogs,
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                isAuthenticated: state.isAuthenticated,
                auditLogs: state.auditLogs,
            }),
        }
    )
)
