# REVAMP: Sistema PROLIMITE - Conformidade ECL + Propensão Otimizada

## 1. Síntese das Pesquisas

### ECL / Resolução 4966
- **Fórmula Central**: `ECL = PD × LGD × EAD`
- **3 Estágios**: Stage 1 (12m ECL), Stage 2 (Lifetime ECL), Stage 3 (Default - LGD máxima)
- **RAROC**: Risk-Adjusted Return On Capital → operação só é aprovada se RAROC > mínimo
- **Capital Alocado**: ECL × Fator Conservador (1.5-2.0)
- **Arrasto**: Se um produto vai para Stage 3, TODOS produtos do cliente migram

### Ratings e Limites
- **Rating afeta AMBOS**: limite E taxa (não apenas taxa)
- **DTI ideal**: ≤36%, aceitável ≤43%, alto risco >50%
- **Brasil não tem LTI regulatório** → cada banco define internamente
- **Multiplicadores por Rating**: baseado no apetite de risco

### Propensão
- **LightGBM + XGBoost + Random Forest** (ensemble)
- **SMOTEENN** para balanceamento de dados
- **Objetivo**: prever uso de produto → alocar limite onde há propensão
- **ECL Otimizado**: reduzir EAD de produtos sem propensão → liberar capital

---

## 2. Mudanças no Módulo PRINAD (PD)

### 2.1 Metodologia Atual vs. Nova

| Aspecto | Atual | Novo (BACEN 4966) |
|---------|-------|-------------------|
| Horizonte PD | Não especificado | **12 meses** (Stage 1) + **Lifetime** (Stage 2/3) |
| Mínimo PD | 0.5% | **0.03%** (floor BACEN) |
| Ratings | 11 níveis (A1→DEFAULT) | ✓ Manter, ajustar PD por faixa |
| Histórico | 24 meses | **36-60 meses** (capturar ciclos) |

### 2.2 PDs por Rating (Nova Tabela Calibrada)

```python
PD_POR_RATING = {
    # Rating: (PD_12m_min, PD_12m_max, PD_lifetime_multiplier)
    'A1': (0.03, 0.50, 2.5),    # 0-4.99% PRINAD
    'A2': (0.50, 1.00, 2.5),    # 5-14.99%
    'A3': (1.00, 2.00, 3.0),    # 15-24.99%
    'B1': (2.00, 3.50, 3.5),    # 25-34.99%
    'B2': (3.50, 5.00, 4.0),    # 35-44.99%
    'B3': (5.00, 7.00, 4.5),    # 45-54.99%
    'C1': (7.00, 10.0, 5.0),    # 55-64.99%
    'C2': (10.0, 15.0, 5.5),    # 65-74.99%
    'C3': (15.0, 25.0, 6.0),    # 75-84.99%
    'D':  (25.0, 50.0, 6.5),    # 85-94.99%
    'DEFAULT': (50.0, 100, 7.0) # 95-100%
}

# Exemplo: Rating B2, PRINAD = 40%
# PD_12m = 3.5% + (40-35)/(45-35) × (5-3.5) = 4.25%
# PD_lifetime = 4.25% × 4.0 = 17%
```

---

## 3. Mudanças no LGD

### 3.1 LGD por Tipo de Garantia (BACEN)

```python
LGD_POR_GARANTIA = {
    # tipo: (LGD_base, LGD_downturn_mult)
    'consignacao': (0.25, 1.25),      # Desconto em folha
    'imovel_residencial': (0.15, 1.30),
    'imovel_comercial': (0.20, 1.35),
    'veiculo': (0.35, 1.40),
    'equipamento': (0.40, 1.45),
    'recebivel': (0.45, 1.30),
    'nenhuma': (0.60, 1.50),          # Sem garantia = maior perda
}

# LGD mínimos regulatórios (BACEN):
# - PF sem colateral: 35%
# - PF com imóvel: 15%
```

### 3.2 LGD por Produto (Default do Sistema)

```python
LGD_POR_PRODUTO = {
    'consignado': 0.25,           # Garantia: consignação
    'imobiliario': 0.15,          # Garantia: imóvel
    'cred_veiculo': 0.35,         # Garantia: veículo
    'energia_solar': 0.35,        # Garantia: equipamento
    'banparacard': 0.55,          # Sem garantia
    'cartao_credito': 0.70,       # Sem garantia, rotativo
    'cheque_especial': 0.65,      # Sem garantia
    'credito_sazonal': 0.30,      # Consignação em 13º/IR
    'pessoal': 0.60,              # Sem garantia
}
```

