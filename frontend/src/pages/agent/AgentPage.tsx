/**
 * Página do Agente de IA
 * 
 * Interface completa para:
 * - Chat com o agente
 * - Histórico de sessões
 * - Artefatos gerados
 * - Ferramentas disponíveis
 */

import { useState, useEffect, useRef, FormEvent } from 'react';
import {
    Bot,
    Send,
    Plus,
    Trash2,
    MessageSquare,
    FileText,
    Loader2,
    Settings,
    Sparkles,
    Calculator,
    FileSearch,
    TrendingUp
} from 'lucide-react';
import {
    sendMessage,
    getSessions,
    createSession,
    getSessionMessages,
    deleteSession,
    ChatSession,
    ToolInfo,
    FileUpload as FileUploadType
} from '../../lib/api/agent_api';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { ArtifactsSidebar } from './ArtifactsSidebar';
import { FileUploadButton } from './FileUploadButton';

// Componentes customizados para renderização de Markdown
const markdownComponents: Components = {
    h1: ({ children }) => <h1 className="text-xl font-bold text-foreground mt-4 mb-2 border-b border-border pb-2">{children}</h1>,
    h2: ({ children }) => <h2 className="text-lg font-bold text-foreground mt-4 mb-2">{children}</h2>,
    h3: ({ children }) => <h3 className="text-base font-semibold text-foreground mt-3 mb-1">{children}</h3>,
    p: ({ children }) => <p className="text-foreground leading-relaxed mb-3">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-6 space-y-1 mb-3">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-6 space-y-2 mb-3">{children}</ol>,
    li: ({ children }) => <li className="text-foreground pl-1">{children}</li>,
    strong: ({ children }) => <strong className="font-bold text-primary">{children}</strong>,
    em: ({ children }) => <em className="italic text-muted-foreground">{children}</em>,
    code: ({ children, className }) => {
        const isBlock = className?.includes('language-');
        if (isBlock) {
            return (
                <pre className="bg-secondary/50 border border-border rounded-lg p-3 overflow-x-auto my-3">
                    <code className="text-sm text-foreground font-mono">{children}</code>
                </pre>
            );
        }
        return <code className="bg-secondary/50 px-1.5 py-0.5 rounded text-sm font-mono text-primary">{children}</code>;
    },
    pre: ({ children }) => <>{children}</>,
    blockquote: ({ children }) => (
        <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground my-3">
            {children}
        </blockquote>
    ),
    table: ({ children }) => (
        <div className="overflow-x-auto my-3">
            <table className="min-w-full border border-border rounded-lg overflow-hidden">
                {children}
            </table>
        </div>
    ),
    thead: ({ children }) => <thead className="bg-secondary/50">{children}</thead>,
    tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
    tr: ({ children }) => <tr className="hover:bg-secondary/30">{children}</tr>,
    th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-foreground">{children}</th>,
    td: ({ children }) => <td className="px-3 py-2 text-sm text-foreground">{children}</td>,
    a: ({ href, children }) => (
        <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
            {children}
        </a>
    ),
    hr: () => <hr className="border-border my-4" />,
};

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'tool';
    content: string;
    toolName?: string;
    timestamp: Date;
}

// Ferramentas disponíveis do agente com prompts automáticos
interface ToolWithPrompt extends ToolInfo {
    prompt: string;
}

