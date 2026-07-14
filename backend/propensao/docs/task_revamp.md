# Task legada: REVAMP PROLIMITE e baseline de ECL

> Registro histórico do protótipo com dados sintéticos. Checkboxes indicam implementação declarada à época, não aceite do backlog atual, validação quantitativa ou conformidade regulatória.

## Fase Atual: IMPLEMENTAÇÃO CONCLUÍDA ✅

### Pesquisa ✓
- [x] Ler pesquisa ECL/BACEN 4966
- [x] Ler pesquisa Rating e Limites
- [x] Ler pesquisa Modelo de Propensão
- [x] Criar plano de implementação REVAMP

### Aprovado ✓
- [x] Plano aprovado pelo usuário

---

### Implementação

#### Fase 1: Constantes e Configurações ✅ CONCLUÍDA
- [x] Atualizar `shared/utils.py` com novas constantes (PD, LGD, multiplicadores)
  - PD_POR_RATING: 11 ratings calibrados (A1 → DEFAULT)
  - CCF_POR_PRODUTO: 10 produtos com Credit Conversion Factor
  - PARAMS_LIMITE_GLOBAL: Grupos A/B/C para cálculo de limite
  - CRITERIOS_STAGE: Critérios de migração IFRS 9
  - CRITERIOS_CURA: Critérios de reversão de stage
  - PROPENSITY_ENSEMBLE_CONFIG: Configuração do modelo de propensão
- [x] Adicionar funções auxiliares:
  - get_rating_from_prinad()
  - calcular_pd_por_rating()
  - calcular_ead()
  - calcular_limite_global_fixo()
  - get_stage_from_criteria()
  - calcular_ecl_por_stage()

#### Fase 2: Data Consolidator ✅ CONCLUÍDA
- [x] Refatorar `data_consolidator.py` para gerar campos ECL e propensão
- [x] Novo método `generate_ecl_propensity_data`:
  - PRINAD_SCORE e RATING (heurístico)
  - pd_12m, pd_lifetime (calibrado por rating)
  - stage (IFRS 9: 1, 2, 3)
  - lgd (por produto + ajuste Stage 3)
  - ead (com CCF)
  - ecl (PD × LGD × EAD por stage)
  - propensao_score e propensao_classificacao
  - limite_global (calculado por renda)

#### Fase 3: Stage Classifier (NOVO) ✅ CONCLUÍDA
- [x] Criar `stage_classifier.py` com lógica de 3 stages
- [x] Implementar critérios de migração (Stage 1→2→3)
- [x] Implementar critérios de cura (reversão)
- [x] Implementar regra do arrasto (drag effect)
- [x] Testes passando (todos os cenários validados)

#### Fase 4: ECL Engine ✅ CONCLUÍDA
- [x] Refatorar `ecl_engine.py` para 3 stages (BACEN 4966)
- [x] ECL_12m para Stage 1 (usa pd_12m)
- [x] ECL_lifetime para Stage 2 (usa pd_lifetime)
- [x] Heurística legada de Stage 3 (LGD × 1,5), hoje considerada incorreta e substituída no estado-alvo por cash shortfall descontado
- [x] Cálculo de EAD com CCF
- [x] Integração com StageClassifier
- [x] 27 testes passando

#### Fase 5: Propensity Model
- [x] Modelo de propensão com heurísticas avançadas (integrado no data_consolidator)
- [ ] *(Opcional futuro)* Criar `propensity_model.py` com LightGBM ensemble
- [ ] *(Opcional futuro)* Implementar SMOTEENN para balanceamento

#### Fase 6: Limit Reallocation (NOVO) ✅ CONCLUÍDA
- [x] Criar `limit_reallocation.py`
- [x] Calcular limite global (renda × parâmetros Price)
- [x] Limites por produto respeitando grupos A/B/C
- [x] Realocação por propensão (reduzir baixa, aumentar alta)
- [x] Respeitar comprometimento 70%
- [x] Testes passando