---

## 4. Mudanças no EAD

### 4.1 EAD = Exposição no Default

```python
def calcular_ead(produto, limite_total, saldo_utilizado, ccf=None):
    """
    EAD = saldo_utilizado + (limite_disponivel × CCF)
    
    CCF (Credit Conversion Factor):
    - Empréstimo amortizado: 100% (já sacou tudo)
    - Linha rotativa: 50-75% (pode sacar mais até default)
    - Pré-aprovado não usado: 30-50%
    """
    limite_disponivel = limite_total - saldo_utilizado
    
    CCF_PADRAO = {
        'consignado': 1.00,       # Amortizado
        'imobiliario': 1.00,
        'cred_veiculo': 1.00,
        'pessoal': 1.00,
        'cartao_credito': 0.75,   # Rotativo
        'banparacard': 0.75,
        'cheque_especial': 0.70,
        'credito_sazonal': 0.50,
        'energia_solar': 1.00,
    }
    
    ccf = ccf or CCF_PADRAO.get(produto, 0.75)
    return saldo_utilizado + (limite_disponivel * ccf)
```

---

## 5. Modelo de 3 Estágios (Stages)

### 5.1 Critérios de Migração

```python
CRITERIOS_STAGE = {
    'STAGE_1': {
        'descricao': 'Risco Normal',
        'ecl_horizonte': '12_meses',
        'condicoes': [
            'dias_atraso <= 30',
            'rating_estavel_ou_melhorando',
            'sem_eventos_negativos_recentes'
        ]
    },
    'STAGE_2': {
        'descricao': 'Aumento Significativo de Risco',
        'ecl_horizonte': 'lifetime',
        'gatilhos': [
            'dias_atraso >= 31 AND dias_atraso <= 90',
            'downgrade >= 2 notches',
            'reducao_renda >= 30%',
            'aumento_dti >= 20pp',
            'score_externo caiu >= 100 pontos'
        ]
    },
    'STAGE_3': {
        'descricao': 'Default/Impairment',
        'ecl_horizonte': 'lifetime_max_lgd',
        'gatilhos': [
            'dias_atraso > 90',
            'evento_judicial',
            'insolvencia_declarada',
            'falha_renegociacao'
        ],
        'arrasto': True  # Todos produtos do cliente migram!
    }
}
```

### 5.2 Critérios de Cura (Reversão)

```python
CRITERIOS_CURA = {
    'STAGE_2_para_1': {
        'periodo_observacao': 6,  # meses
        'condicoes': [
            'adimplente_por_6_meses_consecutivos',
            'rating_estabilizado_ou_melhorado',
            'sem_novos_atrasos'
        ]
    },
    'STAGE_3_para_2': {
        'periodo_observacao': 12,  # meses
        'condicoes': [
            'debito_totalmente_quitado',
            'adimplente_por_12_meses',
            'rating >= C2'
        ]
    }
}
```

---

## 6. Limite Global Dinâmico e Limites por Produto

### 6.1 CONCEITOS FUNDAMENTAIS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LIMITE GLOBAL (FIXO)                             │
│                                                                          │
│  É calculado SEMPRE pelo MÁXIMO TEÓRICO de crédito possível:            │
│  - 35% consignado × 180 meses × taxa consignado                         │
│  - 30% imobiliário × 420 meses × taxa imobiliário                       │
│  - 5% bens × 60 meses × taxa veículo/solar                              │
│                                                                          │
│  SÓ MUDA QUANDO A RENDA BRUTA MUDA (não é afetado por propensão)        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPROMETIMENTO (FLEXÍVEL - 70%)                      │
│                                                                          │
│  Dentro dos 70%, o cliente pode alocar como quiser, respeitando:        │
│                                                                          │
│  LIMITES MÁXIMOS POR PRODUTO:                                           │
│  ├─ Consignado: 35% (limite LEGAL, não pode ultrapassar)                │
│  ├─ Banparacard: 35% (pode receber de outros grupos)                    │
│  ├─ Pessoal: 35%                                                        │
│  ├─ Imobiliário: 30%                                                    │
│  ├─ Veículo: 35% (ATUALIZADO)                                           │
│  └─ Energia Solar: 25%                                                  │
│                                                                          │
│  SOMA TOTAL ≤ 70%                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Exemplos de Alocação Válida

