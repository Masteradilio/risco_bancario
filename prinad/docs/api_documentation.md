# API PRINAD - Documentação Técnica

## Visão Geral

A API PRINAD fornece endpoints RESTful para classificação de risco de crédito em tempo real, utilizando modelo de machine learning em conformidade com Basel III.

**Base URL**: `http://localhost:8000`

**Versão**: `1.0.0`

---

## Autenticação

A API utiliza autenticação via API Key no header:

```http
Authorization: Bearer <API_KEY>
```

---

## Endpoints

### 1. Health Check

Verifica se a API está funcionando corretamente.

```http
GET /health
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0",
  "timestamp": "2024-12-23T21:52:00Z"
}
```

---

### 2. Classificação Individual

Classifica um único cliente pelo CPF.

```http
POST /predict
```

**Request Body**:
```json
{
  "cpf": "12345678901",
  "dados_cadastrais": {
    "idade": 35,
    "renda_bruta": 5000.00,
    "renda_liquida": 4200.00,
    "ocupacao": "ASSALARIADO",
    "escolaridade": "SUPERIOR",
    "estado_civil": "CASADO",
    "qt_dependentes": 2,
    "tempo_relacionamento": 48,
    "tipo_residencia": "PROPRIA",
    "possui_veiculo": "SIM",
    "portabilidade": "NAO PORTADO"
  },
  "dados_comportamentais": {
    "v205": 0.0,
    "v210": 0.0,
    "v220": 0.0,
    "v230": 0.0,
    "v240": 0.0,
    "v245": 0.0,
    "v250": 0.0,
    "v255": 0.0,
    "v260": 0.0,
    "v270": 0.0,
    "v280": 0.0,
    "v290": 0.0
  }
}
```

**Response** `200 OK`:
```json
{
  "cpf": "12345678901",
  "prinad": 8.5,
  "rating": "A3",
  "rating_descricao": "Risco Baixo",
  "cor": "verde",
  "pd_base": 8.5,
  "penalidade_historica": 0.0,
  "componentes": {
    "peso_atual": 0.5,
    "peso_historico": 0.5
  },
  "acao_sugerida": "Aprovação com análise simplificada",
  "explicacao_shap": [
    {"feature": "renda_liquida", "valor": 4200.0, "contribuicao": -2.1, "direcao": "reduz_risco"},
    {"feature": "tempo_relacionamento", "valor": 48, "contribuicao": -1.8, "direcao": "reduz_risco"},
    {"feature": "ocupacao", "valor": "ASSALARIADO", "contribuicao": -0.9, "direcao": "reduz_risco"},
    {"feature": "qt_dependentes", "valor": 2, "contribuicao": +0.5, "direcao": "aumenta_risco"},
    {"feature": "escolaridade", "valor": "SUPERIOR", "contribuicao": -0.7, "direcao": "reduz_risco"}
  ],
  "timestamp": "2024-12-23T21:52:00Z",
  "model_version": "1.0.0"
}
```

**Códigos de Erro**:

| Código | Descrição |
|--------|-----------|
| 400 | Dados inválidos ou incompletos |
| 404 | CPF não encontrado na base |
| 500 | Erro interno do servidor |

---

### 3. Classificação em Lote

Classifica múltiplos clientes de uma vez.

```http
POST /batch
```

**Request Body**:
```json
{
  "clientes": [
    {
      "cpf": "12345678901",
      "dados_cadastrais": {...},
      "dados_comportamentais": {...}
    },
    {
      "cpf": "98765432100",
      "dados_cadastrais": {...},
      "dados_comportamentais": {...}
    }
  ]
}
```

**Response** `200 OK`:
```json
{
  "total_processados": 2,
  "total_sucesso": 2,
  "total_erro": 0,
  "resultados": [
    {
      "cpf": "12345678901",
      "prinad": 8.5,
      "rating": "A3",
      "status": "sucesso"
    },
    {
      "cpf": "98765432100",
      "prinad": 45.2,
      "rating": "B3",
      "status": "sucesso"
    }
  ],
  "erros": [],
  "timestamp": "2024-12-23T21:52:00Z"
}
```

---

### 4. Stream de Classificação (WebSocket)

Endpoint para classificação em tempo real via WebSocket.

```
ws://localhost:8000/ws/stream
```

