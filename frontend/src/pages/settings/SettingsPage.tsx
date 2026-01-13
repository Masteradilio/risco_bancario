import { useTheme, THEMES, THEME_LABELS } from '@/stores/useTheme'
import { useAuth } from '@/stores/useAuth'
import { Palette, User, Bell, Shield, Monitor } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const { user } = useAuth()

    return (
        <div className="space-y-6 max-w-3xl">
            {/* Perfil */}
            <div className="chart-container">
                <div className="flex items-center gap-3 mb-4">
                    <User className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Meu Perfil</h3>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-sm text-muted-foreground">Nome</label>
                        <p className="font-medium mt-1">{user?.nome || '-'}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Email</label>
                        <p className="font-medium mt-1">{user?.email || '-'}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Matrícula</label>
                        <p className="font-medium mt-1">{user?.matricula || '-'}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Departamento</label>
                        <p className="font-medium mt-1">{user?.departamento || '-'}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Perfil</label>
                        <p className="font-medium mt-1">{user?.role || '-'}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Último Login</label>
                        <p className="font-medium mt-1">
                            {user?.lastLogin ? new Date(user.lastLogin).toLocaleString('pt-BR') : '-'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Aparência */}
            <div className="chart-container">
                <div className="flex items-center gap-3 mb-4">
                    <Palette className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Aparência</h3>
                </div>

                <p className="text-sm text-muted-foreground mb-4">
                    Escolha o tema da interface. Você pode alternar entre temas escuros, claros ou seguir as preferências do sistema.
                </p>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {THEMES.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTheme(t)}
                            className={cn(
                                'p-4 rounded-xl border-2 transition-all text-center',
                                theme === t
                                    ? 'border-primary bg-primary/5'
                                    : 'border-border hover:border-primary/50'
                            )}
                        >
                            <div className={cn(
                                'w-10 h-10 rounded-lg mx-auto mb-2',
                                t === 'dark-ocean' && 'bg-[#0a0a14]',
                                t === 'dark-midnight' && 'bg-[#0f0f0f]',
                                t === 'light-snow' && 'bg-[#fafafa] border border-border',
                                t === 'light-cream' && 'bg-[#faf7f2] border border-border',
                                t === 'system' && 'bg-gradient-to-br from-[#0a0a14] to-[#fafafa]',
                            )} />
                            <p className="text-sm font-medium">{THEME_LABELS[t]}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Notificações */}
            <div className="chart-container">
                <div className="flex items-center gap-3 mb-4">
                    <Bell className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Notificações</h3>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium">Alertas de Classificação</p>
                            <p className="text-sm text-muted-foreground">Receber notificações para classificações de alto risco</p>
                        </div>
                        <button className="w-12 h-6 rounded-full bg-primary relative">
                            <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                        </button>
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium">Relatórios Diários</p>
                            <p className="text-sm text-muted-foreground">Resumo diário por email</p>
                        </div>
                        <button className="w-12 h-6 rounded-full bg-muted relative">
                            <span className="absolute left-1 top-1 w-4 h-4 bg-muted-foreground rounded-full" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Segurança */}
            <div className="chart-container">
                <div className="flex items-center gap-3 mb-4">
                    <Shield className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Segurança</h3>
                </div>

                <div className="space-y-4">
                    <button className="w-full text-left px-4 py-3 rounded-lg bg-secondary hover:bg-accent transition-colors">
                        <p className="font-medium">Alterar Senha</p>
                        <p className="text-sm text-muted-foreground">Atualizar senha de acesso</p>
                    </button>

                    <button className="w-full text-left px-4 py-3 rounded-lg bg-secondary hover:bg-accent transition-colors">
                        <p className="font-medium">Sessões Ativas</p>
                        <p className="text-sm text-muted-foreground">Gerenciar dispositivos conectados</p>
                    </button>
                </div>
            </div>
        </div>
    )
}