```
EXEMPLO 1: Cliente quer maximizar Veículo + Banparacard
├─ Veículo: 35%
├─ Banparacard: 35%
├─ TOTAL: 70% ✓
└─ Consignado, Imobiliário, Solar: 0%

EXEMPLO 2: Cliente quer Consignado + Imobiliário
├─ Consignado: 35%
├─ Imobiliário: 30%
├─ Veículo: 5%
├─ TOTAL: 70% ✓
└─ Banparacard, Solar: 0%

EXEMPLO 3: Cliente quer só Imobiliário
├─ Imobiliário: 30%
├─ TOTAL: 30% (usa menos que o máximo)
└─ Limite Global ainda é calculado pelo máximo
```

### 6.3 Fórmula do Limite Global (FIXO)

```python
def calcular_limite_global_fixo(renda_bruta: float) -> dict:
    """
    Calcula o limite global SEMPRE pelo máximo teórico.
    NÃO é afetado por propensão - só muda quando renda muda.
    
    Fórmula:
    - Grupo A (35%): parcela 35% × prazo 180m × taxa consignado
    - Grupo B (30%): parcela 30% × prazo 420m × taxa imobiliário
    - Grupo C (5%): parcela 5% × prazo 60m × taxa veículo
    """
    
    # Parâmetros fixos para cálculo do limite global
    PARAMS_LIMITE_GLOBAL = {
        'grupo_a': {'pct': 0.35, 'prazo': 180, 'taxa': 0.018},   # Consignado
        'grupo_b': {'pct': 0.30, 'prazo': 420, 'taxa': 0.0085},  # Imobiliário  
        'grupo_c': {'pct': 0.05, 'prazo': 60, 'taxa': 0.018},    # Veículo
    }
    
    limite_global = 0
    detalhes = {}
    
    for grupo, params in PARAMS_LIMITE_GLOBAL.items():
        parcela = renda_bruta * params['pct']
        taxa = params['taxa']
        prazo = params['prazo']
        
        # Fórmula Price: PV = PMT × [(1 - (1 + i)^-n) / i]
        fator = (1 - (1 + taxa) ** -prazo) / taxa
        limite = parcela * fator
        
        detalhes[grupo] = {
            'parcela': parcela,
            'prazo': prazo,
            'limite': limite,
        }
        limite_global += limite
    
    return {
        'limite_global': limite_global,
        'detalhes': detalhes,
        'renda_bruta': renda_bruta,
        'so_muda_com_renda': True,  # Indicador importante!
    }

# Exemplo: Renda R$ 10.000
# Grupo A: R$ 3.500 × 52.98 = R$ 185.430
# Grupo B: R$ 3.000 × 110.89 = R$ 332.670
# Grupo C: R$ 500 × 44.95 = R$ 22.475
# LIMITE GLOBAL FIXO = R$ 540.575
```

### 6.4 Limites Individuais por Produto (Flexíveis dentro dos 70%)

```python
# Máximo que cada produto pode comprometer da renda
# Cliente pode usar até esse máximo, respeitando soma ≤ 70%
MAX_COMPROMETIMENTO_PRODUTO = {
    'consignado':     0.35,  # LEGAL - não pode ultrapassar
    'banparacard':    0.35,  # Pode receber de outros grupos
    'pessoal':        0.35,  # Pode receber de outros grupos
    'imobiliario':    0.30,  # Máximo do produto
    'cred_veiculo':   0.35,  # ATUALIZADO: era 20%, agora 35%
    'energia_solar':  0.25,  # Máximo do produto
}

# Parâmetros para cálculo do limite por produto
PARAMETROS_PRODUTO = {
    # produto: (prazo_max_meses, taxa_juros_mensal)
    'consignado':     (180, 0.0180),   # 180m, 1.80% a.m.
    'banparacard':    (84,  0.0250),   # 84m, 2.50% a.m.
    'pessoal':        (60,  0.0350),   # 60m, 3.50% a.m.
    'imobiliario':    (420, 0.0085),   # 420m, 0.85% a.m.
    'cred_veiculo':   (60,  0.0180),   # 60m, 1.80% a.m.
    'energia_solar':  (84,  0.0150),   # 84m, 1.50% a.m.
}

PRODUTOS_FORA_LIMITE_GLOBAL = {
    'limite_rotativo': {
        'limite_total': 'renda_bruta',  # 100% da renda
        'produtos_concorrentes': ['cartao_credito', 'cheque_especial'],
        'descricao': 'Cliente decide proporção entre cartão e cheque',
    },
    'credito_sazonal': {
        'limite': '0.80 * max(decimo_terceiro, restituicao_ir)',
        'descricao': '80% do 13º ou IR',
    },
}
```

