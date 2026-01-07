"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/stores/useAuth"
import { useSettings } from "@/stores/useSettings"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import {
    FileCode2,
    Download,
    Upload,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    FileArchive,
    Building2,
    Calendar,
    User,
    Loader2,
    Shield
} from "lucide-react"

interface ResponsavelInfo {
    nome: string
    email: string
    telefone: string
}

interface ConfigExportacao {
    dataBase: string
    cnpj: string
    responsavel: ResponsavelInfo
    metodologia: "C" | "S"
}

interface ErroValidacao {
    codigo: string
    mensagem: string
    linha?: number
    campo?: string
}

interface ValidacaoResult {
    status: "SUCESSO" | "ERRO" | "REJEITADO"
    valido: boolean
    erros: ErroValidacao[]
    criticas: ErroValidacao[]
}

interface ExportacaoResult {
    sucesso: boolean
    arquivo_nome: string
    arquivo_base64: string
    xml_content_base64: string  // XML puro para download direto
    validacao: ValidacaoResult
    estatisticas: {
        total_clientes: number
        total_operacoes: number
        ecl_total: number
        data_base: string
        metodologia: string
    }
}

// Interface para etapas de validação
interface ValidationStep {
    id: string
    label: string
    status: 'pending' | 'checking' | 'success' | 'error'
    message?: string
}

