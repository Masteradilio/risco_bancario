# Registro de Limitações Metodológicas e Amostrais (Limitation Register)

Este documento registra todas as limitações quantitativas, metodológicas e de infraestrutura de dados observadas na validação independente dos modelos de risco de crédito (PD, LGD, EAD/CCF e ECL).

## 1. Limitações de Tamanho Amostral e Cobertura (Volume Limit)

- **Backtesting de PD**: O conjunto de teste fora do tempo (OOT) do ano de 2024 possui apenas 233 observações maduras e 27 eventos de default. Para obter conclusões com relevância estatística, as diretrizes de governança exigem ao menos 100 observações maduras por rating/produto. O ano de 2025 permanece com a classificação contábil imatura, sem desfecho maduro observado.
- **Backtesting de LGD**: O holdout de desenvolvimento possui apenas 10 workouts de default finalizados nos anos de 2022-2023. O requisito mínimo de estabilidade estatística é de 100 workouts concluídos. Adicionalmente, 7 workouts encontram-se censurados (abertos) e não fornecem base para estimativa final de LGD.
- **Backtesting de CCF (EAD Rotativo)**: Há somente 4 defaults em produtos com limite não utilizado no conjunto de teste OOT, inviabilizando qualquer teste estatístico robusto ou comparação de MAE/RMSE.
- **Off-Balance (Compromissos e Garantias)**: O gerador de dados sintéticos atual não produz defaults ou utilização de limites de crédito para compromissos e garantias financeiras. A exposição nesses produtos foi modelada de forma puramente paramétrica baseada na política versionada, sem suporte empírico.

## 2. Limitações Metodológicas e de Calibração

- **Colapso de Calibração da PD**: O calibrador *Isotonic Regression* treinado na base de calibração colapsou para uma probabilidade constante de 29,41% no conjunto OOT de 2024. Isso resultou em erro absoluto médio de calibração elevado (17,82 p.p.), levando à rejeição objetiva do modelo Champion.
- **Uso Não Independente do Holdout de LGD**: O conjunto de validação temporal (holdout) de 2022-2023 foi consumido na fase de desenvolvimento para a seleção de algoritmos (comparação Ridge vs Two-Stage vs One-Inflated), violando o princípio de blindagem do teste independente.
- **Falta de Série Histórica de ECL**: Não há armazenamento de snapshots históricos de cálculo de ECL concomitante com desfechos reais de perdas por contrato em base longitudinal consolidada, impossibilitando a execução de backtesting quantitativo de ECL com dados maduros.

## 3. Classificação de Status dos Componentes

| Componente | Validação | Status Validação | Causa Principal |
|---|---|---|---|
| **PD 12m/Lifetime** | Estatística / OOT | **REJECTED** | Colapso de calibração no OOT e erro de calibragem elevado. |
| **LGD** | Estatística / Holdout | **REJECTED** | Amostra reduzida (10 workouts) e uso inadequado do holdout. |
| **EAD Amortizado** | Reconciliação | **PASSED** | Identidade metodológica da amortização linear. |
| **EAD Rotativo (CCF)** | Estatística / OOT | **REJECTED** | Amostra reduzida (4 observações) e MAE relativo de 40.36%. |
| **ECL** | Reconciliação | **REJECTED** | Falta de snapshots históricos longitudinais. |

---

## 4. Recomendações e Plano de Ação

1. **Ajuste do Gerador de Dados**: Expandir a fábrica de dados sintéticos para aumentar a taxa de inadimplência em contratos não-POCI e gerar histórico longitudinal amplo de snapshots mensais de ECL.
2. **Re-modelagem e Tuning**: Implementar algoritmos alternativos de calibração (Platt Scaling ou Beta Calibration) para contornar a rigidez da regressão isotônica em amostras de dados esparsos.
3. **Ampliação do Período OOT**: Coletar dados reais ou sintéticos adicionais para amadurecer os defaults de 2025 e obter um holdout com amostragem adequada (N >= 500).
