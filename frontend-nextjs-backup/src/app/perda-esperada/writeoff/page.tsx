"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useSettings } from "@/stores/useSettings"
import { toast } from "sonner"
import { FileX2, DollarSign, TrendingUp, Clock, PlusCircle, Search } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Legend,
    LineChart,
    Line,
} from "recharts"

// Dados mockados
const kpis = {
    total_baixado: 8500000,
    total_recuperado: 1870000,
    taxa_recuperacao: 0.22,
    contratos_ativos: 245,
    tempo_medio_recup: 18,
}

const baixasPorMotivo = [
    { motivo: "Inadimplência", valor: 4500000, qtd: 125, color: "#ef4444" },
    { motivo: "Falência/RJ", valor: 2100000, qtd: 45, color: "#f97316" },
    { motivo: "Óbito", valor: 350000, qtd: 28, color: "#6b7280" },
    { motivo: "Cessão", valor: 1200000, qtd: 35, color: "#3b82f6" },
    { motivo: "Outros", valor: 350000, qtd: 12, color: "#8b5cf6" },
]

const evolucaoRecuperacao = [
    { mes: "Jul", baixas: 850000, recuperacoes: 120000 },
    { mes: "Ago", baixas: 920000, recuperacoes: 180000 },
    { mes: "Set", baixas: 780000, recuperacoes: 220000 },
    { mes: "Out", baixas: 850000, recuperacoes: 280000 },
    { mes: "Nov", baixas: 680000, recuperacoes: 350000 },
    { mes: "Dez", baixas: 720000, recuperacoes: 420000 },
]

const contratosRecentes = [
    { contrato: "CTR2023001", valor: 15000, motivo: "inadimplencia", status: "em_acompanhamento", recuperado: 3500, dias: 180 },
    { contrato: "CTR2023002", valor: 85000, motivo: "falencia_rj", status: "recuperacao_parcial", recuperado: 12000, dias: 250 },
    { contrato: "CTR2023003", valor: 8500, motivo: "obito", status: "irrecuperavel", recuperado: 0, dias: 120 },
    { contrato: "CTR2022004", valor: 25000, motivo: "cessao", status: "recuperacao_total", recuperado: 22500, dias: 400 },
]

const formatCurrency = (v: number) => {
    if (v >= 1000000) return `R$ ${(v / 1000000).toFixed(2)}M`
    if (v >= 1000) return `R$ ${(v / 1000).toFixed(0)}k`
    return `R$ ${v.toFixed(0)}`
}

