/**
 * Sidebar de Artefatos Gerados
 * Exibe artefatos da sessão com opções de visualizar, baixar e excluir
 */

import { useState, useEffect, useCallback } from 'react';
import {
    FileText,
    FileSpreadsheet,
    FileImage,
    FileType,
    Presentation,
    Download,
    Eye,
    Trash2,
    X,
    Printer,
    Monitor,
    ChevronRight,
    ChevronLeft,
    RefreshCw
} from 'lucide-react';
import {
    Artifact,
    getArtifacts,
    getArtifactViewUrl,
    getArtifactDownloadUrl,
    deleteArtifact
} from '../../lib/api/agent_api';
import { cn } from '@/lib/utils';

interface ArtifactsSidebarProps {
    sessionId?: string;
    isOpen: boolean;
    onToggle: () => void;
    refreshTrigger?: number;  // Incrementar para forçar reload
    onArtifactsChange?: (count: number) => void;  // Notificar quando há artefatos
}

// Ícones por tipo de artefato
const getArtifactIcon = (tipo: string) => {
    switch (tipo) {
        case 'grafico':
            return <FileImage className="w-5 h-5 text-purple-400" />;
        case 'excel':
            return <FileSpreadsheet className="w-5 h-5 text-green-400" />;
        case 'pdf':
            return <FileText className="w-5 h-5 text-red-400" />;
        case 'docx':
            return <FileType className="w-5 h-5 text-blue-400" />;
        case 'pptx':
            return <Presentation className="w-5 h-5 text-orange-400" />;
        case 'markdown':
            return <FileText className="w-5 h-5 text-gray-400" />;
        default:
            return <FileText className="w-5 h-5 text-muted-foreground" />;
    }
};

