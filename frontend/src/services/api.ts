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