### 6.3 Parâmetros por Produto para Cálculo de Limite

```python
PARAMETROS_PRODUTO = {
    # produto: (prazo_max_meses, taxa_juros_mensal, grupo)
    'consignado':     (180, 0.0180, 'GRUPO_A'),   # 180m, 1.80% a.m.
    'banparacard':    (84,  0.0250, 'GRUPO_A'),   # 84m, 2.50% a.m.
    'pessoal':        (60,  0.0350, 'GRUPO_A'),   # 60m, 3.50% a.m.
    'imobiliario':    (420, 0.0085, 'GRUPO_B'),   # 420m, 0.85% a.m. (TR+8.5%)
    'cred_veiculo':   (60,  0.0180, 'GRUPO_C'),   # 60m, 1.80% a.m.
    'energia_solar':  (84,  0.0150, 'GRUPO_C'),   # 84m, 1.50% a.m.
}
```

### 6.4 Fórmula de Cálculo do Limite por Produto

```python
def calcular_limite_produto(renda_bruta: float, produto: str, 
                            comprometimento_disponivel: float) -> dict:
    """
    Calcula o limite máximo de crédito para um produto
    baseado na parcela máxima e taxa de juros.
    
    Fórmula Price (Tabela SAC simplificada):
    PV = PMT × [(1 - (1 + i)^-n) / i]
    
    Onde:
    - PV = Valor Presente (Limite)
    - PMT = Parcela Máxima (renda × % comprometimento)
    - i = Taxa de juros mensal
    - n = Prazo em meses
    """
    prazo, taxa, grupo = PARAMETROS_PRODUTO[produto]
    
    # Parcela máxima possível
    parcela_max = renda_bruta * comprometimento_disponivel
    
    # Fórmula Price inversa: PV dado PMT
    if taxa > 0:
        fator = (1 - (1 + taxa) ** -prazo) / taxa
        limite_principal = parcela_max * fator
    else:
        limite_principal = parcela_max * prazo
    
    return {
        'produto': produto,
        'parcela_max': parcela_max,
        'prazo_meses': prazo,
        'taxa_mensal': taxa,
        'limite_principal': limite_principal,
        'grupo': grupo,
    }
```

### 6.5 Algoritmo de Cálculo do Limite Global Dinâmico

```python
def calcular_limite_global_dinamico(cliente: dict) -> dict:
    """
    Calcula o limite global e por produto baseado na renda,
    respeitando os grupos e o máximo de 70% de comprometimento.
    """
    renda = cliente['renda_bruta']
    comprometimento_atual = cliente.get('comprometimento_atual', 0)
    
    # Espaço disponível no limite global (70% - já comprometido)
    espaco_global = max(0, 0.70 - comprometimento_atual)
    
    resultado = {
        'renda_bruta': renda,
        'comprometimento_atual': comprometimento_atual,
        'espaco_disponivel': espaco_global,
        'limites_grupos': {},
        'limites_produtos': {},
        'limite_global_total': 0,
    }
    
    # Calcular limite máximo por grupo
    for grupo_id, grupo_config in GRUPOS_LIMITE.items():
        max_grupo = grupo_config['max_comprometimento']
        
        # O grupo não pode exceder seu máximo NEM o espaço global restante
        comprometimento_grupo = min(max_grupo, espaco_global)
        
        limites_grupo = []
        for produto in grupo_config['produtos']:
            limite_produto = calcular_limite_produto(
                renda, produto, comprometimento_grupo
            )
            limites_grupo.append(limite_produto)
            resultado['limites_produtos'][produto] = limite_produto
        
        resultado['limites_grupos'][grupo_id] = {
            'max_comprometimento': comprometimento_grupo,
            'parcela_max': renda * comprometimento_grupo,
            'produtos': limites_grupo,
        }
        
        # Reduzir espaço global pelo grupo (para próximos grupos)
        # Na prática, todos competem, então mantemos espaço até 70% total
    
    # Limite global = soma dos limites máximos de todos grupos
    # Mas respeitando que soma dos comprometimentos ≤ 70%
    limite_global = 0
    for grupo in resultado['limites_grupos'].values():
        # Pegar o maior limite do grupo (produto mais longo/barato)
        maior_limite = max(p['limite_principal'] for p in grupo['produtos'])
        limite_global += maior_limite
    
    resultado['limite_global_total'] = limite_global
    
    # Produtos fora do limite global
    resultado['limites_fora_global'] = {
        'cartao_credito': renda,  # 100% da renda
        'credito_sazonal': renda * 0.80,  # 80% do 13º (simplificado)
        'cheque_especial': renda * 0.50,  # 50% da renda
    }
    
    return resultado
```

