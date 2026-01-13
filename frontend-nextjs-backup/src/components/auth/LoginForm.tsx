"use client"

import { useState } from "react"
import { useAuth } from "@/stores/useAuth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"
import { Shield, Lock, Mail, Loader2 } from "lucide-react"

export function LoginForm() {
    const [email, setEmail] = useState("")
    const [senha, setSenha] = useState("")
    const { login, isLoading } = useAuth()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!email || !senha) {
            toast.error("Preencha todos os campos")
            return
        }

        const success = await login(email, senha)

        if (success) {
            toast.success("Login realizado com sucesso!")
        } else {
            toast.error("Credenciais inválidas")
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
            </div>

            <Card className="w-full max-w-md relative backdrop-blur-sm bg-card/95 border-slate-700">
                <CardHeader className="text-center pb-8">
                    <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-500/25">
                        <Shield className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        Sistema de Risco Bancário
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Acesse sua conta para continuar
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-slate-300">E-mail Corporativo</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="usuario@banco.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="pl-10 bg-slate-800/50 border-slate-700 focus:border-blue-500 focus:ring-blue-500/20"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="senha" className="text-slate-300">Senha</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                                <Input
                                    id="senha"
                                    type="password"
                                    placeholder="••••••••"
                                    value={senha}
                                    onChange={(e) => setSenha(e.target.value)}
                                    className="pl-10 bg-slate-800/50 border-slate-700 focus:border-blue-500 focus:ring-blue-500/20"
                                />
                            </div>
                        </div>
                        <Button
                            type="submit"
                            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg shadow-blue-500/25"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Autenticando...
                                </>
                            ) : (
                                "Entrar"
                            )}
                        </Button>
                    </form>

                    {/* Demo credentials */}
                    <div className="mt-8 p-4 bg-slate-900 rounded-lg border border-slate-600">
                        <p className="text-sm text-white mb-3 font-semibold">Credenciais de demonstração:</p>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-300 font-medium">Analista:</span>
                                <code className="text-cyan-400 font-mono">analista@banco.com / analista123</code>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-300 font-medium">Gestor:</span>
                                <code className="text-cyan-400 font-mono">gestor@banco.com / gestor123</code>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-300 font-medium">Auditor:</span>
                                <code className="text-cyan-400 font-mono">auditor@banco.com / auditor123</code>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-300 font-medium">Admin:</span>
                                <code className="text-cyan-400 font-mono">admin@banco.com / admin123</code>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