**Mensagem de Entrada**:
```json
{
  "type": "classify",
  "payload": {
    "cpf": "12345678901",
    "dados_cadastrais": {...},
    "dados_comportamentais": {...}
  }
}
```

**Mensagem de Saída**:
```json
{
  "type": "classification_result",
  "payload": {
    "cpf": "12345678901",
    "prinad": 8.5,
    "rating": "A3",
    "timestamp": "2024-12-23T21:52:00.123Z"
  }
}
```

---

### 5. Métricas do Modelo

Retorna estatísticas de performance do modelo.

```http
GET /metrics
```

**Response** `200 OK`:
```json
{
  "model_version": "1.0.0",
  "treinado_em": "2024-12-23",
  "metricas_validacao": {
    "auc_roc": 0.82,
    "gini": 0.64,
    "ks": 0.47,
    "precision_default": 0.75,
    "recall_default": 0.71
  },
  "distribuicao_ratings": {
    "A1": 0.05,
    "A2": 0.10,
    "A3": 0.15,
    "B1": 0.20,
    "B2": 0.18,
    "B3": 0.12,
    "C1": 0.10,
    "C2": 0.07,
    "D": 0.03
  },
  "classificacoes_ultimas_24h": 15234,
  "latencia_media_ms": 45
}
```

---

### 6. Explicação Individual

Retorna explicação SHAP detalhada para uma classificação.

```http
GET /explain/{cpf}
```

**Response** `200 OK`:
```json
{
  "cpf": "12345678901",
  "prinad": 8.5,
  "rating": "A3",
  "explicacao_completa": {
    "base_value": 15.0,
    "output_value": 8.5,
    "features": [
      {
        "nome": "renda_liquida",
        "valor_cliente": 4200.0,
        "valor_medio_populacao": 3100.0,
        "shap_value": -2.1,
        "interpretacao": "Renda acima da média reduz risco em 2.1 pontos percentuais"
      },
      ...
    ]
  },
  "grafico_waterfall_base64": "iVBORw0KGgoAAAANSUhEUg..."
}
```

---

## Modelos de Dados

### Rating

```typescript
enum Rating {
  A1 = "A1",  // 0.00% - 2.00%
  A2 = "A2",  // 2.00% - 5.00%
  A3 = "A3",  // 5.00% - 10.00%
  B1 = "B1",  // 10.00% - 20.00%
  B2 = "B2",  // 20.00% - 35.00%
  B3 = "B3",  // 35.00% - 50.00%
  C1 = "C1",  // 50.00% - 70.00%
  C2 = "C2",  // 70.00% - 90.00%
  D  = "D"    // 90.00% - 100.00%
}
```

### Cores

| Rating | HEX | Nome |
|--------|-----|------|
| A1-A3 | `#22c55e` | Verde |
| B1-B2 | `#eab308` | Amarelo |
| B3 | `#f97316` | Laranja |
| C1-C2 | `#ef4444` | Vermelho |
| D | `#1f2937` | Preto |

---

## Limites e Rate Limiting

| Endpoint | Limite | Janela |
|----------|--------|--------|
| `/predict` | 100 req | 1 min |
| `/batch` | 10 req | 1 min |
| `/ws/stream` | 1000 msg | 1 min |

---

## Exemplos de Uso

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "sua_api_key"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Classificação individual
response = requests.post(
    f"{API_URL}/predict",
    headers=headers,
    json={
        "cpf": "12345678901",
        "dados_cadastrais": {
            "idade": 35,
            "renda_bruta": 5000.00,
            # ...
        },
        "dados_comportamentais": {
            "v205": 0.0,
            # ...
        }
    }
)

resultado = response.json()
print(f"PRINAD: {resultado['prinad']}% - Rating: {resultado['rating']}")
```

### cURL

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Authorization: Bearer sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "cpf": "12345678901",
    "dados_cadastrais": {"idade": 35, "renda_bruta": 5000},
    "dados_comportamentais": {"v205": 0.0}
  }'
```

---

## Changelog

### v1.0.0 (2024-12-23)
- Lançamento inicial
- Endpoints: `/health`, `/predict`, `/batch`, `/ws/stream`, `/metrics`, `/explain`
- Modelo ensemble XGBoost + LightGBM + CatBoost
- SHAP interpretability integrado
