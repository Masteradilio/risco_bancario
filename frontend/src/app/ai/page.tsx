"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Bot, Send } from "lucide-react"

export default function AIPage() {
    const [message, setMessage] = useState("")
    const [messages, setMessages] = useState<Array<{ role: string, content: string }>>([
        {
            role: "assistant",
            content: "Olá! Sou o assistente IA do Sistema de Risco Bancário. Posso ajudá-lo com:\n\n• Classificar clientes (PRINAD)\n• Calcular ECL (Perda Esperada)\n• Recomendar ajustes de limite\n• Explicar conceitos do sistema\n\nComo posso ajudar?"
        }
    ])
    const [loading, setLoading] = useState(false)

    const handleSend = async () => {
        if (!message.trim()) return

        const userMessage = { role: "user", content: message }
        setMessages([...messages, userMessage])
        setMessage("")
        setLoading(true)

        // Simulação - Em produção, conectaria ao LangGraph
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "Esta funcionalidade está em desenvolvimento. Em breve o agente IA estará disponível com LangGraph e integração OpenRouter."
            }])
            setLoading(false)
        }, 1000)
    }

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="mb-6">
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                    <Bot className="h-8 w-8" />
                    Assistente IA
                </h1>
                <p className="text-muted-foreground">
                    Utilize linguagem natural para interagir com o sistema
                </p>
            </div>

            <Card className="flex-1 flex flex-col">
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg p-3 ${msg.role === "user"
                                        ? "bg-primary text-primary-foreground"
                                        : "bg-muted"
                                    }`}
                            >
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-muted rounded-lg p-3">
                                <p className="animate-pulse">Pensando...</p>
                            </div>
                        </div>
                    )}
                </CardContent>
                <div className="p-4 border-t">
                    <div className="flex gap-2">
                        <Input
                            placeholder="Digite sua mensagem..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        />
                        <Button onClick={handleSend} disabled={loading}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    )
}
