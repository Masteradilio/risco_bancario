import { Calculator, Info } from 'lucide-react'

export default function ECLCalculoPage() {
    return (
        <div className="space-y-6">
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Calculadora ECL Individual</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="text-sm text-muted-foreground">PD (Probabilidade de Default)</label>
                        <input
                            type="number"
                            placeholder="Ex: 15.5"
                            className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary"
                        />
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">LGD (%)</label>
                        <input
                            type="number"
                            placeholder="Ex: 45"
                            className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary"
                        />
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">EAD (R$)</label>
                        <input
                            type="number"
                            placeholder="Ex: 50000"
                            className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary"
                        />
                    </div>
                </div>
                <button className="mt-4 flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity">
                    <Calculator className="h-4 w-4" />
                    Calcular ECL
                </button>
            </div>

            <div className="chart-container bg-emerald-500/5 border-emerald-500/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-emerald-500 mt-0.5" />
                    <div>
                        <h4 className="font-medium text-emerald-500">Fórmula ECL</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            <strong className="text-foreground">ECL = PD × LGD × EAD</strong>
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                            Onde: PD = Probabilidade de Default, LGD = Loss Given Default, EAD = Exposure at Default
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