const defaultTools: ToolWithPrompt[] = [
    { name: 'consultar_score_prinad', description: 'Consulta score PRINAD de um cliente', prompt: 'Consulte o score PRINAD do cliente CPF 123.456.789-00' },
    { name: 'classificar_risco_cliente', description: 'Classifica risco de crédito', prompt: 'Classifique o risco de crédito do cliente com os seguintes dados: renda R$ 5.000, tempo de conta 24 meses' },
    { name: 'calcular_ecl_individual', description: 'Calcula ECL de um contrato', prompt: 'Calcule a ECL (Perda Esperada) do contrato número 12345 com saldo de R$ 50.000' },
    { name: 'calcular_ecl_portfolio', description: 'Calcula ECL do portfólio', prompt: 'Calcule a ECL total do portfólio de crédito pessoal' },
    { name: 'simular_cenario_forward_looking', description: 'Simula cenários forward-looking', prompt: 'Simule um cenário forward-looking considerando aumento de 2% na taxa Selic' },
    { name: 'buscar_regulamentacao', description: 'Busca regulamentações BACEN', prompt: 'Busque a regulamentação CMN 4966/2021 sobre provisão para perdas esperadas' },
    { name: 'exportar_xml_bacen', description: 'Exporta XML para BACEN', prompt: 'Exporte o arquivo XML 4060 (SCR) da data-base dezembro/2025' },
    { name: 'validar_conformidade', description: 'Valida conformidade CMN 4966', prompt: 'Valide a conformidade dos cálculos de ECL com a resolução CMN 4966' },
    { name: 'ler_arquivo_excel', description: 'Lê arquivos Excel', prompt: 'Leia o arquivo Excel da carteira de crédito e apresente um resumo' },
    { name: 'gerar_grafico', description: 'Gera gráficos e visualizações', prompt: 'Gere um gráfico de evolução da ECL nos últimos 12 meses' },
    { name: 'pesquisar_web', description: 'Pesquisa informações na web', prompt: 'Pesquise as últimas notícias sobre regulamentação bancária do BACEN' },
];

