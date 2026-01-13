'use client'

/**
 * PermissionGate - Componente de Controle de Acesso por Permissão
 * 
 * Renderiza children apenas se o usuário possui a permissão especificada.
 * Caso contrário, renderiza fallback (ou nada).
 * 
 * @example
 * // Oculta botão para quem não tem permissão
 * <PermissionGate permission="export:bacen">
 *   <Button>Exportar XML BACEN</Button>
 * </PermissionGate>
 * 
 * @example
 * // Com mensagem alternativa
 * <PermissionGate 
 *   permission="manage:users" 
 *   fallback={<p>Acesso negado</p>}
 * >
 *   <UserManagement />
 * </PermissionGate>
 * 
 * @example
 * // Múltiplas permissões (qualquer uma)
 * <PermissionGate permission={["view:audit", "view:logs"]}>
 *   <AuditLogs />
 * </PermissionGate>
 */

import { useAuth } from '@/stores/useAuth'
import { ReactNode } from 'react'

interface PermissionGateProps {
    /** Permissão(ões) necessária(s). Se array, basta ter UMA delas. */
    permission: string | string[]
    /** Conteúdo a ser renderizado se tiver permissão */
    children: ReactNode
    /** Conteúdo alternativo se não tiver permissão (opcional) */
    fallback?: ReactNode
    /** Se true, exige TODAS as permissões (AND). Padrão: false (OR) */
    requireAll?: boolean
}

export function PermissionGate({
    permission,
    children,
    fallback = null,
    requireAll = false
}: PermissionGateProps) {
    const { checkPermission, isAuthenticated } = useAuth()

    // Se não está autenticado, não mostra nada
    if (!isAuthenticated) {
        return <>{fallback}</>
    }

    const permissions = Array.isArray(permission) ? permission : [permission]

    let hasPermission: boolean
    if (requireAll) {
        // Precisa ter TODAS as permissões
        hasPermission = permissions.every(p => checkPermission(p))
    } else {
        // Basta ter UMA das permissões
        hasPermission = permissions.some(p => checkPermission(p))
    }

    return hasPermission ? <>{children}</> : <>{fallback}</>
}

/**
 * RoleGate - Componente de Controle de Acesso por Perfil
 * 
 * Renderiza children apenas se o usuário possui um dos perfis especificados.
 * 
 * @example
 * <RoleGate roles={["ADMIN"]}>
 *   <AdminPanel />
 * </RoleGate>
 */

interface RoleGateProps {
    /** Perfis permitidos */
    roles: ('ANALISTA' | 'GESTOR' | 'AUDITOR' | 'ADMIN')[]
    /** Conteúdo a ser renderizado se tiver o perfil */
    children: ReactNode
    /** Conteúdo alternativo se não tiver o perfil (opcional) */
    fallback?: ReactNode
}

export function RoleGate({ roles, children, fallback = null }: RoleGateProps) {
    const { user, isAuthenticated } = useAuth()

    if (!isAuthenticated || !user) {
        return <>{fallback}</>
    }

    const hasRole = roles.includes(user.role)

    return hasRole ? <>{children}</> : <>{fallback}</>
}

/**
 * ReadOnlyGate - Wrapper que desabilita interações para Auditors
 * 
 * Auditores têm acesso somente leitura. Este componente:
 * - Adiciona overlay semi-transparente
 * - Desabilita pointer events
 * - Mostra tooltip explicativo
 * 
 * @example
 * <ReadOnlyGate>
 *   <FormularioECL />
 * </ReadOnlyGate>
 */

interface ReadOnlyGateProps {
    children: ReactNode
    /** Mensagem do tooltip quando hover sobre conteúdo bloqueado */
    message?: string
}

export function ReadOnlyGate({
    children,
    message = "Perfil Auditor: Acesso somente leitura"
}: ReadOnlyGateProps) {
    const { user } = useAuth()

    const isAuditor = user?.role === 'AUDITOR'

    if (!isAuditor) {
        return <>{children}</>
    }

    return (
        <div className="relative group" title={message}>
            <div className="pointer-events-none opacity-80">
                {children}
            </div>
            <div className="absolute inset-0 bg-transparent cursor-not-allowed" />
            {/* Tooltip on hover */}
            <div className="absolute top-0 right-0 m-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="bg-amber-500 text-white text-xs px-2 py-1 rounded shadow-lg">
                    🔒 Somente leitura
                </span>
            </div>
        </div>
    )
}

/**
 * ExternalUserBadge - Badge indicando usuário externo
 * 
 * Mostra badge de "Externo" para auditores externos do BACEN.
 */

export function ExternalUserBadge() {
    const { user } = useAuth()

    // TODO: Adicionar campo is_externo ao User model do frontend
    // Por enquanto, não renderiza nada
    // if (!user?.is_externo) return null

    return null

    // return (
    //     <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
    //         Externo (BACEN)
    //     </span>
    // )
}
