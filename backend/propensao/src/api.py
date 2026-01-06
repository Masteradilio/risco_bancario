"""
Propensao (PROLIMITE) - FastAPI Application
REST API para calculo de propensao e otimizacao de limites.

Endpoints:
- /health - Health check
- /score - Calcula score de propensao
- /recomendar - Recomendacao de limite
- /simular - Simulacao de impacto
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from propensao.src.pipeline_runner import (
    PRINADEnricher,
    PropensityEnricher,
    ECLCalculator,
    LimitActionCalculator
)
from propensao.src.propensity_model import PropensityModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Propensao API",
    description="API de Propensao e Otimizacao de Limites - PROLIMITE",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
propensity_enricher: Optional[PropensityEnricher] = None
limit_calculator: Optional[LimitActionCalculator] = None
propensity_model: Optional[PropensityModel] = None


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    enricher_loaded: bool
    calculator_loaded: bool
    version: str
    timestamp: str


class ScoreRequest(BaseModel):
    """Request para score de propensao."""
    cpf: str = Field(..., description="CPF do cliente")
    produto: str = Field(..., description="Produto de credito")
    prinad: float = Field(..., description="Score PRINAD (0-100)")
    renda: float = Field(..., description="Renda mensal")
    utilizacao: float = Field(..., description="Taxa de utilizacao (0-1)")
    tempo_relacionamento: int = Field(..., description="Tempo de relacionamento em meses")


class ScoreResponse(BaseModel):
    """Response do score de propensao."""
    cpf: str
    produto: str
    propensity_score: float
    classificacao: str
    recomendacao: str
    timestamp: str


class RecomendacaoRequest(BaseModel):
    """Request para recomendacao de limite."""
    cpf: str = Field(..., description="CPF do cliente")
    produto: str = Field(..., description="Produto de credito")
    prinad: float = Field(..., description="Score PRINAD (0-100)")
    propensity_score: float = Field(..., description="Score de propensao (0-1)")
    limite_atual: float = Field(..., description="Limite atual")
    saldo_utilizado: float = Field(..., description="Saldo utilizado")
    margem_disponivel: float = Field(0, description="Margem disponivel para aumento")


class RecomendacaoResponse(BaseModel):
    """Response da recomendacao de limite."""
    cpf: str
    produto: str
    acao: str
    percentual_ajuste: float
    novo_limite: float
    justificativa: str
    economia_ecl: float
    timestamp: str


class SimulacaoRequest(BaseModel):
    """Request para simulacao de impacto."""
    portfolio: List[Dict[str, Any]] = Field(..., description="Lista de operacoes")
    cenario: str = Field("conservador", description="Cenario: conservador, moderado, agressivo")


class SimulacaoResponse(BaseModel):
    """Response da simulacao."""
    cenario: str
    ecl_atual: float
    ecl_projetado: float
    economia_ecl: float
    receita_adicional: float
    impacto_liquido: float
    distribuicao_acoes: Dict[str, int]
    timestamp: str


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load components on startup."""
    global propensity_enricher, limit_calculator, propensity_model
    
    try:
        propensity_enricher = PropensityEnricher()
        logger.info("Propensity Enricher loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Propensity Enricher: {e}")
    
    try:
        limit_calculator = LimitActionCalculator()
        logger.info("Limit Calculator loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Limit Calculator: {e}")
    
    try:
        propensity_model = PropensityModel()
        logger.info("Propensity Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Propensity Model: {e}")


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """Verificar status da API."""
    return HealthResponse(
        status="healthy" if propensity_enricher and limit_calculator else "degraded",
        enricher_loaded=propensity_enricher is not None,
        calculator_loaded=limit_calculator is not None,
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/score", response_model=ScoreResponse, tags=["Propensao"])
async def calcular_score(request: ScoreRequest):
    """
    Calcula score de propensao para um produto.
    """
    if not propensity_enricher:
        raise HTTPException(status_code=503, detail="Enricher nao carregado")
    
    try:
        import pandas as pd
        
        # Criar row para calculo
        row = pd.Series({
            'CPF': request.cpf,
            'PRINAD_SCORE': request.prinad,
            'RENDA_BRUTA': request.renda,
            'utilizacao_consignado': request.utilizacao,
            'TEMPO_RELACIONAMENTO_MESES': request.tempo_relacionamento
        })
        
        # Calcular propensao
        score = propensity_enricher.calculate_propensity_heuristic(
            row, request.produto, request.prinad
        )
        
        # Classificar
        if score >= 0.7:
            classificacao = "ALTA"
            recomendacao = "Cliente com alta propensao, considerar ofertas"
        elif score >= 0.4:
            classificacao = "MEDIA"
            recomendacao = "Cliente com propensao moderada"
        else:
            classificacao = "BAIXA"
            recomendacao = "Cliente com baixa propensao, manter monitoramento"
        
        return ScoreResponse(
            cpf=request.cpf,
            produto=request.produto,
            propensity_score=score,
            classificacao=classificacao,
            recomendacao=recomendacao,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recomendar", response_model=RecomendacaoResponse, tags=["Limites"])
async def recomendar_limite(request: RecomendacaoRequest):
    """
    Gera recomendacao de ajuste de limite.
    """
    if not limit_calculator:
        raise HTTPException(status_code=503, detail="Calculator nao carregado")
    
    try:
        import pandas as pd
        
        # Criar row para calculo
        utilizacao = request.saldo_utilizado / request.limite_atual if request.limite_atual > 0 else 0
        
        row = pd.Series({
            'CPF': request.cpf,
            'PRINAD_SCORE': request.prinad,
            'propensity_score': request.propensity_score,
            f'limite_{request.produto}': request.limite_atual,
            f'saldo_{request.produto}': request.saldo_utilizado,
            f'utilizacao_{request.produto}': utilizacao,
            'margem_consignavel': request.margem_disponivel
        })
        
        # Calcular acao
        result = limit_calculator.calculate_action(row)
        
        # Calcular novo limite
        acao = result.get('acao', 'MANTER')
        percentual = 0.0
        novo_limite = request.limite_atual
        economia_ecl = 0.0
        
        if acao == 'AUMENTAR':
            percentual = result.get('percentual', 0.25)
            novo_limite = request.limite_atual * (1 + percentual)
        elif acao == 'REDUZIR':
            percentual = result.get('percentual', 0.25)
            novo_limite = request.limite_atual * (1 - percentual)
            # Economia ECL estimada
            limite_reduzido = request.limite_atual - novo_limite
            economia_ecl = limite_reduzido * 0.01 * 0.35  # PD * LGD aproximados
        elif acao == 'ZERAR':
            percentual = 1.0
            novo_limite = 0
            economia_ecl = (request.limite_atual - request.saldo_utilizado) * 0.05 * 0.35
        
        return RecomendacaoResponse(
            cpf=request.cpf,
            produto=request.produto,
            acao=acao,
            percentual_ajuste=percentual,
            novo_limite=novo_limite,
            justificativa=result.get('justificativa', 'Sem justificativa'),
            economia_ecl=economia_ecl,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error recommending limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simular", response_model=SimulacaoResponse, tags=["Simulacao"])
async def simular_impacto(request: SimulacaoRequest):
    """
    Simula impacto financeiro de ajustes de limite.
    """
    try:
        # Parametros por cenario
        cenarios = {
            "conservador": {"reducao": 0.10, "taxa_conversao": 0.30},
            "moderado": {"reducao": 0.15, "taxa_conversao": 0.40},
            "agressivo": {"reducao": 0.20, "taxa_conversao": 0.50}
        }
        
        params = cenarios.get(request.cenario, cenarios["moderado"])
        
        # Calcular metricas
        ecl_atual = 0.0
        limite_total = 0.0
        limite_nao_utilizado = 0.0
        distribuicao = {"MANTER": 0, "AUMENTAR": 0, "REDUZIR": 0, "ZERAR": 0}
        
        for op in request.portfolio:
            limite = op.get("limite", 0)
            saldo = op.get("saldo", 0)
            pd = op.get("pd", 0.05)
            lgd = op.get("lgd", 0.35)
            
            limite_total += limite
            limite_nao_utilizado += max(0, limite - saldo)
            ecl_atual += saldo * pd * lgd
            
            # Simular acao
            prinad = op.get("prinad", 50)
            if prinad >= 95:
                distribuicao["ZERAR"] += 1
            elif prinad >= 80:
                distribuicao["REDUZIR"] += 1
            elif prinad <= 30 and op.get("propensity", 0.5) >= 0.6:
                distribuicao["AUMENTAR"] += 1
            else:
                distribuicao["MANTER"] += 1
        
        # Projecoes
        reducao_limite = limite_nao_utilizado * params["reducao"]
        economia_ecl = reducao_limite * 0.013  # 1.3% (PD * LGD medio)
        
        aumento_credito = limite_total * 0.14 * 0.25 * params["taxa_conversao"]  # 14% alta propensao, 25% aumento
        receita_adicional = aumento_credito * 0.235  # Spread medio 23.5%
        
        ecl_projetado = ecl_atual - economia_ecl
        impacto_liquido = economia_ecl + receita_adicional - (receita_adicional * 0.10)  # 10% custo operacional
        
        return SimulacaoResponse(
            cenario=request.cenario,
            ecl_atual=ecl_atual,
            ecl_projetado=ecl_projetado,
            economia_ecl=economia_ecl,
            receita_adicional=receita_adicional,
            impacto_liquido=impacto_liquido,
            distribuicao_acoes=distribuicao,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error simulating impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/produtos", tags=["Config"])
async def listar_produtos():
    """Lista produtos de credito disponiveis."""
    return {
        "produtos": [
            {"codigo": "consignado", "nome": "Credito Consignado", "lgd_base": 0.25},
            {"codigo": "cartao_credito_rotativo", "nome": "Cartao de Credito", "lgd_base": 0.80},
            {"codigo": "imobiliario", "nome": "Credito Imobiliario", "lgd_base": 0.10},
            {"codigo": "veiculo", "nome": "Financiamento de Veiculo", "lgd_base": 0.35},
            {"codigo": "energia_solar", "nome": "Energia Solar", "lgd_base": 0.35}
        ]
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