### 6.6 Exemplos de Cálculo (COM PRIORIZAÇÃO A → B → C)

#### Exemplo 1: Cliente com Renda R$ 10.000 (sem comprometimento)

```
Renda Bruta: R$ 10.000
Comprometimento Atual: 0%

CÁLCULO COM PRIORIZAÇÃO:
├─ GRUPO A (Prioridade 1): 35% disponível
├─ GRUPO B (Prioridade 2): 30% disponível  
└─ GRUPO C (Prioridade 3): 70% - 35% - 30% = 5% disponível

GRUPO A (35% = R$ 3.500/mês):
└─ Consignado: R$ 3.500 × [(1-(1.018)^-180)/0.018] = R$ 185.430

GRUPO B (30% = R$ 3.000/mês):
└─ Imobiliário: R$ 3.000 × [(1-(1.0085)^-420)/0.0085] = R$ 332.670

GRUPO C (5% = R$ 500/mês):
└─ Solar: R$ 500 × [(1-(1.015)^-84)/0.015] = R$ 26.070

═══════════════════════════════════════════════════════════════
LIMITE GLOBAL = R$ 185.430 + R$ 332.670 + R$ 26.070 = R$ 544.170
═══════════════════════════════════════════════════════════════

FORA DO LIMITE GLOBAL:
├─ Limite Rotativo (Cartão + Cheque): R$ 10.000 (100% renda)
│   Cliente decide proporção: 70% cartão / 30% cheque, etc.
└─ Crédito Sazonal: R$ 8.000 (80% do 13º)
```

#### Exemplo 2: Cliente já comprometido (Veículo R$ 4.000 + Imóvel R$ 6.000)

```
Renda Bruta: R$ 20.000
Comprometimento Atual: 50% (R$ 10.000/mês)
├─ Grupo C usado: 20% (Veículo R$ 4.000)
└─ Grupo B usado: 30% (Imóvel R$ 6.000)

Espaço Disponível: 70% - 50% = 20%

GRUPO A (Prioridade 1): 20% disponível (do limite de 35%)
└─ Consignado: R$ 4.000 × 52.98 = R$ 211.920

GRUPO B: JÁ TOTALMENTE USADO (30%)
GRUPO C: JÁ TOTALMENTE USADO (20%)

LIMITE ADICIONAL DISPONÍVEL: R$ 211.920

FORA DO LIMITE GLOBAL (não afetados):
├─ Limite Rotativo: R$ 20.000 (cliente aloca como quiser)
└─ Crédito Sazonal: R$ 16.000
```

### 6.7 Realocação Dinâmica ENTRE Grupos por Propensão

