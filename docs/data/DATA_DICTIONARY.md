# Dicionário de dados sintéticos

Datas são datas civis no primeiro dia do mês, salvo datas de evento. Valores
monetários estão em BRL e usam duas casas; taxas e razões usam representação
decimal, exceto variáveis macro em pontos percentuais.

## Entidades e contratos

| Tabela | Campos principais | Definição |
|---|---|---|
| `clients` | `client_id`, `counterparty_id`, `client_type`, `relationship_start_date`, `region` | Cliente sintético PF/PJ sem identificador real. |
| `counterparties` | `counterparty_id`, `party_type`, `economic_group_id`, `inception_date` | Contraparte e vínculo opcional a grupo. |
| `contracts` | `contract_id`, `client_id`, `product_code`, `facility_type`, `origination_date`, `maturity_date` | Instrumento originado. |
| `contracts` | `effective_interest_rate`, `original_amount`, `credit_limit`, `initial_drawn_amount` | Termos financeiros na originação. |
| `contracts` | `acquired_credit_impaired`, `policy_version` | Indicador POCI sintético e política vigente. |
| `collateral` | `collateral_id`, `contract_id`, `collateral_type`, `appraised_value`, `enforceable_share` | Garantia e parcela executável. |
| `schedules` | `installment_number`, `due_date`, `opening_balance`, `principal`, `interest`, `payment`, `closing_balance` | Cronograma contratual. |

## Histórico mensal

| Campo | Definição |
|---|---|
| `reference_date` | Data-base observável. |
| `origination_cohort`, `months_on_book` | Safra mensal e idade do contrato. |
| `balance`, `credit_limit`, `utilization` | Saldo, limite e razão utilizada. |
| `scheduled_payment`, `paid_amount` | Obrigação e pagamento observados no mês. |
| `days_past_due` | Atraso observado em dias. |
| `behavior_score`, `rating` | Sinais comportamentais calculados apenas com estado corrente/passado. |
| `modified` | Existência de modificação na data-base. |

## Eventos de crédito

| Tabela | Campos principais | Definição |
|---|---|---|
| `defaults` | `default_id`, `contract_id`, `default_date`, `exposure_at_default`, `trigger`, `is_redefault` | Default ou redefault posterior ao snapshot. |
| `collections` | `collection_id`, `default_id`, `event_date`, `action` | Ação de cobrança. |
| `recoveries` | `recovery_date`, `source`, `gross_amount`, `cost_amount`, `cost_type`, `net_amount`, `post_writeoff` | Fluxo líquido e seus custos. |
| `cures` | `cure_date`, `observation_months` | Cura após período observacional. |
| `writeoffs` | `writeoff_date`, `amount`, `policy_version` | Baixa reconciliada da exposição remanescente. |

## Macroeconomia

| Campo | Definição |
|---|---|
| `scenario_id`, `regime` | Caminho observado sintético ou cenário e regime. |
| `gdp_growth` | Crescimento anualizado sintético do PIB, em pontos percentuais. |
| `inflation`, `policy_rate`, `unemployment`, `household_debt` | Indicadores sintéticos em pontos percentuais. |
| `risk_pressure` | Função não linear observável de condições adversas. |
| `policy_version` | Versão da trajetória/configuração. |

## Datasets de modelagem

| Dataset/campo | Papel |
|---|---|
| `pd_modeling.target_default_12m` | Label: default em `(t, t+12m]`. |
| `pd_modeling.target_hazard_1m` | Label: default em `(t, t+1m]`. |
| `pd_modeling.origination_cohort` | Safra mensal de originação; metadado de segmentação, não feature automática. |
| `lgd_modeling.target_realized_lgd_undiscounted` | Label: perda líquida realizada, ainda sem desconto EIR. |
| `ead_modeling.target_exposure_at_default` | Label: exposição realizada na data de default. |
| `ead_modeling.target_ccf` | Label: parcela do limite não utilizado convertida, quando aplicável. |
| `sicr_modeling.target_sicr_12m` | Label: deterioração relevante futura conforme definição sintética documentada. |
| `split` | `train`, `validation`, `calibration`, `oot` ou `backtesting`. |

Targets de PD, hazard e SICR são nulos em `backtesting` enquanto a janela futura
não estiver completa. Anos de embargo não são exportados para modelagem.

Identificadores, datas de evento e campos `target_*` são metadados/labels e não
devem entrar automaticamente na matriz de features.
