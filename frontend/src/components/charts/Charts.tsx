"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LineChart, Line, CartesianGrid } from 'recharts'

const RATING_COLORS: Record<string, string> = {
    'A1': '#22c55e',
    'A2': '#4ade80',
    'A3': '#86efac',
    'B1': '#eab308',
    'B2': '#facc15',
    'B3': '#fde047',
    'C1': '#f97316',
    'C2': '#fb923c',
    'C3': '#fdba74',
    'D': '#ef4444',
    'DEFAULT': '#1f2937',
}

const STAGE_COLORS: Record<number, string> = {
    1: '#22c55e',
    2: '#f59e0b',
    3: '#ef4444',
}

interface RatingDistributionProps {
    data: Array<{ rating: string; count: number }>
}

export function RatingDistributionChart({ data }: RatingDistributionProps) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="rating" width={60} />
                <Tooltip />
                <Bar dataKey="count" name="Clientes">
                    {data.map((entry) => (
                        <Cell key={entry.rating} fill={RATING_COLORS[entry.rating] || '#6b7280'} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    )
}

interface StageDistributionProps {
    data: Array<{ name: string; value: number; stage: number }>
}

export function StageDistributionChart({ data }: StageDistributionProps) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    nameKey="name"
                    label
                >
                    {data.map((entry) => (
                        <Cell key={entry.name} fill={STAGE_COLORS[entry.stage]} />
                    ))}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    )
}

interface PDTimelineProps {
    data: Array<{ date: string; pd_medio: number; clientes: number }>
}

export function PDTimelineChart({ data }: PDTimelineProps) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="pd_medio" name="PD Médio" stroke="#3b82f6" strokeWidth={2} />
                <Line yAxisId="right" type="monotone" dataKey="clientes" name="Clientes" stroke="#10b981" strokeWidth={2} />
            </LineChart>
        </ResponsiveContainer>
    )
}

interface ECLByGroupProps {
    data: Array<{ grupo: string; ecl: number; clientes: number }>
}

export function ECLByGroupChart({ data }: ECLByGroupProps) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="grupo" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="ecl" name="ECL Total" fill="#3b82f6" />
                <Bar yAxisId="right" dataKey="clientes" name="Clientes" fill="#10b981" />
            </BarChart>
        </ResponsiveContainer>
    )
}

interface PropensaoDistribuicaoProps {
    data: Array<{ acao: string; valor: number; percentual: number }>
}

export function PropensaoDistributionChart({ data }: PropensaoDistribuicaoProps) {
    const ACAO_COLORS: Record<string, string> = {
        'AUMENTAR': '#22c55e',
        'MANTER': '#3b82f6',
        'REDUZIR': '#f59e0b',
        'ZERAR': '#ef4444',
    }

    return (
        <ResponsiveContainer width="100%" height={300}>
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="valor"
                    nameKey="acao"
                    label
                >
                    {data.map((entry) => (
                        <Cell key={entry.acao} fill={ACAO_COLORS[entry.acao] || '#6b7280'} />
                    ))}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    )
}

