/**
 * Floating Chat - Widget de chat flutuante
 * 
 * Exibe um botão no canto inferior direito que expande
 * para uma janela de chat com o Agente IA.
 */

import { useState, useRef, useEffect, FormEvent } from 'react';
import {
    MessageSquare,
    X,
    Send,
    Loader2,
    Minimize2,
    Sparkles,
    Bot
} from 'lucide-react';
import { sendMessage, ChatMessage } from '../../lib/api/agent_api';
import ReactMarkdown from 'react-markdown';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export function FloatingChat() {
    const [isOpen, setIsOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [unreadCount, setUnreadCount] = useState(0);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll para novas mensagens
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus no input quando abre
    useEffect(() => {
        if (isOpen && !isMinimized) {
            inputRef.current?.focus();
        }
    }, [isOpen, isMinimized]);

    // Reset unread quando abre
    useEffect(() => {
        if (isOpen) {
            setUnreadCount(0);
        }
    }, [isOpen]);

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
            const response = await sendMessage(userMessage.content, sessionId || undefined);

            if (!sessionId) {
                setSessionId(response.sessionId);
            }

            const assistantMessage: Message = {
                id: Date.now().toString() + '_response',
                role: 'assistant',
                content: response.response,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Incrementar unread se minimizado
            if (isMinimized) {
                setUnreadCount(prev => prev + 1);
            }
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            const errorMessage: Message = {
                id: Date.now().toString() + '_error',
                role: 'assistant',
                content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
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

    // Botão flutuante quando fechado
    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-indigo-600 
                   rounded-full shadow-lg hover:shadow-xl transition-all duration-300 
                   flex items-center justify-center text-white hover:scale-110 z-50
                   group"
                title="Abrir Assistente IA"
            >
                <Bot className="w-6 h-6" />
                <Sparkles className="w-3 h-3 absolute top-2 right-2 text-yellow-300 animate-pulse" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full 
                         text-xs flex items-center justify-center font-bold">
                        {unreadCount}
                    </span>
                )}
            </button>
        );
    }

    // Janela minimizada
    if (isMinimized) {
        return (
            <div className="fixed bottom-6 right-6 w-72 bg-white dark:bg-gray-800 rounded-lg 
                      shadow-2xl border border-gray-200 dark:border-gray-700 z-50">
                <div
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-600 to-indigo-600 
                     rounded-t-lg cursor-pointer"
                    onClick={() => setIsMinimized(false)}
                >
                    <div className="flex items-center gap-2 text-white">
                        <Bot className="w-5 h-5" />
                        <span className="font-medium">Assistente IA</span>
                        {unreadCount > 0 && (
                            <span className="bg-red-500 text-xs px-1.5 py-0.5 rounded-full">
                                {unreadCount}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
                        className="text-white/80 hover:text-white"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>
        );
    }

    // Janela expandida
    return (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white dark:bg-gray-800 
                    rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 
                    flex flex-col z-50 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-600 to-indigo-600">
                <div className="flex items-center gap-2 text-white">
                    <Bot className="w-5 h-5" />
                    <span className="font-semibold">Assistente IA</span>
                    <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">Beta</span>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsMinimized(true)}
                        className="p-1.5 text-white/80 hover:text-white hover:bg-white/20 rounded"
                        title="Minimizar"
                    >
                        <Minimize2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="p-1.5 text-white/80 hover:text-white hover:bg-white/20 rounded"
                        title="Fechar"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
                {messages.length === 0 && (
                    <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                        <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p className="font-medium">Olá! Como posso ajudar?</p>
                        <p className="text-sm mt-1">
                            Pergunte sobre ECL, PRINAD, regulamentações BACEN...
                        </p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[85%] rounded-lg px-4 py-2 ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-bl-none'
                                }`}
                        >
                            {msg.role === 'assistant' ? (
                                <div className="prose prose-sm dark:prose-invert max-w-none">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            ) : (
                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                          rounded-lg rounded-bl-none px-4 py-2 flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                            <span className="text-sm text-gray-500">Pensando...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-end gap-2">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Digite sua mensagem..."
                        className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 
                     bg-white dark:bg-gray-800 px-3 py-2 text-sm 
                     focus:outline-none focus:ring-2 focus:ring-blue-500
                     max-h-32"
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
    );
}

export default FloatingChat;
