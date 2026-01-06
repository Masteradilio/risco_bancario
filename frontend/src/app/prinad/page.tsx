"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSettings } from "@/stores/useSettings"
import { prinadApi } from "@/services/api"
import { toast } from "sonner"
import { RatingDistributionChart, StageDistributionChart, PDTimelineChart } from "@/components/charts/Charts"
import { Upload, FileSpreadsheet, Download } from "lucide-react"

// Mock data for dashboard demo
const mockRatingData = [
    { rating: 'A1', count: 1250 },
    { rating: 'A2', count: 2100 },
    { rating: 'A3', count: 1800 },
    { rating: 'B1', count: 950 },
    { rating: 'B2', count: 720 },
    { rating: 'B3', count: 480 },
    { rating: 'C1', count: 320 },
    { rating: 'C2', count: 180 },
    { rating: 'C3', count: 95 },
    { rating: 'D', count: 65 },
    { rating: 'DEFAULT', count: 40 },
]

const mockStageData = [
    { name: 'Stage 1', value: 7200, stage: 1 },
    { name: 'Stage 2', value: 680, stage: 2 },
    { name: 'Stage 3', value: 120, stage: 3 },
]

const mockTimelineData = [
    { date: 'Jan', pd_medio: 0.023, clientes: 7850 },
    { date: 'Fev', pd_medio: 0.025, clientes: 7920 },
    { date: 'Mar', pd_medio: 0.024, clientes: 7890 },
    { date: 'Abr', pd_medio: 0.026, clientes: 7950 },
    { date: 'Mai', pd_medio: 0.028, clientes: 8020 },
    { date: 'Jun', pd_medio: 0.027, clientes: 8000 },
]