#### Fase 7: Pipeline Runner ✅ CONCLUÍDA
- [x] Integrar ECL Engine v2.0 no pipeline
- [x] Integrar Stage Classifier no pipeline
- [x] Integrar Limit Reallocation no pipeline
- [x] Novo `LimitReallocationEnricher` para realocação por propensão
- [x] Relatório de conformidade BACEN 4966 (`_log_summary_report`)
- [x] Fluxo completo: PRINAD → Stage → ECL → Propensão → Realocação → Ação

#### Fase 8: Validação e Documentação ✅ CONCLUÍDA
- [x] 137 testes passando
- [x] CHANGELOG.md atualizado (v2.0.0)
- [x] task_revamp.md atualizado

---

## Resumo do Progresso

| Fase | Status | Descrição |
|------|--------|-----------|
| 1 | ✅ | Constantes BACEN 4966 |
| 2 | ✅ | Data Consolidator |
| 3 | ✅ | Stage Classifier |
| 4 | ✅ | ECL Engine v2.0 |
| 5 | 🔶 | Propensity Model (heurísticas OK, ML opcional) |
| 6 | ✅ | Limit Reallocation |
| 7 | ✅ | Pipeline Runner |
| 8 | ✅ | Validação |

**Progresso: 100% concluído**

## Arquivos Criados/Modificados

### Novos
- `propensao/src/stage_classifier.py` - Classificação IFRS 9 (3 stages + arrasto + cura)
- `propensao/src/limit_reallocation.py` - Realocação de limites por propensão

### Modificados
- `shared/utils.py` - +262 linhas com constantes e funções BACEN 4966
- `propensao/src/ecl_engine.py` - Reescrito para conformidade 4966
- `propensao/src/data_consolidator.py` - Novo método generate_ecl_propensity_data
- `propensao/src/pipeline_runner.py` - Integração completa v2.0
- `propensao/tests/test_ecl_engine.py` - Novos testes para v2.0
- `propensao/CHANGELOG.md` - Nova versão 2.0.0

## Pipeline Flow (v2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    PROLIMITE Pipeline v2.0                   │
│       (protótipo demonstrativo; conformidade não avaliada)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Load Base                                           │
│   - base_clientes.csv (already enriched by data_consolidator)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: PRINAD Enrichment                                   │
│   - Score 0-100 (heurístico ou modelo)                      │
│   - Rating A1-DEFAULT                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Propensity Enrichment                               │
│   - propensao_score 0-100                                   │
│   - propensao_classificacao ALTA/MEDIA/BAIXA                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: ECL Calculation (BACEN 4966)                        │
│   - pd_12m, pd_lifetime (calibrado)                         │
│   - stage (1, 2, 3)                                         │
│   - lgd (por produto, ajustado Stage 3)                     │
│   - ead (com CCF)                                           │
│   - ecl = PD × LGD × EAD                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Limit Reallocation                                  │
│   - limite_global (por renda)                               │
│   - limite_realocado (por propensão)                        │
│   - variacao_propensao (+/- limite)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Limit Actions                                       │
│   - ZERAR (PRINAD >= 95)                                    │
│   - REDUZIR (PRINAD 75-94 ou baixa propensão)               │
│   - AUMENTAR (PRINAD < 75 + propensão + margem)             │
│   - MANTER (demais)                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Summary Report                                      │
│   - BACEN 4966 Compliance Report                            │
│   - Stage/Rating/Propensity Distribution                    │
│   - ECL Coverage                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Output: base_clientes_processada.csv                        │
│         notificacoes/notif_d0.csv, d30.csv, d60.csv         │
└─────────────────────────────────────────────────────────────┘
```

## Próximos Passos (Opcionais)

1. **ML Propensity Model**: Treinar LightGBM + XGBoost + RF com SMOTEENN
2. **Backtesting**: Validar ECL contra dados históricos reais
3. **Monitoramento**: Dashboard de acompanhamento de stages em produção
4. **Stress Testing**: Cenários de stress para ECL (recession, downturn)
