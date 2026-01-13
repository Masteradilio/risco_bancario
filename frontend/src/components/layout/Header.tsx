import { useLocation } from 'react-router-dom'
import { useAuth } from '@/stores/useAuth'
import { useTheme, THEMES, THEME_LABELS, type Theme } from '@/stores/useTheme'
import {
    LogOut,
    User,
    Palette,
    Moon,
    Sun,
    Monitor,
    ChevronDown,
} from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

// Mapear paths para títulos
const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
    '/': { title: 'Dashboard', subtitle: 'Visão geral do sistema' },
    '/prinad': { title: 'PRINAD', subtitle: 'Classificação de Risco de Crédito' },
    '/propensao': { title: 'Propensão', subtitle: 'Otimização de Limites de Crédito' },
    '/perda-esperada': { title: 'Perda Esperada', subtitle: 'Cálculo ECL - IFRS 9' },
    '/perda-esperada/calculo': { title: 'Cálculo ECL', subtitle: 'Perda Esperada por Contrato' },
    '/perda-esperada/estagios': { title: 'Estágios IFRS 9', subtitle: 'Classificação em 3 Estágios' },
    '/perda-esperada/grupos': { title: 'Grupos Homogêneos', subtitle: 'Segmentação por Perfil de Risco' },
    '/perda-esperada/forward-looking': { title: 'Forward Looking', subtitle: 'Cenários Macroeconômicos' },
    '/perda-esperada/lgd': { title: 'LGD Segmentado', subtitle: 'Perda Dada a Inadimplência' },
    '/perda-esperada/cura': { title: 'Sistema de Cura', subtitle: 'Reversão de Estágios - Art. 41' },
    '/perda-esperada/writeoff': { title: 'Write-off', subtitle: 'Baixas e Recuperações' },
    '/perda-esperada/exportacao': { title: 'Exportação BACEN', subtitle: 'Doc3040 - Resolução CMN 4966' },
    '/perda-esperada/pipeline': { title: 'Pipeline ECL', subtitle: 'Execução Completa' },
    '/auditoria': { title: 'Auditoria', subtitle: 'Logs e Conformidade' },
    '/relatorios': { title: 'Relatórios', subtitle: 'Documentos e Exportações' },
    '/admin': { title: 'Administração', subtitle: 'Gerenciamento de Usuários' },
    '/settings': { title: 'Configurações', subtitle: 'Preferências do Sistema' },
}

function ThemeIcon({ theme }: { theme: Theme }) {
    if (theme === 'system') return <Monitor className="h-4 w-4" />
    if (theme.startsWith('dark')) return <Moon className="h-4 w-4" />
    return <Sun className="h-4 w-4" />
}

export default function Header() {
    const location = useLocation()
    const { user, logout } = useAuth()
    const { theme, setTheme } = useTheme()
    const [showThemeMenu, setShowThemeMenu] = useState(false)
    const [showUserMenu, setShowUserMenu] = useState(false)
    const themeMenuRef = useRef<HTMLDivElement>(null)
    const userMenuRef = useRef<HTMLDivElement>(null)

    // Fechar menus ao clicar fora
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (themeMenuRef.current && !themeMenuRef.current.contains(event.target as Node)) {
                setShowThemeMenu(false)
            }
            if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
                setShowUserMenu(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const pageInfo = PAGE_TITLES[location.pathname] || {
        title: 'Página',
        subtitle: ''
    }

    return (
        <header className="relative z-50 flex items-center justify-between px-6 py-4 border-b border-border bg-background/80 backdrop-blur-sm">
            {/* Título da página */}
            <div>
                <h2 className="text-xl font-semibold text-foreground">{pageInfo.title}</h2>
                {pageInfo.subtitle && (
                    <p className="text-sm text-muted-foreground">{pageInfo.subtitle}</p>
                )}
            </div>

            {/* Ações */}
            <div className="flex items-center gap-3">
                {/* Seletor de Tema */}
                <div className="relative" ref={themeMenuRef}>
                    <button
                        onClick={() => setShowThemeMenu(!showThemeMenu)}
                        className={cn(
                            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
                            'bg-secondary hover:bg-accent transition-colors'
                        )}
                    >
                        <Palette className="h-4 w-4" />
                        <span className="hidden sm:inline">{THEME_LABELS[theme]}</span>
                        <ChevronDown className="h-4 w-4" />
                    </button>

                    {showThemeMenu && (
                        <>
                            {/* Overlay invisível para capturar cliques fora */}
                            <div
                                className="fixed inset-0 z-[9998]"
                                onClick={() => setShowThemeMenu(false)}
                            />
                            {/* Menu dropdown - posição absoluta abaixo do botão */}
                            <div
                                className="absolute right-0 top-full mt-2 w-52 rounded-xl border-2 border-primary/20 bg-popover shadow-2xl z-[9999] animate-fade-in"
                                style={{
                                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                                }}
                            >
                                <div className="p-2">
                                    <p className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                                        Escolher Tema
                                    </p>
                                    {THEMES.map((t) => (
                                        <button
                                            key={t}
                                            onClick={() => {
                                                setTheme(t)
                                                setShowThemeMenu(false)
                                            }}
                                            className={cn(
                                                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
                                                'hover:bg-accent',
                                                theme === t && 'bg-primary text-primary-foreground font-medium'
                                            )}
                                        >
                                            <ThemeIcon theme={t} />
                                            <span>{THEME_LABELS[t]}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* Menu do Usuário */}
                <div className="relative" ref={userMenuRef}>
                    <button
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
                    >
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-medium">
                            {user?.nome?.charAt(0) || 'U'}
                        </div>
                        <div className="hidden sm:block text-left">
                            <p className="text-sm font-medium">{user?.nome || 'Usuário'}</p>
                            <p className="text-xs text-muted-foreground">{user?.role}</p>
                        </div>
                        <ChevronDown className="h-4 w-4" />
                    </button>

                    {showUserMenu && (
                        <div className="absolute right-0 top-full mt-2 w-56 rounded-lg border border-border bg-popover shadow-lg z-50 animate-fade-in">
                            <div className="p-3 border-b border-border">
                                <p className="text-sm font-medium">{user?.nome}</p>
                                <p className="text-xs text-muted-foreground">{user?.email}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Matrícula: {user?.matricula}
                                </p>
                            </div>
                            <div className="p-1">
                                <button
                                    onClick={() => setShowUserMenu(false)}
                                    className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-accent transition-colors"
                                >
                                    <User className="h-4 w-4" />
                                    <span>Meu Perfil</span>
                                </button>
                                <button
                                    onClick={() => {
                                        logout()
                                        setShowUserMenu(false)
                                    }}
                                    className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-destructive hover:bg-destructive/10 transition-colors"
                                >
                                    <LogOut className="h-4 w-4" />
                                    <span>Sair</span>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    )
}
