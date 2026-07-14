"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSettings } from "@/stores/useSettings"
import { eclApi } from "@/services/api"
import { toast } from "sonner"
import Link from "next/link"
import { Upload, Calculator, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from "recharts"

const produtos = [
    { value: "consignado", label: "Crédito Consignado", lgd: 0.25 },
    { value: "cartao_credito_rotativo", label: "Cartão de Crédito", lgd: 0.80 },
    { value: "imobiliario", label: "Crédito Imobiliário", lgd: 0.10 },
    { value: "veiculo", label: "Financiamento de Veículo", lgd: 0.35 },
    { value: "energia_solar", label: "Energia Solar", lgd: 0.40 },
    { value: "pessoal", label: "Crédito Pessoal", lgd: 0.70 },
]

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const formatPct = (value: number) => `${(value * 100).toFixed(2)}%`

export default function CalculoECLPage() {
    const { eclApiUrl } = useSettings()
    const [formData, setFormData] = useState({
        cpf: "",
        produto: "consignado",
        saldo_utilizado: "",
        limite_total: "",
        dias_atraso: "0",
    })
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)

    const handleCalculate = async () => {
        if (!formData.cpf || !formData.saldo_utilizado || !formData.limite_total) {
            toast.error("Preencha todos os campos obrigatórios")
            return
        }

        setLoading(true)
        try {
            const response = await eclApi.calcular(eclApiUrl, {
                cpf: formData.cpf,
                produto: formData.produto,
                saldo_utilizado: parseFloat(formData.saldo_utilizado),
                limite_total: parseFloat(formData.limite_total),
                dias_atraso: parseInt(formData.dias_atraso),
            })
            setResult(response.data)
            toast.success("ECL calculado com sucesso!")
        } catch (error: any) {
            toast.error(error.message || "Erro ao calcular ECL")
        } finally {
            setLoading(false)
        }
    }

    const getStageColor = (stage: number) => {
        if (stage === 1) return 'text-green-600'
        if (stage === 2) return 'text-yellow-600'
        return 'text-red-600'
    }

    const getStageLabel = (stage: number) => {
        if (stage === 1) return { label: 'Stage 1', desc: '12 meses', color: 'bg-green-100 text-green-700' }
        if (stage === 2) return { label: 'Stage 2', desc: 'Lifetime', color: 'bg-yellow-100 text-yellow-700' }
        return { label: 'Stage 3', desc: 'Lifetime + Piso', color: 'bg-red-100 text-red-700' }
    }

    // Dados para radar chart do resultado
    const radarData = result ? [
        { subject: 'PD', value: result.pd_ajustado * 100, fullMark: 100 },
        { subject: 'LGD', value: result.lgd_final * 100, fullMark: 100 },
        { subject: 'EAD/Limite', value: (result.ead / parseFloat(formData.limite_total || '1')) * 100, fullMark: 150 },
        { subject: 'Stage', value: result.stage * 33.33, fullMark: 100 },
        { subject: 'GH', value: result.grupo_homogeneo * 25, fullMark: 100 },
    ] : []

    // Breakdown do ECL
    const breakdownData = result ? [
        { name: 'PD Ajustado', valor: result.pd_ajustado },
        { name: 'LGD Final', valor: result.lgd_final },
        { name: 'EAD', valor: result.ead / 10000 }, // Escala para visualização
    ] : []

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <Calculator className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">O que é o Cálculo ECL?</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                O <strong>ECL (Expected Credit Loss)</strong> é a Perda de Crédito Esperada, calculada pela fórmula
                                <code className="mx-1 px-1 bg-blue-100 dark:bg-blue-900 rounded">baseline: PD × LGD × EAD</code>, onde PD é a
                                Probabilidade de Default, LGD é a Perda Dado o Default e EAD é a Exposição no Default.
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Referência histórica não verificada: arts. 21 a 25 da CMN 4.966/2021
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Tabs defaultValue="individual" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="individual" className="gap-2">
                        <Calculator className="h-4 w-4" />
                        Cálculo Individual
                    </TabsTrigger>
                    <TabsTrigger value="portfolio" className="gap-2">
                        <Upload className="h-4 w-4" />
                        Cálculo Portfólio
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="individual" className="space-y-4">
                    <div className="grid gap-6 lg:grid-cols-2">
                        {/* Formulário */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Calcular ECL Individual</CardTitle>
                                <CardDescription>
                                    Informe os dados da operação para calcular a perda esperada
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label htmlFor="cpf">CPF *</Label>
                                        <Input
                                            id="cpf"
                                            placeholder="00000000000"
                                            value={formData.cpf}
                                            onChange={(e) => setFormData({ ...formData, cpf: e.target.value.replace(/\D/g, "") })}
                                            maxLength={11}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="produto">Produto *</Label>
                                        <Select
                                            value={formData.produto}
                                            onValueChange={(value) => setFormData({ ...formData, produto: value })}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {produtos.map((p) => (
                                                    <SelectItem key={p.value} value={p.value}>
                                                        {p.label} (LGD: {(p.lgd * 100).toFixed(0)}%)
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="saldo">Saldo Utilizado (R$) *</Label>
                                        <Input
                                            id="saldo"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.saldo_utilizado}
                                            onChange={(e) => setFormData({ ...formData, saldo_utilizado: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="limite">Limite Total (R$) *</Label>
                                        <Input
                                            id="limite"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.limite_total}
                                            onChange={(e) => setFormData({ ...formData, limite_total: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2 md:col-span-2">
                                        <Label htmlFor="atraso">Dias em Atraso</Label>
                                        <Input
                                            id="atraso"
                                            type="number"
                                            placeholder="0"
                                            value={formData.dias_atraso}
                                            onChange={(e) => setFormData({ ...formData, dias_atraso: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <Button
                                    onClick={handleCalculate}
                                    disabled={loading}
                                    className="w-full"
                                    size="lg"
                                >
                                    {loading ? "Calculando..." : "Calcular ECL"}
                                </Button>
                            </CardContent>
                        </Card>

                        {/* Resultado */}
                        {result ? (
                            <Card className="border-2 border-primary/20">
                                <CardHeader className="pb-2">
                                    <div className="flex items-center justify-between">
                                        <CardTitle>Resultado ECL</CardTitle>
                                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStageLabel(result.stage).color}`}>
                                            {getStageLabel(result.stage).label}
                                        </span>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {/* ECL Principal */}
                                    <div className="text-center p-4 bg-gradient-to-br from-blue-500/10 to-blue-600/5 rounded-lg">
                                        <p className="text-sm text-muted-foreground">Perda Esperada (ECL)</p>
                                        <p className="text-4xl font-bold text-blue-600">
                                            {formatCurrency(result.ecl_final)}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Horizonte: {result.horizonte_ecl}
                                        </p>
                                    </div>

                                    {/* Grid de métricas */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">Rating</p>
                                            <p className="text-xl font-bold">{result.rating}</p>
                                        </div>
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">Grupo Homogêneo</p>
                                            <p className="text-xl font-bold">GH {result.grupo_homogeneo}</p>
                                        </div>
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">PD Ajustado</p>
                                            <p className="text-xl font-bold">{formatPct(result.pd_ajustado)}</p>
                                        </div>
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">LGD Final</p>
                                            <p className="text-xl font-bold">{formatPct(result.lgd_final)}</p>
                                        </div>
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">EAD</p>
                                            <p className="text-xl font-bold">{formatCurrency(result.ead)}</p>
                                        </div>
                                        <div className="p-3 bg-muted/50 rounded-lg">
                                            <p className="text-xs text-muted-foreground">Piso Aplicado</p>
                                            <p className="text-xl font-bold flex items-center gap-1">
                                                {result.piso_aplicado ? (
                                                    <><AlertCircle className="h-4 w-4 text-yellow-500" /> Sim</>
                                                ) : (
                                                    <><CheckCircle2 className="h-4 w-4 text-green-500" /> Não</>
                                                )}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Fórmula */}
                                    <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg text-sm">
                                        <p className="font-medium mb-1">Fórmula ECL:</p>
                                        <code className="text-xs">
                                            Baseline escalar = PD × LGD × EAD = {formatPct(result.pd_ajustado)} × {formatPct(result.lgd_final)} × {formatCurrency(result.ead)}
                                        </code>
                                    </div>

                                    {/* Radar Chart */}
                                    <div className="h-[200px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RadarChart data={radarData}>
                                                <PolarGrid />
                                                <PolarAngleAxis dataKey="subject" className="text-xs" />
                                                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                                <Radar
                                                    name="Perfil"
                                                    dataKey="value"
                                                    stroke="#3b82f6"
                                                    fill="#3b82f6"
                                                    fillOpacity={0.5}
                                                />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <Card className="flex items-center justify-center border-dashed">
                                <CardContent className="text-center py-16">
                                    <Calculator className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                                    <p className="text-muted-foreground">
                                        Preencha o formulário e clique em Calcular ECL
                                    </p>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="portfolio" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Cálculo de Portfólio</CardTitle>
                            <CardDescription>
                                Faça upload de um CSV para calcular ECL em lote
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="border-2 border-dashed rounded-lg p-8 text-center">
                                <Upload className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                                <p className="text-muted-foreground mb-4">
                                    Arraste um arquivo CSV ou clique para selecionar
                                </p>
                                <Button variant="outline">
                                    Selecionar Arquivo
                                </Button>
                            </div>
                            <div className="text-sm text-muted-foreground">
                                <p className="font-medium mb-2">Formato esperado do CSV:</p>
                                <code className="text-xs bg-muted p-2 rounded block">
                                    cliente_id,produto,saldo_utilizado,limite_total,dias_atraso,prinad,rating,pd_12m,pd_lifetime,stage
                                </code>
                            </div>
                            <Link href="/perda-esperada/calculo/portfolio">
                                <Button variant="link" className="p-0">
                                    Ir para página completa de portfólio →
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
