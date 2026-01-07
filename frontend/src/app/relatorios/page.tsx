"use client"

import { useState } from "react"
import { useAuth } from "@/stores/useAuth"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { toast } from "sonner"
import {
    FileText,
    Download,
    Printer,
    FileSpreadsheet,
    Building2,
    User,
    Calendar,
    Shield
} from "lucide-react"
import dynamic from 'next/dynamic'
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"

// Dynamic import para componentes PDF (client-side only)
const PDFDownloadLink = dynamic(
    () => import('@react-pdf/renderer').then(mod => mod.PDFDownloadLink),
    { ssr: false, loading: () => <span>Carregando...</span> }
)

// Componente de laudo será importado dinamicamente
import { LaudoCreditoPDF, DadosLaudo } from "@/components/reports/LaudoCreditoPDF"

// Tipo de relatório
type TipoRelatorio = 'laudo_credito' | 'portfolio_ecl' | 'regulatorio_bacen'

export default function RelatoriosPage() {
    const { user, checkPermission, addAuditLog } = useAuth()
    const [tipoRelatorio, setTipoRelatorio] = useState<TipoRelatorio>('laudo_credito')
    const [loading, setLoading] = useState(false)

    // Dados do formulário de laudo
    const [dadosLaudo, setDadosLaudo] = useState<DadosLaudo>({
        cliente: {
            cpf: '',
            nome: '',
            dataNascimento: '',
            rendaMensal: 0,
            profissao: '',
            tempoRelacionamento: 0,
        },
        classificacao: {
            prinad: 0,
            rating: 'A1',
            pd12m: 0,
            pdLifetime: 0,
            stage: 1,
            dataClassificacao: new Date().toISOString(),
        },
        operacao: {
            produto: 'Consignado',
            limiteAprovado: 0,
            saldoUtilizado: 0,
            taxaJuros: 0,
            prazo: 0,
        },
        ecl: {
            pd: 0,
            lgd: 0,
            ead: 0,
            eclFinal: 0,
            grupoHomogeneo: 'GH1',
            pisoAplicado: false,
        },
        analista: {
            nome: user?.nome || '',
            matricula: user?.matricula || '',
            departamento: user?.departamento || '',
        },
    })

    // Verificar permissão de export
    const canExportPDF = checkPermission('export:pdf')
    const canExportBACEN = checkPermission('export:bacen')

    const handleInputChange = (section: keyof DadosLaudo, field: string, value: any) => {
        setDadosLaudo(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [field]: value
            }
        }))
    }

    const handleGerarLaudo = () => {
        if (!dadosLaudo.cliente.cpf || !dadosLaudo.cliente.nome) {
            toast.error("Preencha pelo menos CPF e Nome do cliente")
            return
        }

        addAuditLog('EXPORT', 'RELATORIO_PDF', `Gerou laudo de crédito para CPF ${dadosLaudo.cliente.cpf}`)
        toast.success("Laudo gerado com sucesso!")
    }

    if (!canExportPDF) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="w-full max-w-md text-center">
                    <CardContent className="pt-6">
                        <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                        <h2 className="text-xl font-semibold mb-2">Acesso Restrito</h2>
                        <p className="text-muted-foreground">
                            Você não tem permissão para gerar relatórios.
                            Esta funcionalidade está disponível para Gestores e Administradores.
                        </p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                    <FileText className="h-8 w-8" />
                    Relatórios e Exportações
                </h1>
                <p className="text-muted-foreground">
                    Gere laudos técnicos, relatórios de portfólio e arquivos regulatórios
                </p>
            </div>

            <Tabs defaultValue="laudo" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="laudo">Laudo de Crédito</TabsTrigger>
                    <TabsTrigger value="portfolio">Portfólio ECL</TabsTrigger>
                    <TabsTrigger value="regulatorio" disabled={!canExportBACEN}>
                        Regulatório BACEN
                    </TabsTrigger>
                </TabsList>

                {/* Tab: Laudo de Crédito */}
                <TabsContent value="laudo" className="space-y-6">
                    <div className="grid gap-6 lg:grid-cols-2">
                        {/* Formulário */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <User className="h-5 w-5" />
                                    Dados do Cliente
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label>CPF</Label>
                                        <Input
                                            placeholder="00000000000"
                                            value={dadosLaudo.cliente.cpf}
                                            onChange={(e) => handleInputChange('cliente', 'cpf', e.target.value.replace(/\D/g, ''))}
                                            maxLength={11}
                                        />
                                    </div>
                                    <div>
                                        <Label>Nome Completo</Label>
                                        <Input
                                            placeholder="Nome do cliente"
                                            value={dadosLaudo.cliente.nome}
                                            onChange={(e) => handleInputChange('cliente', 'nome', e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Renda Mensal (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={dadosLaudo.cliente.rendaMensal || ''}
                                            onChange={(e) => handleInputChange('cliente', 'rendaMensal', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Tempo de Relacionamento (meses)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0"
                                            value={dadosLaudo.cliente.tempoRelacionamento || ''}
                                            onChange={(e) => handleInputChange('cliente', 'tempoRelacionamento', parseInt(e.target.value) || 0)}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Shield className="h-5 w-5" />
                                    Classificação de Risco
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label>PRINAD Score (%)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0-100"
                                            value={dadosLaudo.classificacao.prinad || ''}
                                            onChange={(e) => handleInputChange('classificacao', 'prinad', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Rating</Label>
                                        <Select
                                            value={dadosLaudo.classificacao.rating}
                                            onValueChange={(value) => handleInputChange('classificacao', 'rating', value)}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D', 'DEFAULT'].map(r => (
                                                    <SelectItem key={r} value={r}>{r}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label>PD 12 meses (%)</Label>
                                        <Input
                                            type="number"
                                            step="0.01"
                                            placeholder="0.00"
                                            value={dadosLaudo.classificacao.pd12m || ''}
                                            onChange={(e) => handleInputChange('classificacao', 'pd12m', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Stage IFRS 9</Label>
                                        <Select
                                            value={dadosLaudo.classificacao.stage.toString()}
                                            onValueChange={(value) => handleInputChange('classificacao', 'stage', parseInt(value))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="1">Stage 1</SelectItem>
                                                <SelectItem value="2">Stage 2</SelectItem>
                                                <SelectItem value="3">Stage 3</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Building2 className="h-5 w-5" />
                                    Operação de Crédito
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label>Produto</Label>
                                        <Select
                                            value={dadosLaudo.operacao.produto}
                                            onValueChange={(value) => handleInputChange('operacao', 'produto', value)}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Consignado">Consignado</SelectItem>
                                                <SelectItem value="Cartão de Crédito">Cartão de Crédito</SelectItem>
                                                <SelectItem value="Imobiliário">Imobiliário</SelectItem>
                                                <SelectItem value="Veículo">Veículo</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <Label>Limite Aprovado (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={dadosLaudo.operacao.limiteAprovado || ''}
                                            onChange={(e) => handleInputChange('operacao', 'limiteAprovado', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Saldo Utilizado (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={dadosLaudo.operacao.saldoUtilizado || ''}
                                            onChange={(e) => handleInputChange('operacao', 'saldoUtilizado', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>Prazo (meses)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0"
                                            value={dadosLaudo.operacao.prazo || ''}
                                            onChange={(e) => handleInputChange('operacao', 'prazo', parseInt(e.target.value) || 0)}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <FileSpreadsheet className="h-5 w-5" />
                                    Cálculo ECL
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <Label>PD (%)</Label>
                                        <Input
                                            type="number"
                                            step="0.0001"
                                            placeholder="0.00"
                                            value={dadosLaudo.ecl.pd || ''}
                                            onChange={(e) => handleInputChange('ecl', 'pd', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>LGD (%)</Label>
                                        <Input
                                            type="number"
                                            step="0.01"
                                            placeholder="0.00"
                                            value={dadosLaudo.ecl.lgd || ''}
                                            onChange={(e) => handleInputChange('ecl', 'lgd', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>EAD (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={dadosLaudo.ecl.ead || ''}
                                            onChange={(e) => handleInputChange('ecl', 'ead', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                    <div>
                                        <Label>ECL Final (R$)</Label>
                                        <Input
                                            type="number"
                                            placeholder="0.00"
                                            value={dadosLaudo.ecl.eclFinal || ''}
                                            onChange={(e) => handleInputChange('ecl', 'eclFinal', parseFloat(e.target.value) || 0)}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Ações */}
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex flex-wrap gap-4">
                                <PDFDownloadLink
                                    document={<LaudoCreditoPDF dados={dadosLaudo} />}
                                    fileName={`laudo_credito_${dadosLaudo.cliente.cpf || 'novo'}_${format(new Date(), 'yyyyMMdd')}.pdf`}
                                    className="inline-flex"
                                >
                                    {({ loading }) => (
                                        <Button disabled={loading} className="gap-2" onClick={handleGerarLaudo}>
                                            <Download className="h-4 w-4" />
                                            {loading ? 'Gerando PDF...' : 'Baixar Laudo PDF'}
                                        </Button>
                                    )}
                                </PDFDownloadLink>
                                <Button variant="outline" className="gap-2">
                                    <Printer className="h-4 w-4" />
                                    Imprimir
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Tab: Portfólio ECL */}
                <TabsContent value="portfolio">
                    <Card>
                        <CardHeader>
                            <CardTitle>Relatório de Portfólio ECL</CardTitle>
                            <CardDescription>
                                Gere relatórios consolidados de toda a carteira de crédito
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="py-8 text-center text-muted-foreground">
                            <FileSpreadsheet className="h-16 w-16 mx-auto mb-4 opacity-50" />
                            <p>Em desenvolvimento...</p>
                            <p className="text-sm">Esta funcionalidade estará disponível em breve</p>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Tab: Regulatório BACEN */}
                <TabsContent value="regulatorio">
                    <Card>
                        <CardHeader>
                            <CardTitle>Exportação Regulatória BACEN</CardTitle>
                            <CardDescription>
                                Gere arquivos XML/JSON no formato exigido pelo Banco Central
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="py-8 text-center text-muted-foreground">
                            <Building2 className="h-16 w-16 mx-auto mb-4 opacity-50" />
                            <p>Em desenvolvimento...</p>
                            <p className="text-sm">Formato conforme Resolução BCB 4.966/2021</p>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
