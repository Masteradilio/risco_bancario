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
                            <Outlet />
                        </div>
                    )}
                </main>
            </div>
        </div>
    )
}

