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

                    {/* Acesso Rápido DEMO */}
                    <div className="mt-6 pt-6 border-t border-border">
                        <p className="text-xs text-muted-foreground text-center mb-4 uppercase tracking-wider font-semibold">
                            Acesso Rápido (DEMO)
                        </p>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                type="button"
                                onClick={() => { setEmail('analista@banco.com'); setSenha('analista123'); }}
                                className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 rounded-lg border border-blue-200 dark:border-blue-800 transition-all group"
                            >
                                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                                    <TrendingUp className="w-4 h-4 text-white" />
                                </div>
                                <div className="text-left">
                                    <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">Analista</p>
                                    <p className="text-xs text-blue-500 dark:text-blue-400">analista@banco.com</p>
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => { setEmail('gestor@banco.com'); setSenha('gestor123'); }}
                                className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/40 rounded-lg border border-green-200 dark:border-green-800 transition-all group"
                            >
                                <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                                    <TrendingUp className="w-4 h-4 text-white" />
                                </div>
                                <div className="text-left">
                                    <p className="text-sm font-semibold text-green-700 dark:text-green-300">Gestor</p>
                                    <p className="text-xs text-green-500 dark:text-green-400">gestor@banco.com</p>
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => { setEmail('auditor@banco.com'); setSenha('auditor123'); }}
                                className="flex items-center gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/40 rounded-lg border border-amber-200 dark:border-amber-800 transition-all group"
                            >
                                <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center">
                                    <Eye className="w-4 h-4 text-white" />
                                </div>
                                <div className="text-left">
                                    <p className="text-sm font-semibold text-amber-700 dark:text-amber-300">Auditor</p>
                                    <p className="text-xs text-amber-500 dark:text-amber-400">auditor@banco.com</p>
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => { setEmail('admin@banco.com'); setSenha('admin123'); }}
                                className="flex items-center gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 rounded-lg border border-purple-200 dark:border-purple-800 transition-all group"
                            >
                                <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                                    <AlertCircle className="w-4 h-4 text-white" />
                                </div>
                                <div className="text-left">
                                    <p className="text-sm font-semibold text-purple-700 dark:text-purple-300">Admin</p>
                                    <p className="text-xs text-purple-500 dark:text-purple-400">admin@banco.com</p>
                                </div>
                            </button>
                        </div>
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
