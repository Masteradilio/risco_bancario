"""
PRINAD - FastAPI Application
REST API for credit risk classification.
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
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from classifier import PRINADClassifier, ClassificationResult, get_classifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    "ultimas_24h": 0,
    "latencia_media_ms": 0
}


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
    latencia_media_ms: float
    timestamp: str


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global classifier
    try:
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
        
        # Calculate latency
        latency = (datetime.now() - start_time).total_seconds() * 1000
        classification_stats["latencia_media_ms"] = (
            (classification_stats["latencia_media_ms"] * (classification_stats["total"] - 1) + latency) 
            / classification_stats["total"]
        )
        
        # Broadcast to WebSocket clients
        await broadcast_classification(result)
        
        return result.to_dict()
        
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
            resultados.append({
                "cpf": result.cpf,
                "prinad": result.prinad,
                "rating": result.rating,
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
        latencia_media_ms=round(classification_stats["latencia_media_ms"], 2),
        timestamp=datetime.now().isoformat()
    )


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


async def broadcast_classification(result: ClassificationResult):
    """Broadcast classification result to all connected WebSocket clients."""
    if connected_clients:
        message = {
            "type": "new_classification",
            "payload": {
                "cpf": result.cpf[-4:].zfill(4),  # Last 4 digits only for privacy
                "prinad": result.prinad,
                "rating": result.rating,
                "cor": result.cor,
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
