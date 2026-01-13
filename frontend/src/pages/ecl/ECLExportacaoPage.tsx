import { FileOutput, Download, CheckCircle, AlertCircle, Clock, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const envios = [
    { codigo: 'DOC3040-2026-01', dataBase: '2025-12-31', dataEnvio: '2026-01-08', status: 'ACEITO', protocolo: 'BCB-2026-00123' },
    { codigo: 'DOC3040-2025-12', dataBase: '2025-11-30', dataEnvio: '2025-12-10', status: 'ACEITO', protocolo: 'BCB-2025-01234' },
    { codigo: 'DOC3040-2025-11', dataBase: '2025-10-31', dataEnvio: '2025-11-08', status: 'ACEITO', protocolo: 'BCB-2025-01100' },
]

export default function ECLExportacaoPage() {
    return (
        <div className="space-y-6">
            {/* Gerador */}
            <div className="chart-container">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="font-semibold">Gerar Doc3040</h3>
                        <p className="text-sm text-muted-foreground">Exportação conforme Resolução CMN 4966/2021</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <label className="text-sm text-muted-foreground">Data Base</label>
                        <input
                            type="date"
                            className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                            defaultValue="2025-12-31"
                        />
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Tipo</label>
                        <select className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border">
                            <option>Mensal</option>
                            <option>Trimestral</option>
                        </select>
                    </div>
                    <div className="flex items-end">
                        <button className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity">
                            <Download className="h-4 w-4" />
                            Gerar XML
                        </button>
                    </div>
                </div>

                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-center gap-2 text-amber-500 text-sm">
                        <Clock className="h-4 w-4" />
                        <span>⚠️ Execute o Pipeline ECL antes de gerar o arquivo BACEN</span>
                    </div>
                </div>
            </div>

            {/* Histórico */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Histórico de Envios</h3>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-border">
                            <th className="text-left py-2">Código</th>
                            <th className="text-left py-2">Data Base</th>
                            <th className="text-left py-2">Data Envio</th>
                            <th className="text-left py-2">Status</th>
                            <th className="text-left py-2">Protocolo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {envios.map((e) => (
                            <tr key={e.codigo} className="border-b border-border hover:bg-muted/50">
                                <td className="py-2 font-medium">{e.codigo}</td>
                                <td className="py-2">{e.dataBase}</td>
                                <td className="py-2">{e.dataEnvio}</td>
                                <td className="py-2">
                                    <span className="status-badge status-badge-success">
                                        <CheckCircle className="h-3 w-3" />
                                        {e.status}
                                    </span>
                                </td>
                                <td className="py-2 text-muted-foreground">{e.protocolo}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="chart-container bg-primary/5 border-primary/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                        <h4 className="font-medium text-primary">Leiaute SCR3040 v5.0</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            O arquivo XML segue o leiaute oficial do BACEN, incluindo a tag <code className="px-1 bg-muted rounded">&lt;ContInstFinRes4966&gt;</code>
                            para informações de perda esperada conforme normas contábeis vigentes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
