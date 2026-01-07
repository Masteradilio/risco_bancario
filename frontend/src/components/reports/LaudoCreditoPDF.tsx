/**
 * Componente de Laudo Técnico de Crédito em PDF
 * 
 * Gera um documento PDF profissional com todas as informações
 * de classificação de risco e cálculo de ECL do cliente.
 */

import React from 'react'
import { Document, Page, Text, View, StyleSheet, Image } from '@react-pdf/renderer'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

// Tipos
export interface DadosLaudo {
    cliente: {
        cpf: string
        nome: string
        dataNascimento?: string
        rendaMensal: number
        profissao?: string
        tempoRelacionamento: number
    }
    classificacao: {
        prinad: number
        rating: string
        pd12m: number
        pdLifetime: number
        stage: number
        dataClassificacao: string
    }
    operacao: {
        produto: string
        limiteAprovado: number
        saldoUtilizado: number
        taxaJuros?: number
        prazo: number
    }
    ecl: {
        pd: number
        lgd: number
        ead: number
        eclFinal: number
        grupoHomogeneo: string
        pisoAplicado: boolean
    }
    analista: {
        nome: string
        matricula: string
        departamento: string
    }
}

// Estilos
const styles = StyleSheet.create({
    page: {
        padding: 40,
        fontSize: 10,
        fontFamily: 'Helvetica',
        backgroundColor: '#ffffff',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        paddingBottom: 15,
        borderBottomWidth: 2,
        borderBottomColor: '#1e40af',
    },
    headerLeft: {
        flex: 1,
    },
    headerTitle: {
        fontSize: 18,
        fontFamily: 'Helvetica-Bold',
        color: '#1e40af',
    },
    headerSubtitle: {
        fontSize: 10,
        color: '#64748b',
        marginTop: 4,
    },
    headerRight: {
        alignItems: 'flex-end',
    },
    headerInfo: {
        fontSize: 8,
        color: '#64748b',
    },
    section: {
        marginBottom: 20,
    },
    sectionTitle: {
        fontSize: 12,
        fontFamily: 'Helvetica-Bold',
        color: '#1e40af',
        marginBottom: 10,
        paddingBottom: 5,
        borderBottomWidth: 1,
        borderBottomColor: '#e2e8f0',
    },
    row: {
        flexDirection: 'row',
        marginBottom: 8,
    },
    col2: {
        flex: 1,
        paddingRight: 10,
    },
    col3: {
        flex: 1,
        paddingRight: 10,
    },
    label: {
        fontSize: 8,
        color: '#64748b',
        marginBottom: 2,
        textTransform: 'uppercase',
    },
    value: {
        fontSize: 10,
        color: '#1e293b',
        fontFamily: 'Helvetica-Bold',
    },
    valueHighlight: {
        fontSize: 14,
        color: '#1e40af',
        fontFamily: 'Helvetica-Bold',
    },
    card: {
        backgroundColor: '#f8fafc',
        padding: 15,
        borderRadius: 4,
        marginBottom: 15,
    },
    cardTitle: {
        fontSize: 10,
        fontFamily: 'Helvetica-Bold',
        color: '#334155',
        marginBottom: 10,
    },
    summaryBox: {
        backgroundColor: '#1e40af',
        padding: 15,
        borderRadius: 4,
        marginBottom: 20,
    },
    summaryTitle: {
        fontSize: 10,
        color: '#93c5fd',
        marginBottom: 5,
    },
    summaryValue: {
        fontSize: 24,
        fontFamily: 'Helvetica-Bold',
        color: '#ffffff',
    },
    summarySubtext: {
        fontSize: 8,
        color: '#93c5fd',
        marginTop: 5,
    },
    table: {
        marginTop: 10,
    },
    tableHeader: {
        flexDirection: 'row',
        backgroundColor: '#e2e8f0',
        padding: 8,
    },
    tableHeaderCell: {
        flex: 1,
        fontSize: 8,
        fontFamily: 'Helvetica-Bold',
        color: '#475569',
        textTransform: 'uppercase',
    },
    tableRow: {
        flexDirection: 'row',
        padding: 8,
        borderBottomWidth: 1,
        borderBottomColor: '#e2e8f0',
    },
    tableCell: {
        flex: 1,
        fontSize: 9,
        color: '#1e293b',
    },
    footer: {
        position: 'absolute',
        bottom: 30,
        left: 40,
        right: 40,
        borderTopWidth: 1,
        borderTopColor: '#e2e8f0',
        paddingTop: 10,
    },
    footerText: {
        fontSize: 7,
        color: '#94a3b8',
        textAlign: 'center',
    },
    ratingBadge: {
        backgroundColor: '#22c55e',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        alignSelf: 'flex-start',
    },
    ratingBadgeText: {
        color: '#ffffff',
        fontSize: 12,
        fontFamily: 'Helvetica-Bold',
    },
    stageBadge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        alignSelf: 'flex-start',
    },
    stage1: {
        backgroundColor: '#22c55e',
    },
    stage2: {
        backgroundColor: '#f59e0b',
    },
    stage3: {
        backgroundColor: '#ef4444',
    },
    stageBadgeText: {
        color: '#ffffff',
        fontSize: 10,
        fontFamily: 'Helvetica-Bold',
    },
    disclaimer: {
        marginTop: 20,
        padding: 10,
        backgroundColor: '#fef3c7',
        borderRadius: 4,
    },
    disclaimerText: {
        fontSize: 8,
        color: '#92400e',
    },
})

