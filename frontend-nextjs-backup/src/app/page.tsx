import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartPie, Calculator, TrendingUp, Bot } from "lucide-react"
import Link from "next/link"

const modules = [
  {
    title: "PRINAD",
    description: "Probabilidade de Inadimplência - Classificação de risco de crédito",
    icon: ChartPie,
    href: "/prinad",
    color: "text-blue-500",
    stats: "97% Precisão"
  },
  {
    title: "ECL",
    description: "Perda Esperada - Cálculo de Expected Credit Loss conforme BACEN 4966",
    icon: Calculator,
    href: "/ecl",
    color: "text-green-500",
    stats: "IFRS 9"
  },
  {
    title: "Propensão",
    description: "Otimização de Limites - Score de propensão e recomendações",
    icon: TrendingUp,
    href: "/propensao",
    color: "text-purple-500",
    stats: "+17.9% Impacto"
  },
  {
    title: "Assistente IA",
    description: "Agente inteligente para análises e consultas em linguagem natural",
    icon: Bot,
    href: "/ai",
    color: "text-orange-500",
    stats: "LangGraph + RAG"
  },
]

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Sistema de Risco Bancário</h1>
        <p className="text-muted-foreground mt-2">
          Gestão integrada de risco de crédito conforme BACEN 4966 / IFRS 9
        </p>
      </div>

      {/* Modules Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {modules.map((module) => (
          <Link key={module.title} href={module.href}>
            <Card className="hover:border-primary transition-colors cursor-pointer h-full">
              <CardHeader className="flex flex-row items-center gap-4">
                <div className={`p-3 rounded-lg bg-muted ${module.color}`}>
                  <module.icon className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <CardTitle className="flex items-center justify-between">
                    {module.title}
                    <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-1 rounded">
                      {module.stats}
                    </span>
                  </CardTitle>
                  <CardDescription>{module.description}</CardDescription>
                </div>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {/* Quick Info */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xl font-bold">Operacional</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Versão
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xl font-bold">2.0.0</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Conformidade
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xl font-bold">BACEN 4966</span>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