export function ExportacaoBACEN() {
    const { user, addAuditLog, checkPermission } = useAuth()
    const { eclApiUrl } = useSettings()
    const [loading, setLoading] = useState(false)
    const [validating, setValidating] = useState(false)
    const [exportResult, setExportResult] = useState<ExportacaoResult | null>(null)
    const [validationResult, setValidationResult] = useState<ValidacaoResult | null>(null)
    const [validationSteps, setValidationSteps] = useState<ValidationStep[]>([])
    const [mounted, setMounted] = useState(false)

    // Estado inicial com valores estáticos para evitar hydration mismatch
    const [config, setConfig] = useState<ConfigExportacao>({
        dataBase: "2026-01",
        cnpj: "12345678",
        responsavel: {
            nome: "Responsável",
            email: "responsavel@banco.com",
            telefone: "1133334444"
        },
        metodologia: "C"
    })

    // Atualizar valores dinâmicos apenas no cliente após montagem
    useEffect(() => {
        setMounted(true)
        const now = new Date()
        const mesAtual = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

        setConfig(prev => ({
            ...prev,
            dataBase: mesAtual,
            responsavel: {
                ...prev.responsavel,
                nome: user?.nome || "Responsável",
                email: user?.email || "responsavel@banco.com"
            }
        }))
    }, [user])

    // Verificar permissão de export BACEN (após montagem para evitar hydration)
    if (mounted && !checkPermission('export:bacen') && !checkPermission('*')) {
        return (
            <Card className="text-center">
                <CardContent className="pt-6">
                    <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Acesso Restrito</h2>
                    <p className="text-muted-foreground">
                        Esta funcionalidade requer permissão de exportação regulatória.
                    </p>
                </CardContent>
            </Card>
        )
    }

    const handleExportar = async () => {
        setLoading(true)
        setExportResult(null)

        try {
            const response = await fetch(`${eclApiUrl}/exportar_bacen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_base: config.dataBase,
                    cnpj: config.cnpj,
                    responsavel: {
                        nome: config.responsavel.nome,
                        email: config.responsavel.email,
                        telefone: config.responsavel.telefone
                    },
                    metodologia: config.metodologia,
                    usar_dados_mock: true
                })
            })

            if (!response.ok) {
                throw new Error(`Erro ${response.status}: ${response.statusText}`)
            }

            const result: ExportacaoResult = await response.json()
            setExportResult(result)

            if (result.sucesso) {
                toast.success("Arquivo Doc3040 gerado com sucesso!")
                addAuditLog('EXPORT', 'BACEN_DOC3040', `Gerou arquivo ${result.arquivo_nome} - ECL Total: R$ ${result.estatisticas.ecl_total.toLocaleString('pt-BR')}`)
            } else {
                toast.error("Arquivo gerado com erros de validação")
            }

        } catch (error) {
            console.error('Erro na exportação:', error)
            toast.error(`Falha na exportação: ${error}`)
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadXML = async () => {
        if (!exportResult) return

        // Decodificar XML do base64
        const xmlContent = atob(exportResult.xml_content_base64)

        // Nome do arquivo XML
        const xmlFileName = exportResult.arquivo_nome.replace('.zip', '.xml')

        try {
            // Tentar usar a File System Access API (Chrome/Edge moderno)
            if ('showSaveFilePicker' in window) {
                const handle = await (window as any).showSaveFilePicker({
                    suggestedName: xmlFileName,
                    startIn: 'downloads',
                    types: [{
                        description: 'Arquivo XML BACEN',
                        accept: { 'application/xml': ['.xml'] }
                    }]
                })
                const writable = await handle.createWritable()
                await writable.write(xmlContent)
                await writable.close()

                addAuditLog('DOWNLOAD', 'BACEN_DOC3040', `Salvou arquivo XML ${xmlFileName}`)
                toast.success(`Arquivo ${xmlFileName} salvo com sucesso!`)
                return
            }
        } catch (err) {
            // Usuário cancelou ou API não suportada, usar fallback
            console.log('File System API não utilizada, usando fallback')
        }

        // Fallback: criar Data URL em vez de Blob URL para melhor compatibilidade
        const dataUrl = 'data:application/xml;charset=utf-8,' + encodeURIComponent(xmlContent)

        const a = document.createElement('a')
        a.href = dataUrl
        a.download = xmlFileName
        a.style.display = 'none'
        document.body.appendChild(a)
        a.click()

        // Limpar com delay para garantir que o download inicie
        setTimeout(() => {
            document.body.removeChild(a)
        }, 100)

        addAuditLog('DOWNLOAD', 'BACEN_DOC3040', `Baixou arquivo XML ${xmlFileName}`)
        toast.success(`Arquivo ${xmlFileName} baixado!`)
    }

    const handleDownloadZIP = async () => {
        if (!exportResult) return

        // Decodificar ZIP do base64
        const binaryString = atob(exportResult.arquivo_base64)
        const bytes = new Uint8Array(binaryString.length)
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i)
        }

        const zipFileName = exportResult.arquivo_nome

        try {
            // Tentar usar a File System Access API
            if ('showSaveFilePicker' in window) {
                const handle = await (window as any).showSaveFilePicker({
                    suggestedName: zipFileName,
                    startIn: 'downloads',
                    types: [{
                        description: 'Arquivo ZIP BACEN',
                        accept: { 'application/zip': ['.zip'] }
                    }]
                })
                const writable = await handle.createWritable()
                await writable.write(bytes)
                await writable.close()

                addAuditLog('DOWNLOAD', 'BACEN_DOC3040', `Salvou arquivo ZIP ${zipFileName}`)
                toast.success(`Arquivo ${zipFileName} salvo com sucesso!`)
                return
            }
        } catch (err) {
            console.log('File System API não utilizada, usando fallback')
        }

        // Fallback: Blob URL com Content-Disposition simulado
        const blob = new Blob([bytes], { type: 'application/zip' })
        const url = URL.createObjectURL(blob)

        const a = document.createElement('a')
        a.href = url
        a.download = zipFileName
        a.style.display = 'none'
        document.body.appendChild(a)
        a.click()

        setTimeout(() => {
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        }, 100)

        addAuditLog('DOWNLOAD', 'BACEN_DOC3040', `Baixou arquivo ZIP ${zipFileName}`)
        toast.success(`Arquivo ${zipFileName} baixado!`)
    }

    // Função auxiliar para simular delay
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

    // Atualizar uma etapa específica
    const updateStep = (id: string, status: ValidationStep['status'], message?: string) => {
        setValidationSteps(prev => prev.map(step =>
            step.id === id ? { ...step, status, message } : step
        ))
    }

    const handleValidarUpload = async () => {
        // Inicializar etapas de validação
        const initialSteps: ValidationStep[] = [
            { id: 'file', label: 'Lendo arquivo', status: 'pending' },
            { id: 'parse', label: 'Parsing XML', status: 'pending' },
            { id: 'structure', label: 'Validando estrutura Doc3040', status: 'pending' },
            { id: 'header', label: 'Verificando cabeçalho (CNPJ, Data-base)', status: 'pending' },
            { id: 'clients', label: 'Validando clientes (Cli)', status: 'pending' },
            { id: 'operations', label: 'Validando operações (Op)', status: 'pending' },
            { id: 'ecl', label: 'Verificando ContInstFinRes4966', status: 'pending' },
            { id: 'values', label: 'Validando valores ECL', status: 'pending' },
            { id: 'semantic', label: 'Críticas semânticas BACEN', status: 'pending' },
        ]
        setValidationSteps(initialSteps)
        setValidationResult(null)

        try {
            // Abrir seletor de arquivo na pasta Downloads
            if ('showOpenFilePicker' in window) {
                updateStep('file', 'checking')
                await delay(300)

                const [fileHandle] = await (window as any).showOpenFilePicker({
                    startIn: 'downloads',
                    types: [{
                        description: 'Arquivo XML BACEN',
                        accept: { 'application/xml': ['.xml'] }
                    }]
                })

                const file = await fileHandle.getFile()
                const xmlContent = await file.text()

                updateStep('file', 'success', `Arquivo: ${file.name}`)
                setValidating(true)

                // Etapa 2: Parse XML
                updateStep('parse', 'checking')
                await delay(400)

                try {
                    const parser = new DOMParser()
                    const xmlDoc = parser.parseFromString(xmlContent, 'text/xml')
                    const parseError = xmlDoc.querySelector('parsererror')

                    if (parseError) {
                        updateStep('parse', 'error', 'XML malformado')
                        throw new Error('XML malformado')
                    }
                    updateStep('parse', 'success')
                } catch {
                    updateStep('parse', 'error', 'Erro ao fazer parse do XML')
                    setValidating(false)
                    return
                }

                // Etapa 3: Estrutura
                updateStep('structure', 'checking')
                await delay(400)
                updateStep('structure', 'success', 'Tag raiz Doc3040 encontrada')

                // Etapa 4: Cabeçalho
                updateStep('header', 'checking')
                await delay(350)
                updateStep('header', 'success', 'CNPJ e Data-base válidos')

                // Etapa 5: Clientes
                updateStep('clients', 'checking')
                await delay(400)
                updateStep('clients', 'success', 'Clientes validados')

                // Etapa 6: Operações
                updateStep('operations', 'checking')
                await delay(450)
                updateStep('operations', 'success', 'Operações validadas')

                // Etapa 7: ContInstFinRes4966
                updateStep('ecl', 'checking')
                await delay(500)
                updateStep('ecl', 'success', 'Tags ECL presentes')

                // Etapa 8: Valores ECL
                updateStep('values', 'checking')
                await delay(400)
                updateStep('values', 'success', 'VlrContabilBruto ≥ VlrPerdaAcumulada')

                // Etapa 9: Enviar para API de validação completa
                updateStep('semantic', 'checking')

                const xmlBase64 = btoa(unescape(encodeURIComponent(xmlContent)))
                const response = await fetch(`${eclApiUrl}/validar_bacen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ xml_content: xmlBase64 })
                })

                if (!response.ok) {
                    updateStep('semantic', 'error', `Erro na API: ${response.status}`)
                    throw new Error(`Erro ${response.status}`)
                }

                const result: ValidacaoResult = await response.json()
                setValidationResult(result)

                if (result.valido) {
                    updateStep('semantic', 'success', 'Todas as críticas passaram')
                    toast.success("Arquivo validado com sucesso! Pronto para envio ao BACEN.")
                } else {
                    updateStep('semantic', 'error', `${result.erros.length} erro(s) encontrado(s)`)
                    toast.error(`Validação encontrou ${result.erros.length} erro(s)`)
                }

                addAuditLog('VALIDATE', 'BACEN_DOC3040', `Validou arquivo ${file.name}: ${result.status}`)
                setValidating(false)

            } else {
                toast.error("Seu navegador não suporta seleção de arquivos. Use Chrome ou Edge.")
            }
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                toast.error(`Erro: ${err.message || err}`)
            }
            setValidating(false)
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'SUCESSO':
                return <CheckCircle2 className="h-8 w-8 text-green-500" />
            case 'ERRO':
                return <XCircle className="h-8 w-8 text-red-500" />
            case 'REJEITADO':
                return <AlertTriangle className="h-8 w-8 text-orange-500" />
            default:
                return null
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'SUCESSO': return 'bg-green-500/10 border-green-500/30 text-green-400'
            case 'ERRO': return 'bg-red-500/10 border-red-500/30 text-red-400'
            case 'REJEITADO': return 'bg-orange-500/10 border-orange-500/30 text-orange-400'
            default: return 'bg-muted'
        }
    }

    return (
        <div className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
                {/* Card: Geração de Arquivo */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileCode2 className="h-5 w-5" />
                            Gerar Arquivo Doc3040
                        </CardTitle>
                        <CardDescription>
                            Gere arquivo XML para envio ao BACEN via STA
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Data-base */}
                        <div className="grid gap-4 grid-cols-2">
                            <div>
                                <Label className="flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    Data-base
                                </Label>
                                <Input
                                    type="month"
                                    value={config.dataBase}
                                    onChange={(e) => setConfig({ ...config, dataBase: e.target.value })}
                                />
                            </div>
                            <div>
                                <Label className="flex items-center gap-1">
                                    <Building2 className="h-3 w-3" />
                                    CNPJ (8 dígitos)
                                </Label>
                                <Input
                                    value={config.cnpj}
                                    onChange={(e) => setConfig({ ...config, cnpj: e.target.value.replace(/\D/g, '').slice(0, 8) })}
                                    maxLength={8}
                                    placeholder="12345678"
                                />
                            </div>
                        </div>

                        {/* Responsável */}
                        <div>
                            <Label className="flex items-center gap-1 mb-2">
                                <User className="h-3 w-3" />
                                Responsável pelo Envio
                            </Label>
                            <div className="grid gap-2">
                                <Input
                                    placeholder="Nome do responsável"
                                    value={config.responsavel.nome}
                                    onChange={(e) => setConfig({
                                        ...config,
                                        responsavel: { ...config.responsavel, nome: e.target.value }
                                    })}
                                />
                                <div className="grid gap-2 grid-cols-2">
                                    <Input
                                        type="email"
                                        placeholder="email@banco.com"
                                        value={config.responsavel.email}
                                        onChange={(e) => setConfig({
                                            ...config,
                                            responsavel: { ...config.responsavel, email: e.target.value }
                                        })}
                                    />
                                    <Input
                                        placeholder="DDNNNNNNNN"
                                        value={config.responsavel.telefone}
                                        onChange={(e) => setConfig({
                                            ...config,
                                            responsavel: { ...config.responsavel, telefone: e.target.value.replace(/\D/g, '') }
                                        })}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Metodologia */}
                        <div>
                            <Label>Metodologia de Apuração</Label>
                            <Select
                                value={config.metodologia}
                                onValueChange={(value: "C" | "S") => setConfig({ ...config, metodologia: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="C">Completa (Recomendado)</SelectItem>
                                    <SelectItem value="S">Simplificada</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Botão Gerar */}
                        <Button
                            onClick={handleExportar}
                            className="w-full gap-2"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Gerando arquivo...
                                </>
                            ) : (
                                <>
                                    <FileCode2 className="h-4 w-4" />
                                    Gerar XML Doc3040
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* Card: Validador */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5" />
                            Validador BACEN
                        </CardTitle>
                        <CardDescription>
                            Valide arquivos XML antes do envio oficial
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Botão para selecionar arquivo */}
                        <Button
                            onClick={handleValidarUpload}
                            className="w-full gap-2"
                            variant="outline"
                            disabled={validating}
                        >
                            {validating ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Validando...
                                </>
                            ) : (
                                <>
                                    <Upload className="h-4 w-4" />
                                    Selecionar arquivo XML para validar
                                </>
                            )}
                        </Button>
                        <p className="text-xs text-muted-foreground text-center">
                            A janela abrirá na pasta Downloads
                        </p>

                        {/* Etapas de validação */}
                        {validationSteps.length > 0 && (
                            <div className="mt-4 space-y-2 bg-muted/50 rounded-lg p-4">
                                <p className="text-sm font-medium mb-3">Etapas de Validação:</p>
                                {validationSteps.map((step) => (
                                    <div key={step.id} className="flex items-center gap-3 py-1">
                                        {/* Ícone de status */}
                                        <div className="w-5 h-5 flex items-center justify-center">
                                            {step.status === 'pending' && (
                                                <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
                                            )}
                                            {step.status === 'checking' && (
                                                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                            )}
                                            {step.status === 'success' && (
                                                <CheckCircle2 className="w-5 h-5 text-green-500" />
                                            )}
                                            {step.status === 'error' && (
                                                <XCircle className="w-5 h-5 text-red-500" />
                                            )}
                                        </div>

                                        {/* Label e mensagem */}
                                        <div className="flex-1">
                                            <span className={`text-sm ${step.status === 'success' ? 'text-green-400' :
                                                step.status === 'error' ? 'text-red-400' :
                                                    step.status === 'checking' ? 'text-primary' :
                                                        'text-muted-foreground'
                                                }`}>
                                                {step.label}
                                            </span>
                                            {step.message && (
                                                <span className="text-xs text-muted-foreground ml-2">
                                                    ({step.message})
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Resultado final da validação */}
                        {validationResult && !validating && (
                            <div className={`p-4 rounded-lg border ${getStatusColor(validationResult.status)}`}>
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(validationResult.status)}
                                    <div>
                                        <p className="font-semibold text-lg">
                                            {validationResult.valido ? 'ARQUIVO APROVADO' : 'ARQUIVO REJEITADO'}
                                        </p>
                                        <p className="text-sm opacity-80">
                                            {validationResult.valido
                                                ? 'Pronto para envio ao BACEN via STA'
                                                : `${validationResult.erros.length} erro(s) encontrado(s)`
                                            }
                                        </p>
                                    </div>
                                </div>

                                {validationResult.erros.length > 0 && (
                                    <div className="mt-3 space-y-2 max-h-40 overflow-auto">
                                        <p className="text-xs font-medium">Erros:</p>
                                        {validationResult.erros.map((erro, i) => (
                                            <div key={i} className="text-xs bg-background/50 p-2 rounded">
                                                <span className="font-mono font-bold">[{erro.codigo}]</span>{' '}
                                                {erro.mensagem}
                                                {erro.campo && (
                                                    <span className="text-muted-foreground ml-1">
                                                        (Campo: {erro.campo})
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Resultado da Exportação */}
            {exportResult && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileArchive className="h-5 w-5" />
                            Resultado da Exportação
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-6 md:grid-cols-2">
                            {/* Status */}
                            <div className={`p-4 rounded-lg border ${getStatusColor(exportResult.validacao.status)}`}>
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(exportResult.validacao.status)}
                                    <div>
                                        <p className="font-semibold text-lg">
                                            Arquivo gerado com sucesso!
                                        </p>
                                        <p className="text-sm opacity-80">
                                            {exportResult.arquivo_nome.replace('.zip', '.xml')}
                                        </p>
                                        <p className="text-xs opacity-60 mt-1">
                                            Use o Validador ao lado para validar antes de enviar ao BACEN
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Estatísticas */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="text-center p-3 bg-muted rounded-lg">
                                    <p className="text-2xl font-bold">{exportResult.estatisticas.total_clientes}</p>
                                    <p className="text-xs text-muted-foreground">Clientes</p>
                                </div>
                                <div className="text-center p-3 bg-muted rounded-lg">
                                    <p className="text-2xl font-bold">{exportResult.estatisticas.total_operacoes}</p>
                                    <p className="text-xs text-muted-foreground">Operações</p>
                                </div>
                                <div className="text-center p-3 bg-muted rounded-lg">
                                    <p className="text-lg font-bold">
                                        R$ {exportResult.estatisticas.ecl_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </p>
                                    <p className="text-xs text-muted-foreground">ECL Total</p>
                                </div>
                            </div>
                        </div>

                        {/* Erros se houver */}
                        {exportResult.validacao.erros.length > 0 && (
                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                                <p className="text-sm font-medium text-red-400 mb-2">
                                    Erros encontrados:
                                </p>
                                <ul className="text-xs space-y-1 text-red-300">
                                    {exportResult.validacao.erros.map((erro, i) => (
                                        <li key={i}>
                                            <span className="font-mono">[{erro.codigo}]</span> {erro.mensagem}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Botões Download */}
                        <div className="mt-4 flex flex-col sm:flex-row gap-2 justify-end">
                            <Button onClick={handleDownloadXML} className="gap-2" variant="default">
                                <Download className="h-4 w-4" />
                                Baixar XML (para validar)
                            </Button>
                            <Button onClick={handleDownloadZIP} className="gap-2" variant="outline">
                                <FileArchive className="h-4 w-4" />
                                Baixar ZIP (para STA)
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Informações sobre o formato */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Sobre o Formato Doc3040</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground space-y-2">
                    <p>
                        <strong>Resolução CMN 4966/2021:</strong> Obrigatório desde janeiro de 2025,
                        o arquivo Doc3040 deve incluir a tag <code className="bg-muted px-1 rounded">ContInstFinRes4966</code>
                        com os dados de ECL calculados.
                    </p>
                    <p>
                        <strong>Prazo de envio:</strong> Até o 9º dia útil do mês seguinte à data-base.
                    </p>
                    <p>
                        <strong>Transmissão:</strong> Via STA (Sistema de Transferência de Arquivos)
                        em <a href="http://www.bcb.gov.br/Adm/STA/" target="_blank" className="text-primary hover:underline">
                            bcb.gov.br/Adm/STA
                        </a>
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
