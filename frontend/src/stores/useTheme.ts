/**
 * Store de Temas - Sistema de 5 temas
 * 
 * Temas disponíveis:
 * - dark-ocean: Escuro azulado (referência Anomalia PIX)
 * - dark-midnight: Escuro puro
 * - light-snow: Claro suave
 * - light-cream: Claro creme
 * - system: Segue preferência do OS
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const THEMES = ['dark-ocean', 'dark-midnight', 'light-snow', 'light-cream', 'system'] as const
export type Theme = typeof THEMES[number]

export const THEME_LABELS: Record<Theme, string> = {
    'dark-ocean': 'Escuro Oceano',
    'dark-midnight': 'Escuro Meia-Noite',
    'light-snow': 'Claro Neve',
    'light-cream': 'Claro Creme',
    'system': 'Sistema',
}

interface ThemeState {
    theme: Theme
    setTheme: (theme: Theme) => void
    resolvedTheme: 'dark' | 'light'
}

// Detectar preferência do sistema
const getSystemTheme = (): 'dark' | 'light' => {
    if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'dark'
}

// Resolver tema baseado na configuração
const resolveTheme = (theme: Theme): 'dark' | 'light' => {
    if (theme === 'system') {
        return getSystemTheme()
    }
    return theme.startsWith('dark') ? 'dark' : 'light'
}

export const useTheme = create<ThemeState>()(
    persist(
        (set, get) => ({
            theme: 'dark-ocean',
            resolvedTheme: 'dark',

            setTheme: (theme: Theme) => {
                set({
                    theme,
                    resolvedTheme: resolveTheme(theme),
                })
            },
        }),
        {
            name: 'theme-storage',
            partialize: (state) => ({
                theme: state.theme,
            }),
            onRehydrateStorage: () => (state) => {
                // Recalcular resolvedTheme após rehidratação
                if (state) {
                    state.resolvedTheme = resolveTheme(state.theme)
                }
            },
        }
    )
)

// Listener para mudanças de preferência do sistema
if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const state = useTheme.getState()
        if (state.theme === 'system') {
            useTheme.setState({
                resolvedTheme: e.matches ? 'dark' : 'light',
            })
        }
    })
}
