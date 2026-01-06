"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSettings } from "@/stores/useSettings"
import { useTheme, applyTheme } from "@/stores/useTheme"
import { toast } from "sonner"

export default function SettingsPage() {
    const {
        prinadApiUrl, setPrinadApiUrl,
        eclApiUrl, setEclApiUrl,
        propensaoApiUrl, setPropensaoApiUrl,
        openrouterApiKey, setOpenrouterApiKey,
        openrouterModel, setOpenrouterModel
    } = useSettings()

    const { theme, setTheme } = useTheme()

    const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
        setTheme(newTheme)
        applyTheme(newTheme)
    }

    const handleSave = () => {
        toast.success("Configurações salvas com sucesso")
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Configurações</h1>
                <p className="text-muted-foreground">
                    Configure as opções do sistema
                </p>
            </div>

            <Tabs defaultValue="apis">
                <TabsList>
                    <TabsTrigger value="apis">APIs Backend</TabsTrigger>
                    <TabsTrigger value="ia">Agente IA</TabsTrigger>
                    <TabsTrigger value="aparencia">Aparência</TabsTrigger>
                </TabsList>

                <TabsContent value="apis" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>URLs das APIs</CardTitle>
                            <CardDescription>
                                Configure as URLs dos serviços backend
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="prinad-url">API PRINAD</Label>
                                <Input
                                    id="prinad-url"
                                    value={prinadApiUrl}
                                    onChange={(e) => setPrinadApiUrl(e.target.value)}
                                    placeholder="http://localhost:8001"
                                />
                            </div>
                            <div>
                                <Label htmlFor="ecl-url">API ECL</Label>
                                <Input
                                    id="ecl-url"
                                    value={eclApiUrl}
                                    onChange={(e) => setEclApiUrl(e.target.value)}
                                    placeholder="http://localhost:8002"
                                />
                            </div>
                            <div>
                                <Label htmlFor="propensao-url">API Propensão</Label>
                                <Input
                                    id="propensao-url"
                                    value={propensaoApiUrl}
                                    onChange={(e) => setPropensaoApiUrl(e.target.value)}
                                    placeholder="http://localhost:8003"
                                />
                            </div>
                            <Button onClick={handleSave}>Salvar</Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="ia" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Configurações do Agente IA</CardTitle>
                            <CardDescription>
                                Configure a integração com OpenRouter
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="openrouter-key">API Key OpenRouter</Label>
                                <Input
                                    id="openrouter-key"
                                    type="password"
                                    value={openrouterApiKey}
                                    onChange={(e) => setOpenrouterApiKey(e.target.value)}
                                    placeholder="sk-or-v1-..."
                                />
                            </div>
                            <div>
                                <Label htmlFor="openrouter-model">Modelo LLM</Label>
                                <Input
                                    id="openrouter-model"
                                    value={openrouterModel}
                                    onChange={(e) => setOpenrouterModel(e.target.value)}
                                    placeholder="moonshotai/kimi-k2:free"
                                />
                            </div>
                            <Button onClick={handleSave}>Salvar</Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="aparencia" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Tema Visual</CardTitle>
                            <CardDescription>
                                Escolha o tema de aparência do sistema
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label>Tema</Label>
                                <Select value={theme} onValueChange={handleThemeChange}>
                                    <SelectTrigger className="w-[200px]">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="system">Sistema (Auto)</SelectItem>
                                        <SelectItem value="light">Claro</SelectItem>
                                        <SelectItem value="dark">Escuro</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