// Helpers
const formatCPF = (cpf: string) => {
    if (!cpf) return '-'
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(value)
}

const formatPercent = (value: number, decimals = 2) => {
    return `${value.toFixed(decimals)}%`
}

const getRatingColor = (rating: string): string => {
    if (rating.startsWith('A')) return '#22c55e'
    if (rating.startsWith('B')) return '#f59e0b'
    if (rating.startsWith('C')) return '#f97316'
    return '#ef4444'
}

const getStageStyle = (stage: number) => {
    switch (stage) {
        case 1: return styles.stage1
        case 2: return styles.stage2
        case 3: return styles.stage3
        default: return styles.stage1
    }
}

// Componente principal
export function LaudoCreditoPDF({ dados }: { dados: DadosLaudo }) {
    const dataGeracao = format(new Date(), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })
    const numeroLaudo = `LC-${Date.now().toString(36).toUpperCase()}`

    return (
        <Document>
            <Page size="A4" style={styles.page}>
                {/* Header */}
                <View style={styles.header}>
                    <View style={styles.headerLeft}>
                        <Text style={styles.headerTitle}>LAUDO TÉCNICO DE CRÉDITO</Text>
                        <Text style={styles.headerSubtitle}>
                            Sistema de Risco Bancário | Resolução CMN 4.966/2021
                        </Text>
                    </View>
                    <View style={styles.headerRight}>
                        <Text style={styles.headerInfo}>Laudo Nº: {numeroLaudo}</Text>
                        <Text style={styles.headerInfo}>Data: {dataGeracao}</Text>
                    </View>
                </View>

                {/* Summary Box */}
                <View style={{ flexDirection: 'row', gap: 10, marginBottom: 20 }}>
                    <View style={[styles.summaryBox, { flex: 1 }]}>
                        <Text style={styles.summaryTitle}>ECL CALCULADO</Text>
                        <Text style={styles.summaryValue}>{formatCurrency(dados.ecl.eclFinal)}</Text>
                        <Text style={styles.summarySubtext}>Perda Esperada conforme IFRS 9</Text>
                    </View>
                    <View style={[styles.card, { flex: 1, justifyContent: 'center' }]}>
                        <Text style={styles.label}>RATING DE CRÉDITO</Text>
                        <View style={[styles.ratingBadge, { backgroundColor: getRatingColor(dados.classificacao.rating) }]}>
                            <Text style={styles.ratingBadgeText}>{dados.classificacao.rating}</Text>
                        </View>
                        <Text style={[styles.label, { marginTop: 10 }]}>STAGE IFRS 9</Text>
                        <View style={[styles.stageBadge, getStageStyle(dados.classificacao.stage)]}>
                            <Text style={styles.stageBadgeText}>Stage {dados.classificacao.stage}</Text>
                        </View>
                    </View>
                </View>

                {/* Dados do Cliente */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>1. IDENTIFICAÇÃO DO CLIENTE</Text>
                    <View style={styles.row}>
                        <View style={styles.col2}>
                            <Text style={styles.label}>CPF</Text>
                            <Text style={styles.value}>{formatCPF(dados.cliente.cpf)}</Text>
                        </View>
                        <View style={styles.col2}>
                            <Text style={styles.label}>Nome Completo</Text>
                            <Text style={styles.value}>{dados.cliente.nome || '-'}</Text>
                        </View>
                    </View>
                    <View style={styles.row}>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Renda Mensal</Text>
                            <Text style={styles.value}>{formatCurrency(dados.cliente.rendaMensal)}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Profissão</Text>
                            <Text style={styles.value}>{dados.cliente.profissao || '-'}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Tempo de Relacionamento</Text>
                            <Text style={styles.value}>{dados.cliente.tempoRelacionamento} meses</Text>
                        </View>
                    </View>
                </View>

                {/* Classificação de Risco */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>2. CLASSIFICAÇÃO DE RISCO (PRINAD)</Text>
                    <View style={styles.row}>
                        <View style={styles.col3}>
                            <Text style={styles.label}>PRINAD Score</Text>
                            <Text style={styles.valueHighlight}>{formatPercent(dados.classificacao.prinad)}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>PD 12 Meses</Text>
                            <Text style={styles.value}>{formatPercent(dados.classificacao.pd12m, 4)}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>PD Lifetime</Text>
                            <Text style={styles.value}>{formatPercent(dados.classificacao.pdLifetime, 4)}</Text>
                        </View>
                    </View>
                </View>

                {/* Operação de Crédito */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>3. OPERAÇÃO DE CRÉDITO</Text>
                    <View style={styles.row}>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Produto</Text>
                            <Text style={styles.value}>{dados.operacao.produto}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Limite Aprovado</Text>
                            <Text style={styles.value}>{formatCurrency(dados.operacao.limiteAprovado)}</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Saldo Utilizado</Text>
                            <Text style={styles.value}>{formatCurrency(dados.operacao.saldoUtilizado)}</Text>
                        </View>
                    </View>
                    <View style={styles.row}>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Prazo</Text>
                            <Text style={styles.value}>{dados.operacao.prazo} meses</Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Taxa de Utilização</Text>
                            <Text style={styles.value}>
                                {dados.operacao.limiteAprovado > 0
                                    ? formatPercent((dados.operacao.saldoUtilizado / dados.operacao.limiteAprovado) * 100)
                                    : '0%'
                                }
                            </Text>
                        </View>
                        <View style={styles.col3}>
                            <Text style={styles.label}>Limite Disponível</Text>
                            <Text style={styles.value}>
                                {formatCurrency(dados.operacao.limiteAprovado - dados.operacao.saldoUtilizado)}
                            </Text>
                        </View>
                    </View>
                </View>

                {/* Cálculo ECL */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>4. CÁLCULO DA PERDA ESPERADA (ECL)</Text>
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Fórmula: ECL = PD × LGD × EAD</Text>
                        <View style={styles.table}>
                            <View style={styles.tableHeader}>
                                <Text style={styles.tableHeaderCell}>Componente</Text>
                                <Text style={styles.tableHeaderCell}>Valor</Text>
                                <Text style={styles.tableHeaderCell}>Descrição</Text>
                            </View>
                            <View style={styles.tableRow}>
                                <Text style={styles.tableCell}>PD (Probability of Default)</Text>
                                <Text style={styles.tableCell}>{formatPercent(dados.ecl.pd, 4)}</Text>
                                <Text style={styles.tableCell}>Probabilidade de inadimplência</Text>
                            </View>
                            <View style={styles.tableRow}>
                                <Text style={styles.tableCell}>LGD (Loss Given Default)</Text>
                                <Text style={styles.tableCell}>{formatPercent(dados.ecl.lgd, 2)}</Text>
                                <Text style={styles.tableCell}>Perda em caso de default</Text>
                            </View>
                            <View style={styles.tableRow}>
                                <Text style={styles.tableCell}>EAD (Exposure at Default)</Text>
                                <Text style={styles.tableCell}>{formatCurrency(dados.ecl.ead)}</Text>
                                <Text style={styles.tableCell}>Exposição no momento do default</Text>
                            </View>
                            <View style={[styles.tableRow, { backgroundColor: '#f1f5f9' }]}>
                                <Text style={[styles.tableCell, { fontFamily: 'Helvetica-Bold' }]}>ECL FINAL</Text>
                                <Text style={[styles.tableCell, { fontFamily: 'Helvetica-Bold', color: '#1e40af' }]}>
                                    {formatCurrency(dados.ecl.eclFinal)}
                                </Text>
                                <Text style={styles.tableCell}>
                                    {dados.ecl.pisoAplicado ? 'Com piso regulamentar' : 'Sem piso'}
                                </Text>
                            </View>
                        </View>
                    </View>
                    <View style={styles.row}>
                        <View style={styles.col2}>
                            <Text style={styles.label}>Grupo Homogêneo</Text>
                            <Text style={styles.value}>{dados.ecl.grupoHomogeneo}</Text>
                        </View>
                        <View style={styles.col2}>
                            <Text style={styles.label}>Piso Regulamentar (BCB 352)</Text>
                            <Text style={styles.value}>{dados.ecl.pisoAplicado ? 'Aplicado' : 'Não aplicado'}</Text>
                        </View>
                    </View>
                </View>

                {/* Disclaimer */}
                <View style={styles.disclaimer}>
                    <Text style={styles.disclaimerText}>
                        Este laudo foi gerado automaticamente pelo Sistema de Risco Bancário em conformidade
                        com a Resolução CMN nº 4.966/2021 e IFRS 9. As informações apresentadas são baseadas
                        nos dados disponíveis na data de geração e nos modelos de risco aprovados.
                    </Text>
                </View>

                {/* Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>
                        Responsável: {dados.analista.nome} | Matrícula: {dados.analista.matricula} |
                        Departamento: {dados.analista.departamento}
                    </Text>
                    <Text style={styles.footerText}>
                        Sistema de Risco Bancário - Documento gerado em {dataGeracao} - Confidencial
                    </Text>
                </View>
            </Page>
        </Document>
    )
}