export default function PRINADPage() {
    const { prinadApiUrl } = useSettings()
    const [cpf, setCpf] = useState("")
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)

    // Batch processing state
    const [batchFile, setBatchFile] = useState<File | null>(null)
    const [batchLoading, setBatchLoading] = useState(false)
    const [batchResults, setBatchResults] = useState<any[]>([])
    const [batchProgress, setBatchProgress] = useState(0)

    const handleClassify = async () => {
        if (!cpf) {
            toast.error("Digite um CPF")
            return
        }

        setLoading(true)
        try {
            const response = await prinadApi.classifyExplained(prinadApiUrl, cpf)
            setResult(response.data)
            toast.success("Classificação realizada com sucesso")
        } catch (error: any) {
            toast.error(error.message || "Erro ao classificar")
        } finally {
            setLoading(false)
        }
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setBatchFile(file)
            toast.info(`Arquivo selecionado: ${file.name}`)
        }
    }

    const handleBatchProcess = async () => {
        if (!batchFile) {
            toast.error("Selecione um arquivo CSV")
            return
        }

        setBatchLoading(true)
        setBatchProgress(0)
        setBatchResults([])

        try {
            const text = await batchFile.text()
            const lines = text.split('\n').filter(line => line.trim())
            const header = lines[0].toLowerCase()
            const cpfIndex = header.split(/[,;]/).findIndex(col => col.includes('cpf'))

            if (cpfIndex === -1) {
                toast.error("Coluna CPF não encontrada")
                setBatchLoading(false)
                return
            }

            const cpfs: string[] = []
            for (let i = 1; i < lines.length; i++) {
                const cols = lines[i].split(/[,;]/)
                if (cols[cpfIndex]) {
                    cpfs.push(cols[cpfIndex].replace(/\D/g, '').padStart(11, '0'))
                }
            }

            toast.info(`Processando ${cpfs.length} CPFs...`)

            // Process in batches of 100
            const batchSize = 100
            const results: any[] = []

            for (let i = 0; i < cpfs.length; i += batchSize) {
                const batch = cpfs.slice(i, i + batchSize)
                try {
                    const response = await prinadApi.classifyMultiple(prinadApiUrl, batch)
                    if (response.data.resultados) {
                        results.push(...response.data.resultados)
                    }
                } catch (error) {
                    console.error('Batch error:', error)
                }
                setBatchProgress(Math.min(100, Math.round(((i + batchSize) / cpfs.length) * 100)))
            }

            setBatchResults(results)
            toast.success(`Processados ${results.length} clientes`)

        } catch (error: any) {
            toast.error(error.message || "Erro ao processar arquivo")
        } finally {
            setBatchLoading(false)
        }
    }

    const downloadResults = () => {
        if (batchResults.length === 0) return

        const csv = [
            'CPF,PRINAD,Rating,Stage,PD_12m,PD_Lifetime',
            ...batchResults.map(r =>
                `${r.cpf},${r.prinad?.toFixed(2)},${r.rating},${r.estagio_pe},${r.pd_12m?.toFixed(6)},${r.pd_lifetime?.toFixed(6)}`
            )
        ].join('\n')

        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'prinad_resultados.csv'
        a.click()
    }

    const getRatingColor = (rating: string) => {
        if (rating?.startsWith('A')) return 'text-green-500'
        if (rating?.startsWith('B')) return 'text-yellow-500'
        if (rating?.startsWith('C')) return 'text-orange-500'
        return 'text-red-500'
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">PRINAD</h1>
                <p className="text-muted-foreground">
                    Probabilidade de Inadimplência - Classificação de Risco de Crédito
                </p>
            </div>

            <Tabs defaultValue="individual">
                <TabsList>
                    <TabsTrigger value="individual">Classificação Individual</TabsTrigger>
                    <TabsTrigger value="lote">Classificação em Lote</TabsTrigger>
                    <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                </TabsList>

                <TabsContent value="individual" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Classificar Cliente</CardTitle>
                            <CardDescription>
                                Digite o CPF para obter a classificação de risco
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <Label htmlFor="cpf">CPF</Label>
                                    <Input
                                        id="cpf"
                                        placeholder="00000000000"
                                        value={cpf}
                                        onChange={(e) => setCpf(e.target.value.replace(/\D/g, ""))}
                                        maxLength={11}
                                    />
                                </div>
                                <div className="flex items-end">
                                    <Button onClick={handleClassify} disabled={loading}>
                                        {loading ? "Classificando..." : "Classificar"}
                                    </Button>
                                </div>
                            </div>

                            {result && (
                                <div className="grid gap-4 md:grid-cols-4 mt-6">
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">PRINAD Score</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <span className="text-2xl font-bold">{result.prinad?.toFixed(2)}%</span>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">Rating</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <span className={`text-2xl font-bold ${getRatingColor(result.rating)}`}>{result.rating}</span>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">Stage IFRS 9</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <span className="text-2xl font-bold">{result.estagio_pe}</span>
                                        </CardContent>
                                    </Card>
                                    <Card>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-sm">PD 12 meses</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <span className="text-2xl font-bold">{(result.pd_12m * 100)?.toFixed(2)}%</span>
                                        </CardContent>
                                    </Card>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="lote">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileSpreadsheet className="h-5 w-5" />
                                Classificação em Lote
                            </CardTitle>
                            <CardDescription>
                                Faça upload de um arquivo CSV com a coluna CPF
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="border-2 border-dashed rounded-lg p-8 text-center">
                                <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                <div className="space-y-2">
                                    <Label htmlFor="file-upload" className="cursor-pointer">
                                        <span className="text-primary font-medium">Clique para selecionar</span>
                                        <span className="text-muted-foreground"> ou arraste um arquivo CSV</span>
                                    </Label>
                                    <Input
                                        id="file-upload"
                                        type="file"
                                        accept=".csv"
                                        className="hidden"
                                        onChange={handleFileChange}
                                    />
                                    {batchFile && (
                                        <p className="text-sm text-muted-foreground">
                                            Arquivo: {batchFile.name}
                                        </p>
                                    )}
                                </div>
                            </div>

                            <Button
                                onClick={handleBatchProcess}
                                disabled={!batchFile || batchLoading}
                                className="w-full"
                            >
                                {batchLoading ? `Processando... ${batchProgress}%` : "Processar Arquivo"}
                            </Button>

                            {batchResults.length > 0 && (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <p className="text-sm text-muted-foreground">
                                            {batchResults.length} registros processados
                                        </p>
                                        <Button variant="outline" size="sm" onClick={downloadResults}>
                                            <Download className="h-4 w-4 mr-2" />
                                            Download CSV
                                        </Button>
                                    </div>

                                    <div className="max-h-[400px] overflow-auto border rounded-lg">
                                        <table className="w-full text-sm">
                                            <thead className="bg-muted sticky top-0">
                                                <tr>
                                                    <th className="p-2 text-left">CPF</th>
                                                    <th className="p-2 text-left">PRINAD</th>
                                                    <th className="p-2 text-left">Rating</th>
                                                    <th className="p-2 text-left">Stage</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {batchResults.slice(0, 100).map((r, i) => (
                                                    <tr key={i} className="border-t">
                                                        <td className="p-2">{r.cpf}</td>
                                                        <td className="p-2">{r.prinad?.toFixed(2)}%</td>
                                                        <td className={`p-2 font-medium ${getRatingColor(r.rating)}`}>{r.rating}</td>
                                                        <td className="p-2">{r.estagio_pe}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
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
                                    Total de Clientes
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">8,000</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    PD Médio
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold">2.7%</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Stage 1
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold text-green-500">90.0%</span>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Stage 3 (Default)
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="text-2xl font-bold text-red-500">1.5%</span>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Distribuição por Rating</CardTitle>
                                <CardDescription>Quantidade de clientes por classificação</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <RatingDistributionChart data={mockRatingData} />
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Distribuição por Stage IFRS 9</CardTitle>
                                <CardDescription>Classificação conforme BACEN 4966</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <StageDistributionChart data={mockStageData} />
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Evolução Temporal</CardTitle>
                            <CardDescription>PD Médio e quantidade de clientes ao longo do tempo</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <PDTimelineChart data={mockTimelineData} />
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
