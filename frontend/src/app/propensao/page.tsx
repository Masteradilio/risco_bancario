"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSettings } from "@/stores/useSettings"
import { propensaoApi } from "@/services/api"
import { toast } from "sonner"
import { PropensaoDistributionChart } from "@/components/charts/Charts"

// Mock data for dashboard
const mockAcaoDistribuicao = [
    { acao: 'MANTER', valor: 5600, percentual: 70 },
    { acao: 'AUMENTAR', valor: 1120, percentual: 14 },
    { acao: 'REDUZIR', valor: 1120, percentual: 14 },
    { acao: 'ZERAR', valor: 160, percentual: 2 },
]

export default function PropensaoPage() {
    const { propensaoApiUrl } = useSettings()
    const [formData, setFormData] = useState({
        cpf: "",
        produto: "consignado",
        prinad: "",
        propensity_score: "",
        limite_atual: "",
        saldo_utilizado: "",
    })
    const [scoreFormData, setScoreFormData] = useState({
        cpf: "",
        produto: "consignado",
        prinad: "",
        renda: "",
        utilizacao: "",
        tempo_relacionamento: "",
    })
    const [simulacaoData, setSimulacaoData] = useState({
        cenario: "moderado",
    })
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [scoreResult, setScoreResult] = useState<any>(null)
    const [simulacaoResult, setSimulacaoResult] = useState<any>(null)

    const handleRecomendar = async () => {
        if (!formData.cpf || !formData.prinad || !formData.limite_atual) {
            toast.error("Preencha todos os campos obrigatórios")
            return
        }

        setLoading(true)
        try {
            const response = await propensaoApi.recomendar(propensaoApiUrl, {
                cpf: formData.cpf,
                produto: formData.produto,
                prinad: parseFloat(formData.prinad),
                propensity_score: parseFloat(formData.propensity_score) || 0.5,
                limite_atual: parseFloat(formData.limite_atual),
                saldo_utilizado: parseFloat(formData.saldo_utilizado) || 0,
            })
            setResult(response.data)
            toast.success("Recomendação gerada com sucesso")
        } catch (error: any) {
            toast.error(error.message || "Erro ao gerar recomendação")
        } finally {
            setLoading(false)
        }
    }

    const handleCalcularScore = async () => {
        if (!scoreFormData.cpf || !scoreFormData.prinad || !scoreFormData.renda) {
            toast.error("Preencha todos os campos obrigatórios")
            return
        }

        setLoading(true)
        try {
            const response = await propensaoApi.score(propensaoApiUrl, {
                cpf: scoreFormData.cpf,
                produto: scoreFormData.produto,
                prinad: parseFloat(scoreFormData.prinad),
                renda: parseFloat(scoreFormData.renda),
                utilizacao: parseFloat(scoreFormData.utilizacao) || 0.5,
                tempo_relacionamento: parseInt(scoreFormData.tempo_relacionamento) || 24,
            })
            setScoreResult(response.data)
            toast.success("Score calculado com sucesso")
        } catch (error: any) {
            toast.error(error.message || "Erro ao calcular score")
        } finally {
            setLoading(false)
        }
    }

    const handleSimular = async () => {
        setLoading(true)
        try {
            // Mock portfolio for simulation
            const mockPortfolio = [
                { limite: 50000, saldo: 35000, pd: 0.02, lgd: 0.35, prinad: 15, propensity: 0.7 },
                { limite: 30000, saldo: 28000, pd: 0.05, lgd: 0.35, prinad: 45, propensity: 0.4 },
                { limite: 80000, saldo: 10000, pd: 0.01, lgd: 0.25, prinad: 8, propensity: 0.8 },
                { limite: 20000, saldo: 19000, pd: 0.15, lgd: 0.80, prinad: 85, propensity: 0.2 },
            ]

            const response = await propensaoApi.simular(propensaoApiUrl, mockPortfolio, simulacaoData.cenario)
            setSimulacaoResult(response.data)
            toast.success("Simulação realizada com sucesso")
        } catch (error: any) {
            toast.error(error.message || "Erro ao simular")
        } finally {
            setLoading(false)
        }
    }

    const getActionColor = (acao: string) => {
        switch (acao) {
            case "AUMENTAR": return "text-green-500"
            case "MANTER": return "text-blue-500"
            case "REDUZIR": return "text-orange-500"
            case "ZERAR": return "text-red-500"
            default: return ""
        }
    }

    const getClassificacaoColor = (classificacao: string) => {
        switch (classificacao) {
            case "ALTA": return "text-green-500"
            case "MEDIA": return "text-yellow-500"
            case "BAIXA": return "text-red-500"
            default: return ""
        }
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Propensão - PROLIMITE</h1>
                <p className="text-muted-foreground">
                    Otimização de Limites e Score de Propensão
                </p>
            </div>

            <Tabs defaultValue="dashboard">
                <TabsList>
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                    <TabsTrigger value="recomendar">Recomendar Limite</TabsTrigger>
                    <TabsTrigger value="score">Score de Propensão</TabsTrigger>
                    <TabsTrigger value="simular">Simulador de Impacto</TabsTrigger>
                </TabsList>

                <TabsContent value="recomendar" className="space-y-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Gerar Recomendação</CardTitle>
                                <CardDescription>
                                    Informe os dados do cliente para obter a recomendação de limite
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label htmlFor="cpf">CPF</Label>
                                        <Input
                                            id="cpf"
                                            placeholder="00000000000"
                                            value={formData.cpf}
                                            onChange={(e) => setFormData({ ...formData, cpf: e.target.value.replace(/\D/g, "") })}
                                            maxLength={11}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="produto">Produto</Label>
                                        <Select
                                            value={formData.produto}
                                            onValueChange={(value) => setFormData({ ...formData, produto: value })}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="consignado">Consignado</SelectItem>
                                                <SelectItem value="cartao_credito_rotativo">Cartão de Crédito</SelectItem>
                                                <SelectItem value="imobiliario">Imobiliário</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label htmlFor="prinad">PRINAD Score (%)</Label>
                                        <Input
                                            id="prinad"
                                            type="number"
                                            placeholder="0-100"
                                            value={formData.prinad}
                                            onChange={(e) => setFormData({ ...formData, prinad: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="propensity">Score Propensão (0-1)</Label>
                                        <Input
                                            id="propensity"
                                            type="number"
                                            step="0.1"
                                            placeholder="0.5"
                                            value={formData.propensity_score}
                                            onChange={(e) => setFormData({ ...formData, propensity_score: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="limite">Limite Atual (R$)</Label>
                                        <Input
                                            id="limite"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.limite_atual}
                                            onChange={(e) => setFormData({ ...formData, limite_atual: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="saldo">Saldo Utilizado (R$)</Label>
                                        <Input
                                            id="saldo"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.saldo_utilizado}
                                            onChange={(e) => setFormData({ ...formData, saldo_utilizado: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <Button onClick={handleRecomendar} disabled={loading} className="w-full">
                                    {loading ? "Gerando..." : "Gerar Recomendação"}
                                </Button>
                            </CardContent>
                        </Card>

                        {result && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Recomendação</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="text-center">
                                        <p className={`text-4xl font-bold ${getActionColor(result.acao)}`}>
                                            {result.acao}
                                        </p>
                                        <p className="text-muted-foreground mt-2">{result.justificativa}</p>
                                    </div>
                                    <div className="grid gap-4 grid-cols-2">
                                        <div>
                                            <p className="text-sm text-muted-foreground">Ajuste</p>
                                            <p className="text-xl font-bold">{(result.percentual_ajuste * 100)?.toFixed(0)}%</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">Novo Limite</p>
                                            <p className="text-xl font-bold">R$ {result.novo_limite?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                        </div>
                                        <div className="col-span-2">
                                            <p className="text-sm text-muted-foreground">Economia ECL</p>
                                            <p className="text-xl font-bold text-green-500">R$ {result.economia_ecl?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="score" className="space-y-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Calcular Score de Propensão</CardTitle>
                                <CardDescription>
                                    Avalie a propensão do cliente para um produto
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label>CPF</Label>
                                        <Input
                                            placeholder="00000000000"
                                            value={scoreFormData.cpf}
                                            onChange={(e) => setScoreFormData({ ...scoreFormData, cpf: e.target.value.replace(/\D/g, "") })}
                                            maxLength={11}
                                        />
                                    </div>
                                    <div>
                                        <Label>Produto</Label>
                                        <Select
                                            value={scoreFormData.produto}
                                            onValueChange={(value) => setScoreFormData({ ...scoreFormData, produto: value })}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="consignado">Consignado</SelectItem>
                                                <SelectItem value="cartao_credito_rotativo">Cartão de Crédito</SelectItem>
                                                <SelectItem value="imobiliario">Imobiliário</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label>PRINAD Score (%)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0-100"
                                            value={scoreFormData.prinad}
                                            onChange={(e) => setScoreFormData({ ...scoreFormData, prinad: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Renda Mensal (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={scoreFormData.renda}
                                            onChange={(e) => setScoreFormData({ ...scoreFormData, renda: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Taxa Utilização (0-1)</Label>
                                        <Input
                                            type="number"
                                            step="0.1"
                                            placeholder="0.5"
                                            value={scoreFormData.utilizacao}
                                            onChange={(e) => setScoreFormData({ ...scoreFormData, utilizacao: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Tempo Relacionamento (meses)</Label>
                                        <Input
                                            type="number"
                                            placeholder="24"
                                            value={scoreFormData.tempo_relacionamento}
                                            onChange={(e) => setScoreFormData({ ...scoreFormData, tempo_relacionamento: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <Button onClick={handleCalcularScore} disabled={loading} className="w-full">
                                    {loading ? "Calculando..." : "Calcular Score"}
                                </Button>
                            </CardContent>
                        </Card>

                        {scoreResult && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Resultado</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="text-center">
                                        <p className="text-6xl font-bold">{(scoreResult.propensity_score * 100)?.toFixed(0)}%</p>
                                        <p className={`text-2xl font-semibold ${getClassificacaoColor(scoreResult.classificacao)}`}>
                                            {scoreResult.classificacao}
                                        </p>
                                    </div>
                                    <div className="p-4 bg-muted rounded-lg">
                                        <p className="text-sm">{scoreResult.recomendacao}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="simular" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Simulador de Impacto Financeiro</CardTitle>
                            <CardDescription>
                                Simule o impacto de ajustes de limite em um portfólio
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-4 items-end">
                                <div className="flex-1">
                                    <Label>Cenário</Label>
                                    <Select
                                        value={simulacaoData.cenario}
                                        onValueChange={(value) => setSimulacaoData({ cenario: value })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="conservador">Conservador (10% redução)</SelectItem>
                                            <SelectItem value="moderado">Moderado (15% redução)</SelectItem>
                                            <SelectItem value="agressivo">Agressivo (20% redução)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleSimular} disabled={loading}>
                                    {loading ? "Simulando..." : "Simular"}
                                </Button>
                            </div>

                            {simulacaoResult && (
                                <div className="grid gap-4 md:grid-cols-3 mt-6">
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">Economia ECL</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-2xl font-bold text-green-500">
                                                R$ {simulacaoResult.economia_ecl?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">Receita Adicional</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-2xl font-bold text-blue-500">
                                                R$ {simulacaoResult.receita_adicional?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">Impacto Líquido</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-2xl font-bold text-primary">
                                                R$ {simulacaoResult.impacto_liquido?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                            </p>
                                        </CardContent>
                                    </Card>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="dashboard" className="space-y-6">
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Limite Total
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">R$ 180M</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Limite Não Utilizado
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold text-orange-500">R$ 54M</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Economia Potencial ECL
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold text-green-500">R$ 702k</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Clientes Alta Propensão
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">14%</span>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Distribuição de Ações Recomendadas</CardTitle>
                            <CardDescription>Proporção de clientes por tipo de ação</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <PropensaoDistributionChart data={mockAcaoDistribuicao} />
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
