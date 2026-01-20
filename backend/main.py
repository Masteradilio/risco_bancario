# -*- coding: utf-8 -*-
"""
Servidor FastAPI Principal - Sistema de Gestão de Risco Bancário
"""

import os
import sys
from pathlib import Path

# Carregar variáveis de ambiente do .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Importar routers
from agente.agent_api import router as agent_router

app = FastAPI(
    title="Sistema de Gestão de Risco Bancário",
    description="API para PRINAD, ECL, Propensão e Agente IA",
    version="3.0.0"
)

# CORS - Permitir origens do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar routers
app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "message": "Sistema de Gestão de Risco Bancário",
        "version": "3.0.0",
        "modules": ["PRINAD", "ECL", "Propensão", "Agente IA"]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