// Formatar tamanho
const formatFileSize = (bytes: number): string => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export function ArtifactsSidebar({
    sessionId,
    isOpen,
    onToggle,
    refreshTrigger = 0,
    onArtifactsChange
}: ArtifactsSidebarProps) {
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState(false);
    const [viewingArtifact, setViewingArtifact] = useState<Artifact | null>(null);

    // Carregar artefatos
    const loadArtifacts = useCallback(async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const data = await getArtifacts(sessionId);
            setArtifacts(data);
            onArtifactsChange?.(data.length);
        } catch (error) {
            console.error('Erro ao carregar artefatos:', error);
        } finally {
            setLoading(false);
        }
    }, [sessionId, onArtifactsChange]);

    // Carregar quando a sessão muda ou quando refreshTrigger muda
    useEffect(() => {
        loadArtifacts();
    }, [sessionId, refreshTrigger, loadArtifacts]);

    const handleView = (artifact: Artifact) => {
        setViewingArtifact(artifact);
    };

    const handleDelete = async (artifactId: string) => {
        if (!confirm('Deseja excluir este artefato?')) return;
        try {
            await deleteArtifact(artifactId);
            setArtifacts(prev => prev.filter(a => a.id !== artifactId));
            onArtifactsChange?.(artifacts.length - 1);
        } catch (error) {
            console.error('Erro ao excluir artefato:', error);
        }
    };

    const handleDownload = (artifactId: string, versao: 'dark' | 'light') => {
        const url = getArtifactDownloadUrl(artifactId, versao);
        // Usar link para forçar download
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Sempre renderizar a sidebar, mesmo sem artefatos (para o toggle funcionar)
    return (
        <>
            {/* Toggle Button - Sempre visível */}
            <button
                onClick={onToggle}
                className={cn(
                    "fixed top-1/2 -translate-y-1/2 z-50",
                    "bg-primary hover:bg-primary/90 text-primary-foreground",
                    "px-2 py-6 rounded-l-lg shadow-lg",
                    "transition-all duration-300 ease-in-out",
                    "flex items-center gap-1",
                    isOpen ? "right-80" : "right-0"
                )}
            >
                {isOpen ? (
                    <ChevronRight className="w-4 h-4" />
                ) : (
                    <>
                        <ChevronLeft className="w-4 h-4" />
                        {artifacts.length > 0 && (
                            <span className="bg-white text-primary text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                                {artifacts.length}
                            </span>
                        )}
                    </>
                )}
            </button>

            {/* Sidebar */}
            <div
                className={cn(
                    "fixed right-0 top-0 h-full w-80 z-40",
                    "bg-card border-l border-border shadow-xl",
                    "transform transition-transform duration-300 ease-in-out",
                    "flex flex-col",
                    isOpen ? "translate-x-0" : "translate-x-full"
                )}
            >
                {/* Header */}
                <div className="p-4 border-b border-border flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                            <FileText className="w-5 h-5 text-primary" />
                            Artefatos
                        </h2>
                        <p className="text-sm text-muted-foreground mt-1">
                            {artifacts.length} artefato{artifacts.length !== 1 ? 's' : ''}
                        </p>
                    </div>
                    <button
                        onClick={loadArtifacts}
                        className="p-2 rounded-lg hover:bg-secondary transition-colors"
                        title="Atualizar"
                    >
                        <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                    </button>
                </div>

                {/* Artifacts List */}
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                    {loading && artifacts.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                            Carregando...
                        </div>
                    ) : artifacts.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>Nenhum artefato gerado ainda.</p>
                            <p className="text-xs mt-2">
                                Peça ao agente para gerar gráficos,<br />
                                planilhas ou documentos.
                            </p>
                        </div>
                    ) : (
                        artifacts.map(artifact => (
                            <div
                                key={artifact.id}
                                className="bg-secondary/50 rounded-xl p-4 border border-border hover:border-primary/50 transition-all"
                            >
                                <div className="flex items-start gap-3">
                                    <div className="p-2 bg-background rounded-lg">
                                        {getArtifactIcon(artifact.tipo)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-foreground truncate">
                                            {artifact.nome}
                                        </p>
                                        {artifact.descricao && (
                                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                                                {artifact.descricao}
                                            </p>
                                        )}
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {formatFileSize(artifact.tamanho)}
                                        </p>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-2 mt-4">
                                    {/* Visualizar */}
                                    <button
                                        onClick={() => handleView(artifact)}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary text-sm font-medium transition-colors"
                                    >
                                        <Eye className="w-4 h-4" />
                                        Visualizar
                                    </button>

                                    {/* Excluir */}
                                    <button
                                        onClick={() => handleDelete(artifact.id)}
                                        className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-colors"
                                        title="Excluir"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* View Modal */}
            {viewingArtifact && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
                    onClick={() => setViewingArtifact(null)}
                >
                    <div
                        className="relative w-[90vw] max-w-5xl h-[85vh] bg-card rounded-2xl border border-border shadow-2xl flex flex-col overflow-hidden"
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/30">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-background rounded-lg">
                                    {getArtifactIcon(viewingArtifact.tipo)}
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground">
                                        {viewingArtifact.nome}
                                    </h3>
                                    {viewingArtifact.descricao && (
                                        <p className="text-sm text-muted-foreground">
                                            {viewingArtifact.descricao}
                                        </p>
                                    )}
                                </div>
                            </div>
                            <button
                                onClick={() => setViewingArtifact(null)}
                                className="p-2 rounded-full hover:bg-secondary transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-auto p-6 flex items-center justify-center bg-secondary/20">
                            {viewingArtifact.tipo === 'grafico' ? (
                                <img
                                    src={getArtifactViewUrl(viewingArtifact.id)}
                                    alt={viewingArtifact.nome}
                                    className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
                                />
                            ) : viewingArtifact.tipo === 'pdf' ? (
                                <iframe
                                    src={getArtifactViewUrl(viewingArtifact.id)}
                                    className="w-full h-full rounded-lg border border-border"
                                    title={viewingArtifact.nome}
                                />
                            ) : (
                                <div className="text-center py-12">
                                    <div className="p-4 bg-secondary rounded-2xl inline-block mb-4">
                                        {getArtifactIcon(viewingArtifact.tipo)}
                                    </div>
                                    <p className="text-lg font-medium text-foreground mb-2">
                                        {viewingArtifact.nome}
                                    </p>
                                    <p className="text-muted-foreground mb-6">
                                        Este tipo de arquivo requer download para visualização.
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Tamanho: {formatFileSize(viewingArtifact.tamanho)}
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="flex items-center justify-between gap-3 p-4 border-t border-border bg-secondary/30">
                            <button
                                onClick={() => setViewingArtifact(null)}
                                className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Fechar
                            </button>

                            <div className="flex items-center gap-3">
                                {viewingArtifact.temVersoes ? (
                                    <>
                                        <button
                                            onClick={() => handleDownload(viewingArtifact.id, 'dark')}
                                            className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                                        >
                                            <Monitor className="w-4 h-4" />
                                            Download Digital
                                        </button>
                                        <button
                                            onClick={() => handleDownload(viewingArtifact.id, 'light')}
                                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                                        >
                                            <Printer className="w-4 h-4" />
                                            Download Impressão
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        onClick={() => handleDownload(viewingArtifact.id, 'dark')}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                                    >
                                        <Download className="w-4 h-4" />
                                        Download
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default ArtifactsSidebar;
