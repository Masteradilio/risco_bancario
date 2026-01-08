import axios, { AxiosInstance } from 'axios'

// Create API instances
export function createApiClient(baseURL: string): AxiosInstance {
    return axios.create({
        baseURL,
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json',
        },
    })
}

// PRINAD API
export const prinadApi = {
    health: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/health')
    },

    classify: async (baseUrl: string, cpf: string) => {
        const client = createApiClient(baseUrl)
        return client.post('/simple_classify', { cpf })
    },

    classifyExplained: async (baseUrl: string, cpf: string) => {
        const client = createApiClient(baseUrl)
        return client.post('/explained_classify', { cpf })
    },

    classifyMultiple: async (baseUrl: string, cpfs: string[]) => {
        const client = createApiClient(baseUrl)
        return client.post('/multiple_classify', { cpfs })
    },
}

// ECL API
export const eclApi = {
    health: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/health')
    },

    calcular: async (baseUrl: string, data: {
        cpf: string
        produto: string
        saldo_utilizado: number
        limite_total: number
        dias_atraso?: number
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/calcular', data)
    },

    calcularDireto: async (baseUrl: string, data: {
        cliente_id: string
        produto: string
        saldo_utilizado: number
        limite_total: number
        dias_atraso: number
        prinad: number
        rating: string
        pd_12m: number
        pd_lifetime: number
        stage: number
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/calcular_direto', data)
    },

    calcularPortfolio: async (baseUrl: string, operacoes: any[]) => {
        const client = createApiClient(baseUrl)
        return client.post('/calcular_portfolio', { operacoes })
    },

    gruposHomogeneos: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/grupos_homogeneos')
    },

    // Write-off endpoints
    writeoffRegistrarBaixa: async (baseUrl: string, data: {
        contrato_id: string
        valor_baixado: number
        motivo: string
        provisao_constituida: number
        estagio_na_baixa?: number
        cliente_id?: string
        produto?: string
        observacoes?: string
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/writeoff/registrar-baixa', data)
    },

    writeoffRegistrarRecuperacao: async (baseUrl: string, data: {
        contrato_id: string
        valor_recuperado: number
        tipo?: string
        observacoes?: string
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/writeoff/registrar-recuperacao', data)
    },

    writeoffRelatorio: async (baseUrl: string, contratoId: string) => {
        const client = createApiClient(baseUrl)
        return client.get(`/writeoff/relatorio/${contratoId}`)
    },

    writeoffConsolidado: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/writeoff/relatorio-consolidado')
    },

    writeoffTaxaRecuperacao: async (baseUrl: string, filtros: {
        produto?: string
        motivo?: string
        periodo_inicial?: string
        periodo_final?: string
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/writeoff/taxa-recuperacao', filtros)
    },

    // Exportação BACEN
    exportarBACEN: async (baseUrl: string, data: any) => {
        const client = createApiClient(baseUrl)
        return client.post('/exportar_bacen', data)
    },

    validarBACEN: async (baseUrl: string, xmlContent: string) => {
        const client = createApiClient(baseUrl)
        return client.post('/validar_bacen', { xml_content: xmlContent })
    },
}


// Propensao API
export const propensaoApi = {
    health: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/health')
    },

    score: async (baseUrl: string, data: {
        cpf: string
        produto: string
        prinad: number
        renda: number
        utilizacao: number
        tempo_relacionamento: number
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/score', data)
    },

    recomendar: async (baseUrl: string, data: {
        cpf: string
        produto: string
        prinad: number
        propensity_score: number
        limite_atual: number
        saldo_utilizado: number
        margem_disponivel?: number
    }) => {
        const client = createApiClient(baseUrl)
        return client.post('/recomendar', data)
    },

    simular: async (baseUrl: string, portfolio: any[], cenario: string) => {
        const client = createApiClient(baseUrl)
        return client.post('/simular', { portfolio, cenario })
    },

    produtos: async (baseUrl: string) => {
        const client = createApiClient(baseUrl)
        return client.get('/produtos')
    },
}
