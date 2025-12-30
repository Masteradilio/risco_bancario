"""
PRINAD - FastAPI Application
REST API for credit risk classification with persistence and bank system simulation.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
import json
import sys
import csv
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from classifier import PRINADClassifier, ClassificationResult, get_classifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
AVALIACOES_FILE = DADOS_DIR / "avaliacoes_risco.csv"

# Create FastAPI app
app = FastAPI(
    title="PRINAD API",
    description="API para classificação de risco de crédito baseada em Basel III",
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

# Global state
classifier: Optional[PRINADClassifier] = None
connected_clients: List[WebSocket] = []
classification_stats = {
    "total": 0,
    "por_rating": {},
    "por_sistema": {},
    "por_produto": {},
    "por_tipo": {},
    "ultimas_24h": 0,
    "latencia_media_ms": 0
}

# CSV Headers
CSV_HEADERS = [
    'timestamp', 'cpf', 'pd_base', 'penalidade_historica', 'prinad', 
    'rating', 'rating_descricao', 'acao_sugerida', 'sistema_origem', 
    'produto_credito', 'tipo_solicitacao'
]


def init_csv_file():
    """Initialize CSVfile with headers if it doesn't exist."""
    if not AVALIACOES_FILE.exists():
        DADOS_DIR.mkdir(parents=True, exist_ok=True)
        with open(AVALIACOES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        logger.info(f"Created CSV file: {AVALIACOES_FILE}")


def persist_avaliacao(result: ClassificationResult, sistema_origem: str, 
                       produto_credito: str, tipo_solicitacao: str):
    """Persist classification result to CSV file."""
    try:
        with open(AVALIACOES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                result.timestamp,
                f"***{result.cpf[-4:]}" if len(result.cpf) >= 4 else result.cpf,
                round(result.pd_base, 2),
                round(result.penalidade_historica, 2),
                round(result.prinad, 2),
                result.rating,
                result.rating_descricao,
                result.acao_sugerida,
                sistema_origem or 'N/A',
                produto_credito or 'N/A',
                tipo_solicitacao or 'N/A'
            ])
    except Exception as e:
        logger.error(f"Error persisting avaliacao: {e}")


