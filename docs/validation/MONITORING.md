# Monitoramento Operacional e Estatístico de Modelos

Este documento detalha o framework de monitoramento estatístico e operacional implementado no pacote `src/validation/monitoring`. O sistema foi projetado para rastrear a estabilidade e a qualidade dos dados e das previsões ao longo do tempo.

## Funcionalidades de Monitoramento

O monitoramento cobre cinco frentes fundamentais exigidas pelas boas práticas de governança de modelos de risco (MRM):

### 1. Data Quality e Schema Drift
`check_schema_drift` compara o schema de um conjunto de dados de referência com o atual para detectar:
- Colunas faltantes ou adicionadas.
- Incompatibilidades de tipo físico de dados (ex. `int` vs `float`).
- Taxa de valores nulos/ausentes excedendo o limite tolerado (padrão: 5%).

### 2. Estabilidade Populacional (PSI)
`calculate_psi` monitora o drift de distribuições contínuas (ex. probabilidades de inadimplência (PD) ou estimativas de LGD) utilizando o **Population Stability Index (PSI)**.
- **Verde (PSI < 0.10)**: Estabilidade na distribuição.
- **Amarelo (0.10 <= PSI < 0.25)**: Drift moderado. Recomenda-se investigação.
- **Vermelho (PSI >= 0.25)**: Drift significativo. Exige ação/recalibração do modelo.

### 3. Alertas de Desempenho e Calibração
`check_calibration` detecta variações de métricas de acurácia ou poder discriminatório (ex. Gini, AUC) em relação a um baseline de calibração pré-definido, acionando níveis de alerta:
- **Amarelo**: Desvio de >= 5% do baseline.
- **Vermelho**: Desvio de >= 10% do baseline.

### 4. Estabilidade de Estágio (Staging Stability)
`check_staging_stability` monitora a distribuição de ativos nos três estágios da IFRS 9 (Stage 1, Stage 2, Stage 3) em relação a uma proporção histórica de baseline. Desvios acionam alertas caso excedam os limiares de tolerância de volume.

### 5. Desvios Macroecnômicos
`check_scenario_deviation` compara as variáveis macroeconômicas observadas no período corrente com as trajetórias estimadas dos cenários econômicos (Base, Otimista, Pessimista e Stress), acionando alertas se o desvio for superior ao limite de tolerância (padrão: 15%).

---

## Estrutura do Pacote

- **`src/validation/monitoring/models.py`**: Modelos e dataclasses imutáveis para representação de relatórios e alertas de monitoramento.
- **`src/validation/monitoring/metrics.py`**: Funções matemáticas e lógicas para o cálculo dos reportes de estabilidade.
- **`tests/validation/test_monitoring.py`**: Testes unitários para validar todos os cenários de Green, Yellow, Red e validações de input.
