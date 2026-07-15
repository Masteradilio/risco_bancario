import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Eye, EyeOff, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/stores/useAuth'
import { THEME_LABELS, THEMES, useTheme } from '@/stores/useTheme'

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isLoading } = useAuth()
    const { theme, setTheme } = useTheme()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault()
        setError('')
        if (!username || !password) return setError('Preencha usuário e senha')
        if (await login(username, password)) navigate('/perda-esperada')
        else setError('Credenciais inválidas ou API indisponível')
    }

    return <div className="flex min-h-screen items-center justify-center bg-background p-4"><div className="w-full max-w-md space-y-8">
        <div className="text-center"><div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10"><TrendingUp className="h-8 w-8 text-primary" /></div><h1 className="text-2xl font-bold">Risco Bancário</h1><p className="mt-1 text-muted-foreground">Workspace canônico de evidências ECL</p></div>
        <div className="rounded-xl border border-border bg-card p-6 shadow-lg"><form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2"><label htmlFor="username" className="text-sm font-medium">Usuário da API</label><input id="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} className="w-full rounded-lg border bg-input px-4 py-3" /></div>
            <div className="space-y-2"><label htmlFor="password" className="text-sm font-medium">Senha</label><div className="relative"><input id="password" autoComplete="current-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-lg border bg-input px-4 py-3 pr-12" /><button type="button" aria-label="Alternar visibilidade da senha" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">{showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}</button></div></div>
            {error && <div role="alert" className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}</div>}
            <button type="submit" disabled={isLoading} className="w-full rounded-lg bg-primary py-3 font-medium text-primary-foreground disabled:opacity-50">{isLoading ? 'Autenticando…' : 'Entrar'}</button>
        </form><p className="mt-5 border-t pt-4 text-xs text-muted-foreground">Não há credenciais de demonstração embutidas. Crie usuários pelo bootstrap seguro da API.</p></div>
        <div className="flex justify-center gap-2">{THEMES.map((item) => <button key={item} onClick={() => setTheme(item)} className={cn('rounded-lg border px-3 py-1.5 text-xs', theme === item && 'border-primary bg-primary text-primary-foreground')}>{THEME_LABELS[item]}</button>)}</div>
    </div></div>
}