def load_avaliacoes(limit: int = 100) -> List[Dict[str, Any]]:
    """Load latest evaluations from CSV file."""
    avaliacoes = []
    try:
        if AVALIACOES_FILE.exists():
            with open(AVALIACOES_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                avaliacoes = list(reader)
            # Return last N records (most recent)
            avaliacoes = avaliacoes[-limit:] if len(avaliacoes) > limit else avaliacoes
            # Reverse to show most recent first
            avaliacoes.reverse()
    except Exception as e:
        logger.error(f"Error loading avaliacoes: {e}")
    return avaliacoes


# Pydantic Models
class DadosCadastrais(BaseModel):
    idade: Optional[int] = Field(None, alias="IDADE_CLIENTE")
    renda_bruta: Optional[float] = Field(None, alias="RENDA_BRUTA")
    renda_liquida: Optional[float] = Field(None, alias="RENDA_LIQUIDA")
    ocupacao: Optional[str] = Field(None, alias="OCUPACAO")
    escolaridade: Optional[str] = Field(None, alias="ESCOLARIDADE")
    estado_civil: Optional[str] = Field(None, alias="ESTADO_CIVIL")
    qt_dependentes: Optional[int] = Field(None, alias="QT_DEPENDENTES")
    tempo_relacionamento: Optional[float] = Field(None, alias="TEMPO_RELAC")
    tipo_residencia: Optional[str] = Field(None, alias="TIPO_RESIDENCIA")
    possui_veiculo: Optional[str] = Field(None, alias="POSSUI_VEICULO")
    portabilidade: Optional[str] = Field(None, alias="PORTABILIDADE")
    comp_renda: Optional[float] = Field(None, alias="COMP_RENDA")
    
    class Config:
        populate_by_name = True


class DadosComportamentais(BaseModel):
    v205: float = 0.0
    v210: float = 0.0
    v220: float = 0.0
    v230: float = 0.0
    v240: float = 0.0
    v245: float = 0.0
    v250: float = 0.0
    v255: float = 0.0
    v260: float = 0.0
    v270: float = 0.0
    v280: float = 0.0
    v290: float = 0.0


class ClassificationRequest(BaseModel):
    cpf: str
    dados_cadastrais: Dict[str, Any]
    dados_comportamentais: Dict[str, Any]
    # New fields for bank system simulation
    sistema_origem: Optional[str] = None
    produto_credito: Optional[str] = None
    tipo_solicitacao: Optional[str] = None


class BatchRequest(BaseModel):
    clientes: List[ClassificationRequest]


class ClassificationResponse(BaseModel):
    cpf: str
    prinad: float
    rating: str
    rating_descricao: str
    cor: str
    pd_base: float
    penalidade_historica: float
    peso_atual: float
    peso_historico: float
    acao_sugerida: str
    explicacao_shap: List[Dict[str, Any]]
    timestamp: str
    model_version: str
    # New fields
    sistema_origem: Optional[str] = None
    produto_credito: Optional[str] = None
    tipo_solicitacao: Optional[str] = None


class BatchResponse(BaseModel):
    total_processados: int
    total_sucesso: int
    total_erro: int
    resultados: List[Dict[str, Any]]
    erros: List[Dict[str, Any]]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    timestamp: str


class MetricsResponse(BaseModel):
    model_version: str
    total_classificacoes: int
    distribuicao_ratings: Dict[str, int]
    distribuicao_sistemas: Dict[str, int]
    distribuicao_produtos: Dict[str, int]
    distribuicao_tipos: Dict[str, int]
    latencia_media_ms: float
    timestamp: str


class AvaliacoesResponse(BaseModel):
    total: int
    avaliacoes: List[Dict[str, Any]]
    timestamp: str


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global classifier
    try:
        # Initialize CSV file
        init_csv_file()
        
        classifier = PRINADClassifier()
        if classifier.is_ready():
            logger.info("PRINAD classifier loaded successfully")
        else:
            logger.warning("Classifier loaded but model artifacts missing")
    except Exception as e:
        logger.error(f"Error loading classifier: {e}")


# Health check
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy" if classifier and classifier.is_ready() else "degraded",
        model_loaded=classifier is not None and classifier.is_ready(),
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


# Single prediction
@app.post("/predict", response_model=ClassificationResponse, tags=["Classification"])
async def predict(request: ClassificationRequest):
    """
    Classify a single client.
    
    Returns PRINAD score, rating, and SHAP explanation.
    """
    global classification_stats
    
    if not classifier or not classifier.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = datetime.now()
    
    try:
        result = classifier.classify({
            "cpf": request.cpf,
            "dados_cadastrais": request.dados_cadastrais,
            "dados_comportamentais": request.dados_comportamentais
        })
        
        # Update stats
        classification_stats["total"] += 1
        rating = result.rating
        classification_stats["por_rating"][rating] = classification_stats["por_rating"].get(rating, 0) + 1
        
        # Update bank system stats
        if request.sistema_origem:
            classification_stats["por_sistema"][request.sistema_origem] = \
                classification_stats["por_sistema"].get(request.sistema_origem, 0) + 1
        if request.produto_credito:
            classification_stats["por_produto"][request.produto_credito] = \
                classification_stats["por_produto"].get(request.produto_credito, 0) + 1
        if request.tipo_solicitacao:
            classification_stats["por_tipo"][request.tipo_solicitacao] = \
                classification_stats["por_tipo"].get(request.tipo_solicitacao, 0) + 1
        
        # Calculate latency
        latency = (datetime.now() - start_time).total_seconds() * 1000
        classification_stats["latencia_media_ms"] = (
            (classification_stats["latencia_media_ms"] * (classification_stats["total"] - 1) + latency) 
            / classification_stats["total"]
        )
        
        # Persist to CSV
        persist_avaliacao(
            result, 
            request.sistema_origem,
            request.produto_credito,
            request.tipo_solicitacao
        )
        
        # Broadcast to WebSocket clients
        await broadcast_classification(result, request.sistema_origem, 
                                        request.produto_credito, request.tipo_solicitacao)
        
        # Build response
        response_data = result.to_dict()
        response_data['sistema_origem'] = request.sistema_origem
        response_data['produto_credito'] = request.produto_credito
        response_data['tipo_solicitacao'] = request.tipo_solicitacao
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Batch prediction
@app.post("/batch", response_model=BatchResponse, tags=["Classification"])
async def batch_predict(request: BatchRequest):
    """
    Classify multiple clients in batch.
    """
    if not classifier or not classifier.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    resultados = []
    erros = []
    
    for cliente in request.clientes:
        try:
            result = classifier.classify({
                "cpf": cliente.cpf,
                "dados_cadastrais": cliente.dados_cadastrais,
                "dados_comportamentais": cliente.dados_comportamentais
            })
            
            # Persist to CSV
            persist_avaliacao(
                result,
                cliente.sistema_origem,
                cliente.produto_credito,
                cliente.tipo_solicitacao
            )
            
            resultados.append({
                "cpf": result.cpf,
                "prinad": result.prinad,
                "rating": result.rating,
                "sistema_origem": cliente.sistema_origem,
                "produto_credito": cliente.produto_credito,
                "tipo_solicitacao": cliente.tipo_solicitacao,
                "status": "sucesso"
            })
        except Exception as e:
            erros.append({
                "cpf": cliente.cpf,
                "erro": str(e),
                "status": "erro"
            })
    
    return BatchResponse(
        total_processados=len(request.clientes),
        total_sucesso=len(resultados),
        total_erro=len(erros),
        resultados=resultados,
        erros=erros,
        timestamp=datetime.now().isoformat()
    )


# Metrics
@app.get("/metrics", response_model=MetricsResponse, tags=["System"])
async def get_metrics():
    """Get classification metrics."""
    return MetricsResponse(
        model_version="1.0.0",
        total_classificacoes=classification_stats["total"],
        distribuicao_ratings=classification_stats["por_rating"],
        distribuicao_sistemas=classification_stats["por_sistema"],
        distribuicao_produtos=classification_stats["por_produto"],
        distribuicao_tipos=classification_stats["por_tipo"],
        latencia_media_ms=round(classification_stats["latencia_media_ms"], 2),
        timestamp=datetime.now().isoformat()
    )


# Get evaluations - NEW ENDPOINT
@app.get("/avaliacoes", response_model=AvaliacoesResponse, tags=["Data"])
async def get_avaliacoes(limit: int = 50):
    """
    Get latest evaluations from the CSV file.
    
    Args:
        limit: Maximum number of evaluations to return (default: 50)
    """
    avaliacoes = load_avaliacoes(limit)
    return AvaliacoesResponse(
        total=len(avaliacoes),
        avaliacoes=avaliacoes,
        timestamp=datetime.now().isoformat()
    )


# Get statistics - NEW ENDPOINT
@app.get("/stats", tags=["System"])
async def get_stats():
    """
    Get aggregated statistics by system, product, and type.
    """
    avaliacoes = load_avaliacoes(1000)  # Load more for better stats
    
    stats = {
        "total_avaliacoes": len(avaliacoes),
        "por_sistema": {},
        "por_produto": {},
        "por_tipo": {},
        "por_rating": {},
        "prinad_medio": 0.0
    }
    
    if avaliacoes:
        prinad_sum = 0
        for av in avaliacoes:
            # Sistema
            sistema = av.get('sistema_origem', 'N/A')
            stats["por_sistema"][sistema] = stats["por_sistema"].get(sistema, 0) + 1
            
            # Produto
            produto = av.get('produto_credito', 'N/A')
            stats["por_produto"][produto] = stats["por_produto"].get(produto, 0) + 1
            
            # Tipo
            tipo = av.get('tipo_solicitacao', 'N/A')
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            
            # Rating
            rating = av.get('rating', 'N/A')
            stats["por_rating"][rating] = stats["por_rating"].get(rating, 0) + 1
            
            # PRINAD sum
            try:
                prinad_sum += float(av.get('prinad', 0))
            except:
                pass
        
        stats["prinad_medio"] = round(prinad_sum / len(avaliacoes), 2)
    
    stats["timestamp"] = datetime.now().isoformat()
    return stats


# Clear evaluations - Utility endpoint
@app.delete("/avaliacoes", tags=["Data"])
async def clear_avaliacoes():
    """Clear all evaluations (reset CSV file)."""
    global classification_stats
    try:
        init_csv_file()
        # Also reset in-memory stats
        classification_stats = {
            "total": 0,
            "por_rating": {},
            "por_sistema": {},
            "por_produto": {},
            "por_tipo": {},
            "ultimas_24h": 0,
            "latencia_media_ms": 0
        }
        # Reinitialize file
        with open(AVALIACOES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        return {"message": "Evaluations cleared", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for real-time streaming
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time classification streaming.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"New WebSocket connection. Total clients: {len(connected_clients)}")
    
    try:
        while True:
            # Receive classification request
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "classify":
                payload = message.get("payload", {})
                
                if classifier and classifier.is_ready():
                    result = classifier.classify(payload)
                    
                    await websocket.send_json({
                        "type": "classification_result",
                        "payload": result.to_dict()
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Model not ready"}
                    })
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"WebSocket disconnected. Total clients: {len(connected_clients)}")


async def broadcast_classification(result: ClassificationResult, sistema_origem: str = None,
                                    produto_credito: str = None, tipo_solicitacao: str = None):
    """Broadcast classification result to all connected WebSocket clients."""
    if connected_clients:
        message = {
            "type": "new_classification",
            "payload": {
                "cpf": result.cpf[-4:].zfill(4),  # Last 4 digits only for privacy
                "prinad": result.prinad,
                "rating": result.rating,
                "cor": result.cor,
                "sistema_origem": sistema_origem,
                "produto_credito": produto_credito,
                "tipo_solicitacao": tipo_solicitacao,
                "timestamp": result.timestamp
            }
        }
        
        for client in connected_clients:
            try:
                await client.send_json(message)
            except:
                pass  # Client disconnected


# Explain endpoint
@app.get("/explain/{cpf}", tags=["Classification"])
async def explain_classification(cpf: str):
    """
    Get detailed SHAP explanation for a CPF.
    
    Note: Requires the client data to be available in the database.
    """
    # In production, this would fetch client data from database
    raise HTTPException(
        status_code=501, 
        detail="Not implemented. Use /predict endpoint with full client data."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
