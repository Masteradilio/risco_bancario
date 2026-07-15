import { Outlet } from 'react-router-dom'
import Header from '@/components/layout/Header'
import Sidebar from '@/components/layout/Sidebar'

export default function MainLayout() {
    return <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto p-6"><div className="mx-auto max-w-screen-2xl animate-fade-in"><div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300">DEMONSTRAÇÃO COM DADOS SINTÉTICOS — não usar para decisão de crédito, contabilização ou reporte oficial.</div><Outlet /></div></main>
        </div>
    </div>
}