export default function WriteoffPage() {
    const { eclApiUrl } = useSettings()
    const [formBaixa, setFormBaixa] = useState({
        contrato_id: "",
        valor_baixado: "",
        motivo: "inadimplencia_prolongada",
        provisao_constituida: "",
    })
    const [formRecuperacao, setFormRecuperacao] = useState({
        contrato_id: "",
        valor_recuperado: "",
        tipo: "pagamento",
    })
    const [loading, setLoading] = useState(false)

    const handleRegistrarBaixa = async () => {
        if (!formBaixa.contrato_id || !formBaixa.valor_baixado) {
            toast.error("Preencha os campos obrigatórios")
            return
        }
        setLoading(true)
        try {
            // Simular chamada API
            await new Promise(r => setTimeout(r, 1000))
            toast.success(`Baixa registrada: ${formBaixa.contrato_id}`)
            setFormBaixa({ contrato_id: "", valor_baixado: "", motivo: "inadimplencia_prolongada", provisao_constituida: "" })
        } catch (error: any) {
            toast.error(error.message)
        } finally {
            setLoading(false)
        }
    }

    const handleRegistrarRecuperacao = async () => {
        if (!formRecuperacao.contrato_id || !formRecuperacao.valor_recuperado) {
            toast.error("Preencha os campos obrigatórios")
            return
        }
        setLoading(true)
        try {
            await new Promise(r => setTimeout(r, 1000))
            toast.success(`Recuperação registrada: ${formRecuperacao.contrato_id}`)
            setFormRecuperacao({ contrato_id: "", valor_recuperado: "", tipo: "pagamento" })
        } catch (error: any) {
            toast.error(error.message)
        } finally {
            setLoading(false)
        }
    }

    const getStatusBadge = (status: string) => {
        const map: Record<string, { label: string, class: string }> = {
            em_acompanhamento: { label: "Em Acompanhamento", class: "bg-blue-100 text-blue-700" },
            recuperacao_parcial: { label: "Recuperação Parcial", class: "bg-yellow-100 text-yellow-700" },
            recuperacao_total: { label: "Recuperação Total", class: "bg-green-100 text-green-700" },
            irrecuperavel: { label: "Irrecuperável", class: "bg-red-100 text-red-700" },
        }
        const s = map[status] || { label: status, class: "bg-gray-100 text-gray-700" }
        return <Badge className={s.class}>{s.label}</Badge>
    }

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <FileX2 className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">Baixa de Ativos (Write-off)</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                Reconhecimento contábil da perda definitiva de um ativo financeiro quando não há expectativa razoável de recuperação.
                                A operação é baixada do balanço, mas deve ser mantida em contas de compensação para controle jurídico e de cobrança por no mínimo 5 anos.
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Conformidade: Art. 49 da Resolução CMN 4966/2021 - Baixa de Ativos
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* KPIs */}
            <div className="grid gap-4 md:grid-cols-5">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Total Baixado</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-2xl font-bold">{formatCurrency(kpis.total_baixado)}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Total Recuperado</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-2xl font-bold text-green-600">{formatCurrency(kpis.total_recuperado)}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Taxa Recuperação</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-2xl font-bold">{(kpis.taxa_recuperacao * 100).toFixed(1)}%</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Em Acompanhamento</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-2xl font-bold">{kpis.contratos_ativos}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Tempo Médio</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-2xl font-bold">{kpis.tempo_medio_recup} meses</p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="dashboard" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                    <TabsTrigger value="registrar">Registrar</TabsTrigger>
                    <TabsTrigger value="contratos">Contratos</TabsTrigger>
                </TabsList>

                <TabsContent value="dashboard" className="space-y-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Baixas por Motivo</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={baixasPorMotivo}
                                                dataKey="valor"
                                                nameKey="motivo"
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={100}
                                                label={({ motivo, percent }) => `${motivo}: ${(percent * 100).toFixed(0)}%`}
                                            >
                                                {baixasPorMotivo.map((entry, i) => (
                                                    <Cell key={i} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip formatter={(v: number) => formatCurrency(v)} />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Evolução Baixas vs Recuperações</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={evolucaoRecuperacao}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="mes" />
                                            <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                            <Tooltip formatter={(v: number) => formatCurrency(v)} />
                                            <Legend />
                                            <Bar dataKey="baixas" name="Baixas" fill="#ef4444" />
                                            <Bar dataKey="recuperacoes" name="Recuperações" fill="#22c55e" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="registrar" className="space-y-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <FileX2 className="h-5 w-5" />
                                    Registrar Baixa
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Contrato *</Label>
                                    <Input
                                        placeholder="CTR..."
                                        value={formBaixa.contrato_id}
                                        onChange={(e) => setFormBaixa({ ...formBaixa, contrato_id: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Valor Baixado *</Label>
                                    <Input
                                        type="number"
                                        placeholder="0.00"
                                        value={formBaixa.valor_baixado}
                                        onChange={(e) => setFormBaixa({ ...formBaixa, valor_baixado: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Motivo</Label>
                                    <Select
                                        value={formBaixa.motivo}
                                        onValueChange={(v) => setFormBaixa({ ...formBaixa, motivo: v })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="inadimplencia_prolongada">Inadimplência Prolongada</SelectItem>
                                            <SelectItem value="falencia_rj">Falência/Recuperação Judicial</SelectItem>
                                            <SelectItem value="obito">Óbito</SelectItem>
                                            <SelectItem value="prescricao">Prescrição</SelectItem>
                                            <SelectItem value="cessao">Cessão de Crédito</SelectItem>
                                            <SelectItem value="outro">Outro</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Provisão Constituída</Label>
                                    <Input
                                        type="number"
                                        placeholder="0.00"
                                        value={formBaixa.provisao_constituida}
                                        onChange={(e) => setFormBaixa({ ...formBaixa, provisao_constituida: e.target.value })}
                                    />
                                </div>
                                <Button onClick={handleRegistrarBaixa} disabled={loading} className="w-full">
                                    <PlusCircle className="h-4 w-4 mr-2" />
                                    Registrar Baixa
                                </Button>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <DollarSign className="h-5 w-5" />
                                    Registrar Recuperação
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Contrato *</Label>
                                    <Input
                                        placeholder="CTR..."
                                        value={formRecuperacao.contrato_id}
                                        onChange={(e) => setFormRecuperacao({ ...formRecuperacao, contrato_id: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Valor Recuperado *</Label>
                                    <Input
                                        type="number"
                                        placeholder="0.00"
                                        value={formRecuperacao.valor_recuperado}
                                        onChange={(e) => setFormRecuperacao({ ...formRecuperacao, valor_recuperado: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Tipo</Label>
                                    <Select
                                        value={formRecuperacao.tipo}
                                        onValueChange={(v) => setFormRecuperacao({ ...formRecuperacao, tipo: v })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="pagamento">Pagamento</SelectItem>
                                            <SelectItem value="acordo">Acordo</SelectItem>
                                            <SelectItem value="acordo_judicial">Acordo Judicial</SelectItem>
                                            <SelectItem value="leilao_garantia">Leilão de Garantia</SelectItem>
                                            <SelectItem value="seguro">Seguro</SelectItem>
                                            <SelectItem value="outro">Outro</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleRegistrarRecuperacao} disabled={loading} className="w-full">
                                    <PlusCircle className="h-4 w-4 mr-2" />
                                    Registrar Recuperação
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="contratos" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Contratos em Acompanhamento</CardTitle>
                            <CardDescription>Período de 5 anos - Art. 49 CMN 4966</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <table className="w-full text-sm">
                                <thead className="bg-muted">
                                    <tr>
                                        <th className="p-3 text-left">Contrato</th>
                                        <th className="p-3 text-right">Valor Baixado</th>
                                        <th className="p-3 text-left">Motivo</th>
                                        <th className="p-3 text-right">Recuperado</th>
                                        <th className="p-3 text-right">Taxa</th>
                                        <th className="p-3 text-right">Dias</th>
                                        <th className="p-3 text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {contratosRecentes.map((c) => (
                                        <tr key={c.contrato} className="border-t hover:bg-muted/50">
                                            <td className="p-3 font-mono">{c.contrato}</td>
                                            <td className="p-3 text-right">{formatCurrency(c.valor)}</td>
                                            <td className="p-3 capitalize">{c.motivo.replace('_', ' ')}</td>
                                            <td className="p-3 text-right text-green-600">{formatCurrency(c.recuperado)}</td>
                                            <td className="p-3 text-right">{((c.recuperado / c.valor) * 100).toFixed(1)}%</td>
                                            <td className="p-3 text-right">{c.dias}</td>
                                            <td className="p-3 text-center">{getStatusBadge(c.status)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
