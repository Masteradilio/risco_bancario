import { Palette, Shield, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/stores/useAuth'
import { THEME_LABELS, THEMES, useTheme } from '@/stores/useTheme'

export default function SettingsPage() {
    const { theme, setTheme } = useTheme()
    const user = useAuth((state) => state.user)
    return <div className="max-w-3xl space-y-6">
        <section className="chart-container"><div className="mb-4 flex items-center gap-3"><User className="h-5 w-5 text-primary" /><h3 className="font-semibold">Identidade da sessão</h3></div><div className="grid grid-cols-2 gap-4 text-sm"><div><span className="text-muted-foreground">Usuário</span><p className="font-medium">{user?.nome ?? '-'}</p></div><div><span className="text-muted-foreground">ID persistido</span><p className="break-all font-mono text-xs">{user?.id ?? '-'}</p></div><div><span className="text-muted-foreground">Perfil RBAC</span><p className="font-medium">{user?.role ?? '-'}</p></div><div><span className="text-muted-foreground">Início local</span><p>{user?.lastLogin ? new Date(user.lastLogin).toLocaleString('pt-BR') : '-'}</p></div></div></section>
        <section className="chart-container"><div className="mb-4 flex items-center gap-3"><Palette className="h-5 w-5 text-primary" /><h3 className="font-semibold">Aparência local</h3></div><div className="grid grid-cols-2 gap-3 md:grid-cols-5">{THEMES.map((item) => <button key={item} onClick={() => setTheme(item)} className={cn('rounded-xl border-2 p-4 text-sm', theme === item ? 'border-primary bg-primary/5' : 'border-border')}>{THEME_LABELS[item]}</button>)}</div></section>
        <section className="chart-container"><div className="mb-3 flex items-center gap-3"><Shield className="h-5 w-5 text-primary" /><h3 className="font-semibold">Segurança</h3></div><p className="text-sm text-muted-foreground">A sessão usa JWT curto e revogável emitido pela API. O token fica somente no armazenamento da sessão do navegador; perfis e permissões são revalidados no servidor em cada chamada.</p></section>
    </div>
}
