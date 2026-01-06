"""
ECL (Perda Esperada) - FastAPI Application
REST API para calculo de Expected Credit Loss - BACEN 4966 Compliant.

Endpoints:
- /health - Health check
- /calcular - Calculo ECL individual
- /calcular_portfolio - Calculo ECL para portfolio
- /grupos_homogeneos - Distribuicao por grupos
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

from perda_esperada.src.pipeline_ecl import ECLPipeline, ECLCompleteResult
from prinad.src.classifier import PRINADClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ECL API",
    description="API de Perda Esperada (ECL) - BACEN 4966 Compliant",
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
pipeline: Optional[ECLPipeline] = None
classifier: Optional[PRINADClassifier] = None


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    pipeline_loaded: bool
    classifier_loaded: bool
    version: str
    timestamp: str


class ECLRequest(BaseModel):
    """Request para calculo de ECL."""
    cpf: str = Field(..., description="CPF do cliente")
    produto: str = Field(..., description="Tipo de produto (consignado, imobiliario, etc)")
    saldo_utilizado: float = Field(..., description="Saldo devedor atual")
    limite_total: float = Field(..., description="Limite total do credito")
    dias_atraso: int = Field(0, description="Dias em atraso")
    valor_operacao: Optional[float] = Field(None, description="Valor da operacao")
    prazo_remanescente: Optional[int] = Field(None, description="Prazo remanescente em meses")
    ocupacao: Optional[str] = Field(None, description="Ocupacao do cliente")


class ECLDirectRequest(BaseModel):
    """Request para calculo de ECL direto (sem classificacao PRINAD)."""
    cliente_id: str = Field(..., description="ID do cliente")
    produto: str = Field(..., description="Tipo de produto")
    saldo_utilizado: float = Field(..., description="Saldo devedor atual")
    limite_total: float = Field(..., description="Limite total")
    dias_atraso: int = Field(0, description="Dias em atraso")
    prinad: float = Field(..., description="Score PRINAD (0-100)")
    rating: str = Field(..., description="Rating (A1-DEFAULT)")
    pd_12m: float = Field(..., description="PD 12 meses")
    pd_lifetime: float = Field(..., description="PD Lifetime")
    stage: int = Field(..., description="Stage IFRS 9 (1, 2 ou 3)")


class ECLResponse(BaseModel):
    """Response do calculo de ECL."""
    cliente_id: str
    produto: str
    prinad: float
    rating: str
    stage: int
    grupo_homogeneo: int
    pd_ajustado: float
    lgd_final: float
    ead: float
    ecl_final: float
    horizonte_ecl: str
    piso_aplicado: bool
    timestamp: str


class PortfolioRequest(BaseModel):
    """Request para calculo de portfolio."""
    operacoes: List[ECLDirectRequest]


class PortfolioResponse(BaseModel):
    """Response do calculo de portfolio."""
    total_operacoes: int
    ecl_total: float
    media_pd: float
    media_lgd: float
    distribuicao_stages: Dict[int, int]
    distribuicao_grupos: Dict[int, int]
    resultados: List[Dict[str, Any]]
    timestamp: str


class GruposHomogeneosResponse(BaseModel):
    """Response com distribuicao de grupos homogeneos."""
    grupos: Dict[int, Dict[str, Any]]
    total_clientes: int


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load pipeline and classifier on startup."""
    global pipeline, classifier
    
    try:
        pipeline = ECLPipeline()
        logger.info("ECL Pipeline loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ECL Pipeline: {e}")
    
    try:
        classifier = PRINADClassifier()
        logger.info("PRINAD Classifier loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load PRINAD Classifier: {e}")


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """Verificar status da API."""
    return HealthResponse(
        status="healthy" if pipeline and classifier else "degraded",
        pipeline_loaded=pipeline is not None,
        classifier_loaded=classifier is not None,
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/calcular", response_model=ECLResponse, tags=["ECL"])
async def calcular_ecl(request: ECLRequest):
    """
    Calcula ECL para um cliente.
    
    1. Classifica o cliente usando PRINAD
    2. Calcula ECL usando o pipeline
    """
    if not pipeline or not classifier:
        raise HTTPException(status_code=503, detail="Pipeline ou Classifier nao carregado")
    
    try:
        # 1. Classificar com PRINAD
        client_data = {
            'cpf': request.cpf,
            'dados_cadastrais': {},
            'dados_comportamentais': {
                'v205': request.dias_atraso if request.dias_atraso <= 30 else 0,
                'v210': request.dias_atraso if 30 < request.dias_atraso <= 60 else 0,
            }
        }
        prinad_result = classifier.classify(client_data)
        
        # 2. Calcular ECL
        ecl_result = pipeline.calcular_ecl_de_prinad_result(
            prinad_result=prinad_result,
            produto=request.produto,
            saldo_utilizado=request.saldo_utilizado,
            limite_total=request.limite_total,
            dias_atraso=request.dias_atraso
        )
        
        return ECLResponse(
            cliente_id=request.cpf,
            produto=request.produto,
            prinad=ecl_result.prinad,
            rating=ecl_result.rating,
            stage=ecl_result.stage,
            grupo_homogeneo=ecl_result.grupo_homogeneo,
            pd_ajustado=ecl_result.pd_ajustado,
            lgd_final=ecl_result.lgd_final,
            ead=ecl_result.ead,
            ecl_final=ecl_result.ecl_final,
            horizonte_ecl=ecl_result.horizonte_ecl,
            piso_aplicado=ecl_result.piso_aplicado,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error calculating ECL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calcular_direto", response_model=ECLResponse, tags=["ECL"])
async def calcular_ecl_direto(request: ECLDirectRequest):
    """
    Calcula ECL usando dados PRINAD fornecidos diretamente.
    
    Util quando ja se tem o resultado do PRINAD.
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline nao carregado")
    
    try:
        ecl_result = pipeline.calcular_ecl_completo(
            cliente_id=request.cliente_id,
            produto=request.produto,
            saldo_utilizado=request.saldo_utilizado,
            limite_total=request.limite_total,
            dias_atraso=request.dias_atraso,
            prinad=request.prinad,
            rating=request.rating,
            pd_12m=request.pd_12m,
            pd_lifetime=request.pd_lifetime,
            stage=request.stage
        )
        
        return ECLResponse(
            cliente_id=request.cliente_id,
            produto=request.produto,
            prinad=ecl_result.prinad,
            rating=ecl_result.rating,
            stage=ecl_result.stage,
            grupo_homogeneo=ecl_result.grupo_homogeneo,
            pd_ajustado=ecl_result.pd_ajustado,
            lgd_final=ecl_result.lgd_final,
            ead=ecl_result.ead,
            ecl_final=ecl_result.ecl_final,
            horizonte_ecl=ecl_result.horizonte_ecl,
            piso_aplicado=ecl_result.piso_aplicado,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error calculating ECL direto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calcular_portfolio", response_model=PortfolioResponse, tags=["Portfolio"])
async def calcular_portfolio(request: PortfolioRequest):
    """
    Calcula ECL para um portfolio de operacoes.
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline nao carregado")
    
    resultados = []
    ecl_total = 0.0
    soma_pd = 0.0
    soma_lgd = 0.0
    distribuicao_stages = {1: 0, 2: 0, 3: 0}
    distribuicao_grupos = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for op in request.operacoes:
        try:
            ecl_result = pipeline.calcular_ecl_completo(
                cliente_id=op.cliente_id,
                produto=op.produto,
                saldo_utilizado=op.saldo_utilizado,
                limite_total=op.limite_total,
                dias_atraso=op.dias_atraso,
                prinad=op.prinad,
                rating=op.rating,
                pd_12m=op.pd_12m,
                pd_lifetime=op.pd_lifetime,
                stage=op.stage
            )
            
            resultados.append(ecl_result.to_dict())
            ecl_total += ecl_result.ecl_final
            soma_pd += ecl_result.pd_ajustado
            soma_lgd += ecl_result.lgd_final
            distribuicao_stages[ecl_result.stage] = distribuicao_stages.get(ecl_result.stage, 0) + 1
            distribuicao_grupos[ecl_result.grupo_homogeneo] = distribuicao_grupos.get(ecl_result.grupo_homogeneo, 0) + 1
            
        except Exception as e:
            logger.error(f"Error processing operation {op.cliente_id}: {e}")
    
    n = len(resultados)
    return PortfolioResponse(
        total_operacoes=n,
        ecl_total=ecl_total,
        media_pd=soma_pd / n if n > 0 else 0,
        media_lgd=soma_lgd / n if n > 0 else 0,
        distribuicao_stages=distribuicao_stages,
        distribuicao_grupos=distribuicao_grupos,
        resultados=resultados,
        timestamp=datetime.now().isoformat()
    )


@app.get("/grupos_homogeneos", response_model=GruposHomogeneosResponse, tags=["Analytics"])
async def obter_grupos_homogeneos():
    """
    Retorna informacoes sobre os grupos homogeneos.
    """
    grupos = {
        1: {
            "nome": "Baixo Risco",
            "faixa_prinad": "0-25%",
            "pd_base": 0.005,
            "descricao": "Clientes com excelente comportamento de credito"
        },
        2: {
            "nome": "Risco Moderado",
            "faixa_prinad": "25-50%",
            "pd_base": 0.05,
            "descricao": "Clientes com bom historico, algumas restricoes"
        },
        3: {
            "nome": "Risco Alto",
            "faixa_prinad": "50-75%",
            "pd_base": 0.15,
            "descricao": "Clientes que requerem atencao"
        },
        4: {
            "nome": "Risco Muito Alto",
            "faixa_prinad": "75-100%",
            "pd_base": 0.40,
            "descricao": "Clientes com alto risco de inadimplencia"
        }
    }
    
    return GruposHomogeneosResponse(
        grupos=grupos,
        total_clientes=0  # Seria preenchido com dados reais
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
