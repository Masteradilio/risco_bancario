import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function MainLayout() {
    const location = useLocation()
    const isAgentPage = location.pathname === '/agent'

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <Header />

                {/* Page Content */}
                <main className={`flex-1 overflow-hidden ${isAgentPage ? '' : 'overflow-y-auto p-6'}`}>
                    {isAgentPage ? (
                        <Outlet />
                    ) : (
                        <div className="max-w-screen-2xl mx-auto animate-fade-in">
                            <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-700 dark:text-amber-300">
                                DEMONSTRAÇÃO COM DADOS SINTÉTICOS — não usar para decisão de crédito, contabilização ou reporte oficial.
                            </div>
                            <Outlet />
                        </div>
                    )}
                </main>
            </div>
        </div>
    )
}
