import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/stores/useAuth'
import { useTheme, THEMES, THEME_LABELS } from '@/stores/useTheme'
import { TrendingUp, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function LoginPage() {
    const navigate = useNavigate()
    const { login, isLoading } = useAuth()
    const { theme, setTheme, resolvedTheme } = useTheme()

    const [email, setEmail] = useState('')
    const [senha, setSenha] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        if (!email || !senha) {
            setError('Preencha todos os campos')
            return
        }

        const success = await login(email, senha)
        if (success) {
            navigate('/')
        } else {
            setError('Email ou senha inválidos')
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <div className="w-full max-w-md space-y-8">
                {/* Logo */}
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
                        <TrendingUp className="h-8 w-8 text-primary" />
                    </div>
                    <h1 className="text-2xl font-bold text-foreground">Propensão</h1>
                    <p className="text-muted-foreground mt-1">Sistema de Gestão de Risco Bancário</p>
                </div>

                {/* Form */}
                <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Email */}
                        <div className="space-y-2">
                            <label htmlFor="email" className="text-sm font-medium text-foreground">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="seu.email@banco.com"
                                className={cn(
                                    'w-full px-4 py-3 rounded-lg border bg-input text-foreground',
                                    'placeholder:text-muted-foreground',
                                    'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                                    'transition-all duration-200'
                                )}
                            />
                        </div>

                        {/* Senha */}
                        <div className="space-y-2">
                            <label htmlFor="senha" className="text-sm font-medium text-foreground">
                                Senha
                            </label>
                            <div className="relative">
                                <input
                                    id="senha"
                                    type={showPassword ? 'text' : 'password'}
                                    value={senha}
                                    onChange={(e) => setSenha(e.target.value)}
                                    placeholder="••••••••"
                                    className={cn(
                                        'w-full px-4 py-3 rounded-lg border bg-input text-foreground',
                                        'placeholder:text-muted-foreground',
                                        'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
                                        'transition-all duration-200 pr-12'
                                    )}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        {/* Error */}
                        {error && (
                            <div className="flex items-center gap-2 text-destructive text-sm">
                                <AlertCircle className="h-4 w-4" />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={cn(
                                'w-full py-3 rounded-lg font-medium transition-all duration-200',
                                'bg-primary text-primary-foreground',
                                'hover:opacity-90 active:scale-[0.98]',
                                'disabled:opacity-50 disabled:cursor-not-allowed'
                            )}
                        >
                            {isLoading ? 'Entrando...' : 'Entrar'}
                        </button>
                    </form>

                    {/* Dica de usuários de teste */}
                    <div className="mt-6 pt-6 border-t border-border">
                        <p className="text-xs text-muted-foreground text-center mb-3">
                            Usuários de teste:
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="bg-secondary/50 rounded-lg p-2">
                                <p className="font-medium">Analista</p>
                                <p className="text-muted-foreground">analista@banco.com</p>
                            </div>
                            <div className="bg-secondary/50 rounded-lg p-2">
                                <p className="font-medium">Gestor</p>
                                <p className="text-muted-foreground">gestor@banco.com</p>
                            </div>
                            <div className="bg-secondary/50 rounded-lg p-2">
                                <p className="font-medium">Auditor</p>
                                <p className="text-muted-foreground">auditor@banco.com</p>
                            </div>
                            <div className="bg-secondary/50 rounded-lg p-2">
                                <p className="font-medium">Admin</p>
                                <p className="text-muted-foreground">admin@banco.com</p>
                            </div>
                        </div>
                        <p className="text-xs text-muted-foreground text-center mt-2">
                            Senha: [role]123 (ex: admin123)
                        </p>
                    </div>
                </div>

                {/* Theme Selector */}
                <div className="flex justify-center gap-2">
                    {THEMES.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTheme(t)}
                            className={cn(
                                'px-3 py-1.5 rounded-lg text-xs transition-all',
                                'border border-border',
                                theme === t
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'bg-card hover:bg-accent'
                            )}
                        >
                            {THEME_LABELS[t]}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    )
}
