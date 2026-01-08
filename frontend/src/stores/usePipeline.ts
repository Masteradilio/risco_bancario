import { create } from 'zustand'

interface PipelineResultado {
    executado: boolean
    dataExecucao: string | null
    totalOperacoes: number
    eclTotal: number
    eclStage1: number
    eclStage2: number
    eclStage3: number
    tempoExecucao: number
    distribuicaoStages: Array<{
        stage: string
        quantidade: number
        ecl: number
        cor: string
    }>
}

interface PipelineStore {
    resultado: PipelineResultado
    setResultado: (resultado: Partial<PipelineResultado>) => void
    resetResultado: () => void
}

const estadoInicial: PipelineResultado = {
    executado: false,
    dataExecucao: null,
    totalOperacoes: 0,
    eclTotal: 0,
    eclStage1: 0,
    eclStage2: 0,
    eclStage3: 0,
    tempoExecucao: 0,
    distribuicaoStages: [],
}

export const usePipelineStore = create<PipelineStore>((set) => ({
    resultado: estadoInicial,
    setResultado: (novoResultado) =>
        set((state) => ({
            resultado: { ...state.resultado, ...novoResultado },
        })),
    resetResultado: () => set({ resultado: estadoInicial }),
}))
