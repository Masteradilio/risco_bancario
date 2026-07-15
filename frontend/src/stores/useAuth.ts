import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type UserRole = 'ANALYST' | 'MANAGER' | 'AUDITOR' | 'ADMIN'

export interface User {
    id: string
    nome: string
    email: string
    matricula: string
    role: UserRole
    departamento: string
    lastLogin: string
}

interface JwtClaims {
    sub: string
    username: string
    role: UserRole
    exp: number
}

interface AuthState {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (username: string, password: string) => Promise<boolean>
    logout: () => Promise<void>
    checkPermission: (permission: string) => boolean
}

const API_URL = import.meta.env.VITE_API_URL ?? ''

const PERMISSIONS: Record<UserRole, readonly string[]> = {
    ANALYST: ['ecl:calculate:individual', 'ecl:result:read'],
    MANAGER: [
        'ecl:calculate:individual',
        'ecl:calculate:portfolio',
        'ecl:result:read',
        'scenario:approve',
        'regulatory:export',
    ],
    AUDITOR: ['ecl:result:read', 'audit:read'],
    ADMIN: ['user:manage', 'audit:read'],
}

function decodeClaims(token: string): JwtClaims {
    const encoded = token.split('.')[1]
    if (!encoded) throw new Error('invalid JWT')
    const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(decodeURIComponent(escape(atob(normalized)))) as JwtClaims
}

export const useAuth = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,

            login: async (username, password) => {
                set({ isLoading: true })
                try {
                    const response = await fetch(`${API_URL}/api/v1/auth/token`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password }),
                    })
                    if (!response.ok) return false
                    const { access_token: token } = (await response.json()) as { access_token: string }
                    const claims = decodeClaims(token)
                    if (claims.exp * 1000 <= Date.now()) return false
                    set({
                        token,
                        user: {
                            id: claims.sub,
                            nome: claims.username,
                            email: claims.username,
                            matricula: claims.sub,
                            role: claims.role,
                            departamento: 'Não informado pela API',
                            lastLogin: new Date().toISOString(),
                        },
                        isAuthenticated: true,
                    })
                    return true
                } catch {
                    return false
                } finally {
                    set({ isLoading: false })
                }
            },

            logout: async () => {
                const token = get().token
                try {
                    if (token) {
                        await fetch(`${API_URL}/api/v1/auth/logout`, {
                            method: 'POST',
                            headers: { Authorization: `Bearer ${token}` },
                        })
                    }
                } finally {
                    set({ user: null, token: null, isAuthenticated: false })
                }
            },

            checkPermission: (permission) => {
                const user = get().user
                return user ? PERMISSIONS[user.role].includes(permission) : false
            },
        }),
        {
            name: 'risk-session',
            storage: createJSONStorage(() => sessionStorage),
            partialize: ({ user, token, isAuthenticated }) => ({ user, token, isAuthenticated }),
            onRehydrateStorage: () => (state) => {
                if (!state?.token) return
                try {
                    if (decodeClaims(state.token).exp * 1000 <= Date.now()) {
                        state.user = null
                        state.token = null
                        state.isAuthenticated = false
                    }
                } catch {
                    state.user = null
                    state.token = null
                    state.isAuthenticated = false
                }
            },
        },
    ),
)

export function apiUrl(path: string): string {
    return `${API_URL}${path}`
}
