import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SettingsState {
    // API URLs
    prinadApiUrl: string
    eclApiUrl: string
    propensaoApiUrl: string

    // OpenRouter
    openrouterApiKey: string
    openrouterModel: string

    // Setters
    setPrinadApiUrl: (url: string) => void
    setEclApiUrl: (url: string) => void
    setPropensaoApiUrl: (url: string) => void
    setOpenrouterApiKey: (key: string) => void
    setOpenrouterModel: (model: string) => void
}

export const useSettings = create<SettingsState>()(
    persist(
        (set) => ({
            // Default values
            prinadApiUrl: 'http://localhost:8001',
            eclApiUrl: 'http://localhost:8002',
            propensaoApiUrl: 'http://localhost:8003',
            openrouterApiKey: '',
            openrouterModel: 'moonshotai/kimi-k2:free',

            // Setters
            setPrinadApiUrl: (url) => set({ prinadApiUrl: url }),
            setEclApiUrl: (url) => set({ eclApiUrl: url }),
            setPropensaoApiUrl: (url) => set({ propensaoApiUrl: url }),
            setOpenrouterApiKey: (key) => set({ openrouterApiKey: key }),
            setOpenrouterModel: (model) => set({ openrouterModel: model }),
        }),
        {
            name: 'settings-storage',
        }
    )
)