```python
def realocar_entre_grupos_por_propensao(cliente: dict, propensoes: dict) -> dict:
    """
    Realoca limite ENTRE GRUPOS baseado em propensão.
    
    REGRAS:
    1. O CONSIGNADO mantém seu limite de 35% FIXO (limite legal)
    2. Se propensão_imobiliario < 40%, pode transferir para:
       - Grupo A (pessoal/banparacard, NÃO consignado)
       - Grupo C (veículo/solar)
    3. Se propensão_veiculo/solar < 40%, pode transferir para:
       - Grupo A (pessoal/banparacard, NÃO consignado)
    4. Limite global de 70% permanece fixo
    """
    
    # Limites que NÃO podem ser realocados
    LIMITES_FIXOS = {
        'consignado': 0.35,  # Limite legal, não muda
    }
    
    # Limites que PODEM ser realocados
    LIMITES_REALOCAVEIS = {
        'imobiliario': 0.30,     # Pode ir para A ou C
        'cred_veiculo': 0.10,    # Parte do 20% do Grupo C
        'energia_solar': 0.10,   # Parte do 20% do Grupo C
        'banparacard': 0.175,    # Parte do 35% sem consignado
        'pessoal': 0.175,        # Parte do 35% sem consignado
    }
    
    espaco_liberado = 0
    
    # Verificar produtos de baixa propensão
    for produto, limite_max in LIMITES_REALOCAVEIS.items():
        propensao = propensoes.get(produto, 50)
        
        if propensao < 40:  # Baixa propensão
            # Liberar parte desse limite
            liberacao = limite_max * 0.50  # Libera até 50%
            espaco_liberado += liberacao
    
    # Alocar espaço liberado para produtos de alta propensão
    for produto, limite_atual in cliente['limites_produtos'].items():
        if produto in LIMITES_FIXOS:
            continue  # Não altera consignado
            
        propensao = propensoes.get(produto, 50)
        
        if propensao > 60 and espaco_liberado > 0:  # Alta propensão
            # Aumentar limite deste produto
            aumento = min(espaco_liberado, limite_atual * 0.30)
            cliente['limites_produtos'][produto] += aumento
            espaco_liberado -= aumento
    
    return cliente
```

### 6.8 Exemplo de Realocação por Propensão

```
Cliente com Renda R$ 10.000

PROPENSÕES:
├─ Consignado: 80% (ALTA)
├─ Imobiliário: 20% (BAIXA) ← Liberar
├─ Veículo: 70% (ALTA)
└─ Solar: 15% (BAIXA) ← Liberar

ANTES (sem realocação):
├─ Grupo A: 35% (R$ 185k consignado)
├─ Grupo B: 30% (R$ 332k imobiliário)
└─ Grupo C: 5% (R$ 26k solar)
├─ TOTAL: 70%

DEPOIS (com realocação):
├─ Consignado: 35% MANTIDO (limite legal)
├─ Imobiliário: 30% → 15% REDUZIDO (baixa propensão)
│   Liberou 15% para outros
├─ Veículo: 5% → 20% AUMENTADO (alta propensão)
│   Recebeu 15% do imobiliário
├─ Solar: 0% ZERADO (baixa propensão)
├─ TOTAL: 70% MANTIDO

LIMITES NOVOS:
├─ Consignado: R$ 185.430 (fixo)
├─ Imobiliário: R$ 166.335 (50% do original)
├─ Veículo: R$ 78.947 (com os 20%, em vez de 5%)
├─ Solar: R$ 0 (zerado)
└─ LIMITE GLOBAL: R$ 430.712 (diferente pois realocado)
```

---

## 7. Modelo de Propensão

### 7.1 Algoritmos (Ensemble)

```python
PROPENSITY_ENSEMBLE = {
    'primario': 'LightGBM',       # 70% peso
    'secundario': 'XGBoost',      # 20% peso
    'validacao': 'RandomForest',  # 10% peso
}

# Balanceamento: SMOTEENN
# Redução dimensionalidade: PCA (95% variância)
# AUC esperado: 85-95% dependendo do produto
```

### 7.2 Features Top 15 (Cross-Product)

```python
FEATURES_PROPENSAO_TOP15 = [
    'credit_score_internal',           # Score PRINAD
    'credit_utilization_ratio',        # % limite usado
    'annual_income',                   # Renda anual
    'transaction_frequency_12m',       # Transações/ano
    'revolving_utilization_ratio',     # % cartão usado
    'payment_history_score',           # % pagamentos em dia
    'months_customer_tenure',          # Tempo de cliente
    'delinquency_rate_12m',            # Taxa atraso 12m
    'discretionary_spending_ratio',    # Gastos não-essenciais
    'debt_to_income_ratio',            # DTI
    'employment_stability_proxy',      # Estabilidade emprego
    'product_holding_diversity',       # Qtd produtos
    'months_since_last_transaction',   # Inatividade
    'historical_product_usage_count',  # Uso histórico
    'app_engagement_score',            # Engajamento digital
]
```

### 7.3 Features Específicas por Produto