export function AgentPage() {
    // Estado
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [uploads, setUploads] = useState<FileUploadType[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [artifactRefreshTrigger, setArtifactRefreshTrigger] = useState(0);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Carregar sessões ao montar
    useEffect(() => {
        loadSessions();
    }, []);

    // Carregar mensagens quando mudar sessão ativa
    useEffect(() => {
        if (activeSessionId) {
            loadMessages(activeSessionId);
        } else {
            setMessages([]);
        }
    }, [activeSessionId]);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadSessions = async () => {
        try {
            const data = await getSessions();
            setSessions(data);
        } catch (error) {
            console.error('Erro ao carregar sessões:', error);
        }
    };

    const loadMessages = async (sessionId: string) => {
        try {
            const data = await getSessionMessages(sessionId);
            setMessages(data.map(m => ({
                ...m,
                timestamp: new Date(m.createdAt)
            })));
        } catch (error) {
            console.error('Erro ao carregar mensagens:', error);
        }
    };



    const handleNewSession = async () => {
        try {
            const session = await createSession();
            setSessions(prev => [session, ...prev]);
            setActiveSessionId(session.id);
            setMessages([]);
        } catch (error) {
            console.error('Erro ao criar sessão:', error);
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        if (!confirm('Excluir esta conversa?')) return;

        try {
            await deleteSession(sessionId);
            setSessions(prev => prev.filter(s => s.id !== sessionId));
            if (activeSessionId === sessionId) {
                setActiveSessionId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Erro ao excluir sessão:', error);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await sendMessage(userMessage.content, activeSessionId || undefined);

            if (!activeSessionId) {
                setActiveSessionId(response.sessionId);
                loadSessions();
            }

            const assistantMessage: Message = {
                id: Date.now().toString() + '_response',
                role: 'assistant',
                content: response.response,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Se um artefato foi gerado, atualizar e abrir a sidebar
            if (response.artifactId) {
                setArtifactRefreshTrigger(prev => prev + 1);
                setSidebarOpen(true);
            }

            if (response.artifactId) {
                setArtifactRefreshTrigger(prev => prev + 1);
                setSidebarOpen(true);
            }
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            const errorMessage: Message = {
                id: Date.now().toString() + '_error',
                role: 'assistant',
                content: 'Desculpe, ocorreu um erro. Tente novamente.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const quickActions = [
        { text: 'Calcular ECL de um contrato', icon: Calculator, color: 'text-emerald-400' },
        { text: 'Consultar score PRINAD', icon: TrendingUp, color: 'text-purple-400' },
        { text: 'Buscar regulamentação CMN 4966', icon: FileSearch, color: 'text-blue-400' },
        { text: 'Simular cenário forward-looking', icon: Sparkles, color: 'text-amber-400' },
    ];

    return (
        <div className="flex h-full overflow-hidden bg-background">
            {/* Sidebar - Sessões e Ferramentas */}
            <div className="w-72 bg-card border-r border-border flex flex-col">
                {/* Header */}
                <div className="p-3 border-b border-border">
                    <button
                        onClick={handleNewSession}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 px-4 py-2.5",
                            "bg-primary text-primary-foreground rounded-lg",
                            "hover:opacity-90 transition-all font-medium"
                        )}
                    >
                        <Plus className="w-4 h-4" />
                        Nova Conversa
                    </button>
                </div>

                {/* Sessions List - 30% da altura */}
                <div className="h-[25%] overflow-y-auto border-b border-border">
                    <div className="p-2">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold px-2 mb-2">
                            Conversas
                        </p>
                        {sessions.length === 0 ? (
                            <div className="p-3 text-center text-muted-foreground">
                                <MessageSquare className="w-6 h-6 mx-auto mb-1 opacity-50" />
                                <p className="text-xs">Nenhuma conversa</p>
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {sessions.map((session) => (
                                    <div
                                        key={session.id}
                                        className={cn(
                                            "group flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all",
                                            activeSessionId === session.id
                                                ? 'bg-primary/10 border border-primary/30'
                                                : 'hover:bg-secondary/50'
                                        )}
                                        onClick={() => setActiveSessionId(session.id)}
                                    >
                                        <MessageSquare className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-medium truncate text-foreground">{session.titulo}</p>
                                        </div>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteSession(session.id); }}
                                            className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Tools List - 70% da altura, sempre visível */}
                <div className="flex-1 overflow-y-auto">
                    <div className="p-2">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold px-2 mb-2 flex items-center gap-2">
                            <Settings className="w-3 h-3" />
                            Ferramentas ({defaultTools.length})
                        </p>
                        <div className="space-y-1">
                            {defaultTools.map((tool) => (
                                <button
                                    key={tool.name}
                                    onClick={() => setInput(tool.prompt)}
                                    className={cn(
                                        "w-full text-left p-2.5 rounded-lg transition-all",
                                        "bg-secondary/20 hover:bg-secondary/50 border border-transparent",
                                        "hover:border-primary/30 group"
                                    )}
                                >
                                    <p className="text-xs font-medium text-foreground group-hover:text-primary transition-colors">
                                        {tool.name.replace(/_/g, ' ')}
                                    </p>
                                    <p className="text-xs text-muted-foreground truncate mt-0.5">
                                        {tool.description}
                                    </p>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto">
                    {messages.length === 0 && !activeSessionId ? (
                        <div className="flex flex-col items-center justify-center h-full text-center p-6">
                            {/* Hero Icon */}
                            <div className="w-20 h-20 bg-gradient-to-br from-primary to-purple-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-primary/20">
                                <Bot className="w-10 h-10 text-white" />
                            </div>

                            <h2 className="text-2xl font-bold text-foreground mb-2">
                                Assistente de Risco Bancário
                            </h2>
                            <p className="text-muted-foreground max-w-md mb-8">
                                Consulte scores PRINAD, calcule ECL, busque regulamentações BACEN e muito mais.
                            </p>

                            {/* Quick Actions - Styled like dashboard cards */}
                            <div className="grid grid-cols-2 gap-4 max-w-xl w-full">
                                {quickActions.map((action) => (
                                    <button
                                        key={action.text}
                                        onClick={() => setInput(action.text)}
                                        className={cn(
                                            "flex items-center gap-3 p-4 text-left",
                                            "bg-card border border-border rounded-xl",
                                            "hover:border-primary/50 hover:bg-secondary/30",
                                            "transition-all group"
                                        )}
                                    >
                                        <div className={cn(
                                            "w-10 h-10 rounded-lg bg-secondary/50 flex items-center justify-center",
                                            "group-hover:bg-primary/10 transition-colors"
                                        )}>
                                            <action.icon className={cn("w-5 h-5", action.color)} />
                                        </div>
                                        <span className="text-sm text-foreground font-medium">{action.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="p-6 space-y-4">
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={cn("flex", msg.role === 'user' ? 'justify-end' : 'justify-start')}
                                >
                                    <div
                                        className={cn(
                                            "max-w-[70%] rounded-xl px-4 py-3",
                                            msg.role === 'user'
                                                ? 'bg-primary text-primary-foreground'
                                                : msg.role === 'tool'
                                                    ? 'bg-amber-500/10 border border-amber-500/30'
                                                    : 'bg-card border border-border'
                                        )}
                                    >
                                        {msg.role === 'tool' && msg.toolName && (
                                            <div className="flex items-center gap-2 text-amber-400 text-xs mb-2">
                                                <Sparkles className="w-3 h-3" />
                                                <span>Ferramenta: {msg.toolName}</span>
                                            </div>
                                        )}
                                        {msg.role === 'assistant' || msg.role === 'tool' ? (
                                            <div className="max-w-none">
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={markdownComponents}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        ) : (
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-card border border-border rounded-xl px-4 py-3 flex items-center gap-3">
                                        <Loader2 className="w-5 h-5 animate-spin text-primary" />
                                        <span className="text-muted-foreground">Processando...</span>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-border bg-card/50">
                    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                        {/* Arquivos anexados */}
                        {uploads.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                                {uploads.map(file => (
                                    <div
                                        key={file.id}
                                        className="flex items-center gap-2 bg-secondary/50 border border-border rounded-lg px-2 py-1 text-xs"
                                    >
                                        <FileText className="w-3 h-3 text-muted-foreground" />
                                        <span className="text-foreground max-w-[100px] truncate">
                                            {file.nome}
                                        </span>
                                        <button
                                            type="button"
                                            onClick={() => setUploads(prev => prev.filter(u => u.id !== file.id))}
                                            className="p-0.5 hover:bg-destructive/20 rounded"
                                        >
                                            <Trash2 className="w-3 h-3 text-destructive" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="flex items-end gap-3">
                            {/* Botão de Upload */}
                            <FileUploadButton
                                sessionId={activeSessionId || undefined}
                                onUploadComplete={(file) => setUploads(prev => [...prev, file])}
                                onError={(error) => console.error(error)}
                            />

                            <div className="flex-1 relative">
                                <textarea
                                    ref={inputRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Pergunte algo sobre risco de crédito, ECL, regulamentações..."
                                    className={cn(
                                        "w-full resize-none rounded-xl border border-border",
                                        "bg-card px-4 py-3 pr-12",
                                        "text-foreground placeholder:text-muted-foreground",
                                        "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                                        "max-h-32 transition-all"
                                    )}
                                    rows={1}
                                    disabled={isLoading}
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className={cn(
                                    "p-3 rounded-xl transition-all",
                                    "bg-primary text-primary-foreground",
                                    "hover:opacity-90",
                                    "disabled:opacity-50 disabled:cursor-not-allowed"
                                )}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Sidebar de Artefatos */}
            <ArtifactsSidebar
                sessionId={activeSessionId || undefined}
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)}
                refreshTrigger={artifactRefreshTrigger}
                onArtifactsChange={(count) => {
                    if (count > 0 && !sidebarOpen) {
                        setSidebarOpen(true);
                    }
                }}
            />
        </div>
    );
}

export default AgentPage;
