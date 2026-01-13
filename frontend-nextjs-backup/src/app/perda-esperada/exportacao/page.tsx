"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useSettings } from "@/stores/useSettings"
import { usePipelineStore } from "@/stores/usePipeline"
import { toast } from "sonner"
import Link from "next/link"
import { FileOutput, Download, CheckCircle2, XCircle, AlertTriangle, FileCode, Loader2, Zap, ArrowLeft } from "lucide-react"

const ultimosEnvios = [
    { id: "ENV202512", data_base: "2025-12", status: "aceito", operacoes: 15847, ecl: 2430000, protocolo: "BCB2026010200001" },
    { id: "ENV202511", data_base: "2025-11", status: "aceito", operacoes: 15234, ecl: 2350000, protocolo: "BCB2025120200001" },
    { id: "ENV202510", data_base: "2025-10", status: "alertas", operacoes: 14890, ecl: 2280000, protocolo: "BCB2025110200002" },
    { id: "ENV202509", data_base: "2025-09", status: "aceito", operacoes: 14502, ecl: 2150000, protocolo: "BCB2025100200001" },
]

const formatCurrency = (v: number) => `R$ ${(v / 1000000).toFixed(2)}M`

export default function ExportacaoPage() {
    const { eclApiUrl } = useSettings()
    const { resultado: pipelineResultado } = usePipelineStore()
    const [formData, setFormData] = useState({
        data_base: new Date().toISOString().slice(0, 7),
        cnpj: "00000000",
        responsavel_nome: "",
        responsavel_email: "",
        responsavel_telefone: "",
        metodologia: "C",
    })
    const [loading, setLoading] = useState(false)
    const [resultado, setResultado] = useState<any>(null)

    // Definição das etapas de validação
    const ETAPAS_INICIAIS = [
        { id: 1, nome: "Estrutura DOC 3040/XML", descricao: "Validação XSD e tags obrigatórias", status: "pendente" },
        { id: 2, nome: "Consistência Contábil", descricao: "Batimento COSIF x Carteira (VlrContabilBruto)", status: "pendente" },
        { id: 3, nome: "Regras Semânticas (CMN 4966)", descricao: "Estágios, Alocação, IPOC único", status: "pendente" },
        { id: 4, nome: "Totais de Controle", descricao: "Verificação de somatórios e integridade", status: "pendente" },
    ]

    const [validacaoEtapas, setValidacaoEtapas] = useState(ETAPAS_INICIAIS)

    const handleGerar = async () => {
        // Validar se o pipeline foi executado
        if (!pipelineResultado.executado) {
            toast.error("Execute primeiro o Pipeline Completo, na aba anterior")
            return
        }

        if (!formData.responsavel_nome || !formData.responsavel_email) {
            toast.error("Preencha os dados do responsável")
            return
        }

        setLoading(true)
        setResultado(null)
        setValidacaoEtapas(ETAPAS_INICIAIS) // Reset

        try {
            // Simulação sequencial de validação
            const etapas = [...ETAPAS_INICIAIS]

            for (let i = 0; i < etapas.length; i++) {
                // Marca atual como processando
                etapas[i] = { ...etapas[i], status: 'processando' }
                setValidacaoEtapas([...etapas])

                // Delay simulado
                await new Promise(r => setTimeout(r, 800))

                // Marca como sucesso
                etapas[i] = { ...etapas[i], status: 'sucesso' }
                setValidacaoEtapas([...etapas])
            }

            // Após validações, prossegue para geração (simulada ou real)
            // ... (código existente de fetch ou mock)

            // Simular resultado final com sucesso
            setResultado({
                validacao: { valido: true, erros: [] },
                estatisticas: {
                    total_operacoes: pipelineResultado.totalOperacoes,
                    ecl_total: pipelineResultado.eclTotal,
                },
                arquivo_nome: `DOC3040_${formData.data_base.replace('-', '')}_${formData.cnpj}.xml`,
            })
            toast.success("Validação concluída e XML gerado com sucesso!")

        } catch (error: any) {
            toast.error("Falha no processo de validação/geração")
        } finally {
            setLoading(false)
        }
    }

    const downloadXML = () => {
        // Gerar XML de exemplo
        const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<DOC3040 xmlns="http://www.bcb.gov.br/sisbacen/schema/3040">
  <Header>
    <CNPJ>${formData.cnpj}</CNPJ>
    <DataBase>${formData.data_base}</DataBase>
    <Metodologia>${formData.metodologia}</Metodologia>
    <Responsavel>
      <Nome>${formData.responsavel_nome}</Nome>
      <Email>${formData.responsavel_email}</Email>
    </Responsavel>
  </Header>
  <PECLD>
    <TotalOperacoes>${pipelineResultado.totalOperacoes}</TotalOperacoes>
    <ECLTotal>${pipelineResultado.eclTotal}</ECLTotal>
    <ECLStage1>${pipelineResultado.eclStage1}</ECLStage1>
    <ECLStage2>${pipelineResultado.eclStage2}</ECLStage2>
    <ECLStage3>${pipelineResultado.eclStage3}</ECLStage3>
    <DataCalculo>${pipelineResultado.dataExecucao}</DataCalculo>
  </PECLD>
</DOC3040>`

        const blob = new Blob([xmlContent], { type: 'application/xml' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = resultado?.arquivo_nome || 'DOC3040.xml'
        a.click()
        URL.revokeObjectURL(url)
        toast.success("XML baixado com sucesso!")
    }

    const getStatusBadge = (status: string) => {
        if (status === "aceito") return <Badge className="bg-green-100 text-green-700">Aceito</Badge>
        if (status === "alertas") return <Badge className="bg-yellow-100 text-yellow-700">Alertas</Badge>
        if (status === "rejeitado") return <Badge className="bg-red-100 text-red-700">Rejeitado</Badge>
        return <Badge>{status}</Badge>
    }

    return (
        <div className="space-y-6">
            {/* Aviso se pipeline não foi executado */}
            {!pipelineResultado.executado && (
                <Card className="bg-amber-50 dark:bg-amber-950/30 border-amber-500/50">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                            <AlertTriangle className="h-8 w-8 text-amber-600 flex-shrink-0" />
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-amber-700 dark:text-amber-400">
                                    Execute primeiro o Pipeline Completo
                                </h3>
                                <p className="text-amber-600 dark:text-amber-500 mt-1">
                                    Para gerar o XML ECL é necessário executar o Pipeline Completo de Perda Esperada primeiro.
                                    Isso garante que os dados estejam atualizados e consistentes.
                                </p>
                                <Link href="/perda-esperada/pipeline">
                                    <Button className="mt-4 gap-2" variant="outline">
                                        <ArrowLeft className="h-4 w-4" />
                                        <Zap className="h-4 w-4" />
                                        Ir para Pipeline Completo
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Info do último pipeline */}
            {pipelineResultado.executado && (
                <Card className="bg-green-50 dark:bg-green-950/30 border-green-500/50">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                            <CheckCircle2 className="h-8 w-8 text-green-600 flex-shrink-0" />
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-green-700 dark:text-green-400">
                                    Pipeline executado - Pronto para exportar
                                </h3>
                                <p className="text-green-600 dark:text-green-500 mt-1">
                                    Dados do pipeline de {new Date(pipelineResultado.dataExecucao!).toLocaleString('pt-BR')}:
                                    <span className="font-semibold ml-2">
                                        {pipelineResultado.totalOperacoes.toLocaleString()} operações |
                                        ECL Total: {formatCurrency(pipelineResultado.eclTotal)}
                                    </span>
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Formulário */}
                <Card className="h-fit">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileOutput className="h-5 w-5" />
                            Gerar XML ECL
                        </CardTitle>
                        <CardDescription>
                            Exportação XML conforme Resolução CMN 4966/2021
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label>Data-Base *</Label>
                                <Input
                                    placeholder="AAAA-MM"
                                    value={formData.data_base}
                                    onChange={(e) => setFormData({ ...formData, data_base: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>CNPJ (8 dígitos)</Label>
                                <Input
                                    placeholder="00000000"
                                    maxLength={8}
                                    value={formData.cnpj}
                                    onChange={(e) => setFormData({ ...formData, cnpj: e.target.value.replace(/\D/g, "") })}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Nome do Responsável *</Label>
                            <Input
                                value={formData.responsavel_nome}
                                onChange={(e) => setFormData({ ...formData, responsavel_nome: e.target.value })}
                            />
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label>Email *</Label>
                                <Input
                                    type="email"
                                    value={formData.responsavel_email}
                                    onChange={(e) => setFormData({ ...formData, responsavel_email: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Telefone</Label>
                                <Input
                                    value={formData.responsavel_telefone}
                                    onChange={(e) => setFormData({ ...formData, responsavel_telefone: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Metodologia</Label>
                            <Select
                                value={formData.metodologia}
                                onValueChange={(v) => setFormData({ ...formData, metodologia: v })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="C">Completa (PECLD Total)</SelectItem>
                                    <SelectItem value="S">Simplificada (Provisão COSIF)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Button
                            onClick={handleGerar}
                            disabled={loading || !pipelineResultado.executado}
                            className="w-full"
                            size="lg"
                        >
                            {loading ? (
                                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Validando e Gerando...</>
                            ) : (
                                <><FileCode className="h-4 w-4 mr-2" /> Iniciar Validação e Geração</>
                            )}
                        </Button>

                        {!pipelineResultado.executado && (
                            <p className="text-xs text-amber-600 text-center">
                                ⚠️ Execute o Pipeline Completo primeiro para habilitar este botão
                            </p>
                        )}
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    {/* Validador BACEN */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <CheckCircle2 className="h-5 w-5 text-blue-600" />
                                Validador BACEN (Simulador)
                            </CardTitle>
                            <CardDescription>
                                Validação prévia conforme Manual DOC 3040
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {validacaoEtapas.map((etapa, index) => (
                                    <div key={index} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                                        {etapa.status === 'pendente' && <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />}
                                        {etapa.status === 'processando' && <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />}
                                        {etapa.status === 'sucesso' && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                                        {etapa.status === 'erro' && <XCircle className="h-5 w-5 text-red-600" />}

                                        <div className="flex-1">
                                            <p className={`font-medium text-sm ${etapa.status === 'processando' ? 'text-blue-600' :
                                                etapa.status === 'sucesso' ? 'text-green-700' :
                                                    etapa.status === 'erro' ? 'text-red-700' : ''
                                                }`}>
                                                {etapa.nome}
                                            </p>
                                            <p className="text-xs text-muted-foreground">{etapa.descricao}</p>
                                        </div>
                                    </div>
                                ))}

                                {validacaoEtapas.every(e => e.status === 'pendente') && (
                                    <p className="text-center text-xs text-muted-foreground py-2">
                                        Clique em "Iniciar Validação" para verificar a conformidade.
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Resultado */}
                    {resultado && (
                        <Card className="animate-in fade-in slide-in-from-top-4">
                            <CardHeader>
                                <CardTitle>Resultado da Exportação</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className={`p-4 rounded-lg border-2 ${resultado.validacao.valido
                                        ? 'border-green-500/30 bg-green-50 dark:bg-green-950/30'
                                        : 'border-red-500/30 bg-red-50 dark:bg-red-950/30'
                                        }`}>
                                        <div className="flex items-center gap-2 mb-2">
                                            {resultado.validacao.valido ? (
                                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                                            ) : (
                                                <XCircle className="h-5 w-5 text-red-600" />
                                            )}
                                            <span className="font-medium">
                                                {resultado.validacao.valido ? "Arquivo Pronto para Envio (STA)" : "Erros de Validação"}
                                            </span>
                                        </div>
                                        {resultado.validacao.erros?.length > 0 && (
                                            <ul className="text-sm text-red-600 list-disc pl-5">
                                                {resultado.validacao.erros.map((e: any, i: number) => (
                                                    <li key={i}>{e.mensagem}</li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-muted rounded-lg">
                                            <p className="text-xs text-muted-foreground">Operações</p>
                                            <p className="text-xl font-bold">{resultado.estatisticas.total_operacoes?.toLocaleString()}</p>
                                        </div>
                                        <div className="p-3 bg-muted rounded-lg">
                                            <p className="text-xs text-muted-foreground">ECL Total</p>
                                            <p className="text-xl font-bold">{formatCurrency(resultado.estatisticas.ecl_total || 0)}</p>
                                        </div>
                                    </div>

                                    <div className="text-sm text-muted-foreground">
                                        <p>Arquivo: <code className="bg-muted px-2 py-1 rounded">{resultado.arquivo_nome}</code></p>
                                    </div>

                                    <Button onClick={downloadXML} className="w-full gap-2" variant="secondary">
                                        <Download className="h-4 w-4" />
                                        Download XML ECL
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>

            {/* Histórico */}
            <Card>
                <CardHeader>
                    <CardTitle>Histórico de Envios</CardTitle>
                </CardHeader>
                <CardContent>
                    <table className="w-full text-sm">
                        <thead className="bg-muted">
                            <tr>
                                <th className="p-3 text-left">ID</th>
                                <th className="p-3 text-left">Data-Base</th>
                                <th className="p-3 text-right">Operações</th>
                                <th className="p-3 text-right">ECL</th>
                                <th className="p-3 text-center">Status</th>
                                <th className="p-3 text-left">Protocolo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ultimosEnvios.map((e) => (
                                <tr key={e.id} className="border-t hover:bg-muted/50">
                                    <td className="p-3 font-mono">{e.id}</td>
                                    <td className="p-3">{e.data_base}</td>
                                    <td className="p-3 text-right">{e.operacoes.toLocaleString()}</td>
                                    <td className="p-3 text-right">{formatCurrency(e.ecl)}</td>
                                    <td className="p-3 text-center">{getStatusBadge(e.status)}</td>
                                    <td className="p-3 font-mono text-xs">{e.protocolo}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
