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
import { ECLByGroupChart, StageDistributionChart } from "@/components/charts/Charts"

const produtos = [
    { value: "consignado", label: "Crédito Consignado" },
    { value: "cartao_credito_rotativo", label: "Cartão de Crédito" },
    { value: "imobiliario", label: "Crédito Imobiliário" },
    { value: "veiculo", label: "Financiamento de Veículo" },
    { value: "energia_solar", label: "Energia Solar" },
]

// Mock data for dashboard
const mockECLByGroup = [
    { grupo: 'GH 1', ecl: 125000, clientes: 4500 },
    { grupo: 'GH 2', ecl: 380000, clientes: 1800 },
    { grupo: 'GH 3', ecl: 920000, clientes: 850 },
    { grupo: 'GH 4', ecl: 1450000, clientes: 350 },
]

const mockStageECL = [
    { name: 'Stage 1', value: 450000, stage: 1 },
    { name: 'Stage 2', value: 780000, stage: 2 },
    { name: 'Stage 3', value: 1200000, stage: 3 },
]

export default function ECLPage() {
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
            toast.success("ECL calculado com sucesso")
        } catch (error: any) {
            toast.error(error.message || "Erro ao calcular ECL")
        } finally {
            setLoading(false)
        }
    }

    const getStageColor = (stage: number) => {
        if (stage === 1) return 'text-green-500'
        if (stage === 2) return 'text-yellow-500'
        return 'text-red-500'
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">ECL - Perda Esperada</h1>
                <p className="text-muted-foreground">
                    Cálculo de Expected Credit Loss conforme BACEN 4966 / IFRS 9
                </p>
            </div>

            <Tabs defaultValue="calculo">
                <TabsList>
                    <TabsTrigger value="calculo">Cálculo ECL</TabsTrigger>
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                </TabsList>

                <TabsContent value="calculo" className="space-y-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Calcular ECL</CardTitle>
                                <CardDescription>
                                    Informe os dados da operação para calcular a perda esperada
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 md:grid-cols-2">
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
                                                {produtos.map((p) => (
                                                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
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
                                    <div>
                                        <Label htmlFor="limite">Limite Total (R$)</Label>
                                        <Input
                                            id="limite"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.limite_total}
                                            onChange={(e) => setFormData({ ...formData, limite_total: e.target.value })}
                                        />
                                    </div>
                                    <div>
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
                                <Button onClick={handleCalculate} disabled={loading} className="w-full">
                                    {loading ? "Calculando..." : "Calcular ECL"}
                                </Button>
                            </CardContent>
                        </Card>

                        {result && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Resultado</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="text-center mb-4">
                                        <p className="text-sm text-muted-foreground">ECL</p>
                                        <p className="text-4xl font-bold text-primary">
                                            R$ {result.ecl_final?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                        </p>
                                    </div>
                                    <div className="grid gap-4 grid-cols-2">
                                        <div>
                                            <p className="text-sm text-muted-foreground">Stage IFRS 9</p>
                                            <p className={`text-2xl font-bold ${getStageColor(result.stage)}`}>{result.stage}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">Rating</p>
                                            <p className="text-xl font-bold">{result.rating}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">Grupo Homogêneo</p>
                                            <p className="text-xl font-bold">{result.grupo_homogeneo}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">Horizonte</p>
                                            <p className="text-xl font-bold">{result.horizonte_ecl}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">LGD</p>
                                            <p className="text-xl font-bold">{(result.lgd_final * 100)?.toFixed(2)}%</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">EAD</p>
                                            <p className="text-xl font-bold">R$ {result.ead?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">PD Ajustado</p>
                                            <p className="text-xl font-bold">{(result.pd_ajustado * 100)?.toFixed(4)}%</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-muted-foreground">Piso Aplicado</p>
                                            <p className="text-xl font-bold">{result.piso_aplicado ? 'Sim' : 'Não'}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="dashboard" className="space-y-6">
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    ECL Total
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">R$ 2.43M</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    LGD Médio
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">32.5%</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    EAD Total
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">R$ 156M</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Cobertura ECL
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">1.56%</span>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>ECL por Grupo Homogêneo</CardTitle>
                                <CardDescription>Distribuição de perdas esperadas por grupo de risco</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <ECLByGroupChart data={mockECLByGroup} />
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>ECL por Stage IFRS 9</CardTitle>
                                <CardDescription>Distribuição conforme classificação BACEN 4966</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <StageDistributionChart data={mockStageECL} />
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Resumo por Produto</CardTitle>
                            <CardDescription>Métricas ECL por tipo de crédito</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-muted">
                                        <tr>
                                            <th className="p-3 text-left">Produto</th>
                                            <th className="p-3 text-right">Carteira</th>
                                            <th className="p-3 text-right">ECL</th>
                                            <th className="p-3 text-right">LGD Médio</th>
                                            <th className="p-3 text-right">Cobertura</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-t">
                                            <td className="p-3">Consignado</td>
                                            <td className="p-3 text-right">R$ 85M</td>
                                            <td className="p-3 text-right">R$ 425k</td>
                                            <td className="p-3 text-right">25.0%</td>
                                            <td className="p-3 text-right">0.50%</td>
                                        </tr>
                                        <tr className="border-t">
                                            <td className="p-3">Cartão de Crédito</td>
                                            <td className="p-3 text-right">R$ 42M</td>
                                            <td className="p-3 text-right">R$ 1.26M</td>
                                            <td className="p-3 text-right">80.0%</td>
                                            <td className="p-3 text-right">3.00%</td>
                                        </tr>
                                        <tr className="border-t">
                                            <td className="p-3">Imobiliário</td>
                                            <td className="p-3 text-right">R$ 25M</td>
                                            <td className="p-3 text-right">R$ 125k</td>
                                            <td className="p-3 text-right">10.0%</td>
                                            <td className="p-3 text-right">0.50%</td>
                                        </tr>
                                        <tr className="border-t">
                                            <td className="p-3">Veículo</td>
                                            <td className="p-3 text-right">R$ 4M</td>
                                            <td className="p-3 text-right">R$ 620k</td>
                                            <td className="p-3 text-right">35.0%</td>
                                            <td className="p-3 text-right">15.5%</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