| Produto | Feature 1 | Feature 2 | Feature 3 |
|---------|-----------|-----------|-----------|
| Pessoal | transaction_freq | discretionary_ratio | months_since_txn |
| Consignado | margem_remaining | is_inss_eligible | refinance_history |
| Imobiliário | has_property | website_visits | income_stability |
| Cartão | txn_frequency_30d | online_shopping_ratio | utilization_ratio |
| 13º/IR | is_clt | current_month | advance_history |
| Solar | property_owner | electricity_bill | environmental_spend |

---

## 8. Dados Sintéticos Necessários (data_consolidator.py)

### 8.1 Campos Novos para ECL

| Campo | Tipo | Descrição | Como Gerar |
|-------|------|-----------|------------|
| `pd_12m` | DECIMAL(5,4) | PD 12 meses | Derivar do PRINAD + rating |
| `pd_lifetime` | DECIMAL(5,4) | PD lifetime | pd_12m × multiplicador |
| `lgd` | DECIMAL(5,4) | Loss Given Default | Por garantia/produto |
| `ead` | DECIMAL(15,2) | Exposure at Default | Saldo + limite×CCF |
| `ecl_12m` | DECIMAL(15,2) | ECL Stage 1 | pd_12m × lgd × ead |
| `ecl_lifetime` | DECIMAL(15,2) | ECL Stage 2/3 | pd_lifetime × lgd × ead |
| `stage` | INT | 1, 2 ou 3 | Baseado em atraso/rating |
| `ecl_current` | DECIMAL(15,2) | ECL atual | Depende do stage |

### 8.2 Campos Novos para Propensão

| Campo | Tipo | Descrição | Como Gerar |
|-------|------|-----------|------------|
| `propensao_score` | INT(0-100) | Score propensão | LightGBM ensemble |
| `propensao_classificacao` | VARCHAR | ALTA/MEDIA/BAIXA | Baseado no score |
| `transaction_frequency_12m` | INT | Transações/ano | Random 50-500 |
| `discretionary_spending_ratio` | DECIMAL | % gastos discricionários | Random 0.1-0.6 |
| `payment_history_score` | INT(0-100) | Histórico pagamentos | Inverso do atraso |
| `app_engagement_score` | INT(0-100) | Engajamento app | Random 20-95 |
| `months_customer_tenure` | INT | Meses como cliente | Random 6-180 |
| `employment_stability` | DECIMAL(0-1) | Estabilidade | Baseado em ocupação |

### 8.3 Campos para Limite Global

| Campo | Tipo | Descrição | Como Gerar |
|-------|------|-----------|------------|
| `limite_global` | DECIMAL(15,2) | Teto máximo | Renda × multiplicador |
| `soma_limites_produtos` | DECIMAL(15,2) | Soma limites | Agregado |
| `limite_realocavel` | DECIMAL(15,2) | Espaço livre | Global - soma |
| `comprometimento_atual` | DECIMAL(5,4) | DTI atual | Parcelas/Renda |

---

## 9. Arquivos a Modificar

### Core PRINAD
- `prinad/src/train_model.py` → Incorporar PD_12m e PD_lifetime
- `prinad/src/classifier.py` → Adicionar cálculo de PD por stage

### Propensão/ECL
- `propensao/src/data_consolidator.py` → Gerar todos campos novos
- `propensao/src/pipeline_runner.py` → Calcular ECL por stage + propensão
- `propensao/src/ecl_engine.py` → Refatorar para 3 stages
- `propensao/src/limit_optimizer.py` → Integrar limite global + realocação

### Novo
- `propensao/src/stage_classifier.py` → Lógica de migração de stages
- `propensao/src/propensity_model.py` → LightGBM + SMOTEENN
- `propensao/src/limit_reallocation.py` → Realocação por propensão

### Documentação
- `propensao/docs/metodologia_ecl_4966.md`
- `propensao/docs/dicionario_dados.md` (atualizar)
- `shared/utils.py` → Constantes novas

---

## 10. Próximos Passos

1. [ ] Aprovar este plano
2. [ ] Atualizar constantes em `shared/utils.py`
3. [ ] Refatorar `data_consolidator.py` com campos novos
4. [ ] Implementar `stage_classifier.py`
5. [ ] Refatorar `ecl_engine.py` para 3 stages
6. [ ] Implementar `propensity_model.py` com LightGBM
7. [ ] Implementar `limit_reallocation.py`
8. [ ] Atualizar `pipeline_runner.py` com fluxo completo
9. [ ] Executar pipeline e validar resultados
10. [ ] Atualizar documentação
11. [ ] Commit e push
