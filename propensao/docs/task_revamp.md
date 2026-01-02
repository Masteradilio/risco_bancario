# Task: REVAMP PROLIMITE - Conformidade ECL + Propensão

## Fase Atual: PLANNING (Aguardando Aprovação)

### Pesquisa ✓
- [x] Ler pesquisa ECL/BACEN 4966
- [x] Ler pesquisa Rating e Limites
- [x] Ler pesquisa Modelo de Propensão
- [x] Criar plano de implementação REVAMP

### Aguardando Aprovação
- [ ] Revisar plano com usuário
- [ ] Confirmar multiplicadores de limite global (20x → 0x)
- [ ] Confirmar PDs por rating
- [ ] Confirmar LGDs por produto/garantia

---

### Implementação (após aprovação)

#### Fase 1: Constantes e Configurações
- [ ] Atualizar `shared/utils.py` com novas constantes (PD, LGD, multiplicadores)

#### Fase 2: Data Consolidator
- [ ] Refatorar `data_consolidator.py` para gerar campos ECL e propensão
- [ ] Adicionar campos: pd_12m, pd_lifetime, lgd, ead, ecl_*, stage
- [ ] Adicionar campos: propensao features (transaction_freq, etc)
- [ ] Adicionar campos: limite_global, comprometimento

#### Fase 3: Stage Classifier (NOVO)
- [ ] Criar `stage_classifier.py` com lógica de 3 stages
- [ ] Implementar critérios de migração (Stage 1→2→3)
- [ ] Implementar critérios de cura (reversão)
- [ ] Implementar regra do arrasto

#### Fase 4: ECL Engine
- [ ] Refatorar `ecl_engine.py` para 3 stages
- [ ] ECL_12m para Stage 1
- [ ] ECL_lifetime para Stage 2
- [ ] ECL com LGD máxima para Stage 3

#### Fase 5: Propensity Model (NOVO)
- [ ] Criar `propensity_model.py` com LightGBM
- [ ] Implementar ensemble (LightGBM + XGBoost + RF)
- [ ] Implementar SMOTEENN para balanceamento
- [ ] Features específicas por produto

#### Fase 6: Limit Reallocation (NOVO)
- [ ] Criar `limit_reallocation.py`
- [ ] Calcular limite global (renda × multiplicador)
- [ ] Realocação por propensão (reduzir baixa, aumentar alta)
- [ ] Respeitar comprometimento 70%

#### Fase 7: Pipeline Runner
- [ ] Integrar todos os módulos no pipeline
- [ ] Fluxo: PRINAD → Stage → ECL → Propensão → Realocação

#### Fase 8: Validação e Documentação
- [ ] Executar pipeline e validar resultados
- [ ] Atualizar documentação
- [ ] Commit e push
