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
from datetime import datetime, date
import logging
import sys
import base64
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from perda_esperada.src.pipeline_ecl import ECLPipeline, ECLCompleteResult
from prinad.src.classifier import PRINADClassifier
from perda_esperada.src.modulo_exportacao_bacen import (
    ExportadorBACEN, 
    ConfigExportacao, 
    ResponsavelInfo, 
    OperacaoECL,
    ValidadorXSD,
    MetodologiaApuracao,
    ClassificacaoAtivoFinanceiro
)
from perda_esperada.src.rastreamento_writeoff import (
    RastreadorWriteOff,
    MotivoBaixa,
    StatusRecuperacao,
    RegistroBaixa,
    RegistroRecuperacao,
    ResumoContratoBaixado
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="ECL API",
    description="API de Perda Esperada (ECL) - BACEN 4966 Compliant",
    version="1.1.0",
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
rastreador_writeoff: Optional[RastreadorWriteOff] = None



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
# PYDANTIC MODELS - EXPORTACAO BACEN
# =============================================================================

class ResponsavelRequest(BaseModel):
    """Dados do responsável pelo envio."""
    nome: str = Field(..., description="Nome do responsável")
    email: str = Field(..., description="Email do responsável")
    telefone: str = Field(..., description="Telefone (formato: DDNNNNNNNN)")


class ExportacaoRequest(BaseModel):
    """Request para exportação BACEN Doc3040."""
    data_base: str = Field(..., description="Data-base no formato AAAA-MM")
    cnpj: str = Field(..., description="CNPJ da instituição (8 dígitos)")
    responsavel: ResponsavelRequest
    metodologia: str = Field("C", description="C=Completa, S=Simplificada")
    usar_dados_mock: bool = Field(True, description="Usar dados mockados para teste")


class ErroValidacaoResponse(BaseModel):
    """Erro de validação."""
    codigo: str
    mensagem: str
    linha: Optional[int] = None
    campo: Optional[str] = None


class ValidacaoResponse(BaseModel):
    """Resultado de validação."""
    status: str  # SUCESSO, ERRO, REJEITADO
    valido: bool
    erros: List[ErroValidacaoResponse]
    criticas: List[ErroValidacaoResponse]
    timestamp: str


class ExportacaoResponse(BaseModel):
    """Response da exportação BACEN."""
    sucesso: bool
    arquivo_nome: str
    arquivo_base64: str  # ZIP compactado
    xml_content_base64: str  # XML puro para download direto
    validacao: ValidacaoResponse
    estatisticas: Dict[str, Any]
    timestamp: str


class ValidarXMLRequest(BaseModel):
    """Request para validar XML BACEN."""
    xml_content: str = Field(..., description="Conteúdo XML em base64")


# =============================================================================
# PYDANTIC MODELS - WRITE-OFF (Art. 49 CMN 4966)
# =============================================================================

class WriteoffBaixaRequest(BaseModel):
    """Request para registrar baixa contábil."""
    contrato_id: str = Field(..., description="ID do contrato")
    valor_baixado: float = Field(..., description="Valor a ser baixado")
    motivo: str = Field(..., description="Motivo da baixa (inadimplencia_prolongada, falencia_rj, obito, prescricao, acordo_judicial, cessao, outro)")
    provisao_constituida: float = Field(..., description="Valor da provisão constituída")
    estagio_na_baixa: int = Field(3, description="Estágio IFRS 9 na baixa (1, 2 ou 3)")
    cliente_id: str = Field("", description="ID do cliente")
    produto: str = Field("", description="Produto do contrato")
    observacoes: str = Field("", description="Observações adicionais")


class WriteoffRecuperacaoRequest(BaseModel):
    """Request para registrar recuperação pós-baixa."""
    contrato_id: str = Field(..., description="ID do contrato")
    valor_recuperado: float = Field(..., description="Valor recuperado")
    tipo: str = Field("pagamento", description="Tipo de recuperação (pagamento, acordo, acordo_judicial, leilao_garantia, seguro, outro)")
    observacoes: str = Field("", description="Observações")


class WriteoffBaixaResponse(BaseModel):
    """Response do registro de baixa."""
    sucesso: bool
    contrato_id: str
    valor_baixado: float
    motivo: str
    data_baixa: str
    data_fim_acompanhamento: str
    timestamp: str


class WriteoffRecuperacaoResponse(BaseModel):
    """Response do registro de recuperação."""
    sucesso: bool
    contrato_id: str
    valor_recuperado: float
    total_recuperado: float
    taxa_recuperacao: float
    timestamp: str


class WriteoffResumoResponse(BaseModel):
    """Response do resumo de um contrato baixado."""
    contrato_id: str
    data_baixa: str
    valor_baixado: float
    total_recuperado: float
    taxa_recuperacao: float
    status: str
    dias_desde_baixa: int
    tempo_restante_dias: int
    quantidade_recuperacoes: int


class WriteoffConsolidadoResponse(BaseModel):
    """Response do relatório consolidado de write-offs."""
    quantidade_contratos: int
    contratos_em_acompanhamento: int
    valor_total_baixado: float
    valor_total_recuperado: float
    taxa_recuperacao_media: float
    taxa_recuperacao_ponderada: float
    distribuicao_status: Dict[str, int]
    contratos: List[Dict[str, Any]]
    timestamp: str


class WriteoffTaxaRecuperacaoRequest(BaseModel):
    """Request para filtrar taxa de recuperação."""
    produto: Optional[str] = Field(None, description="Filtrar por produto")
    motivo: Optional[str] = Field(None, description="Filtrar por motivo de baixa")
    periodo_inicial: Optional[str] = Field(None, description="Data inicial (YYYY-MM-DD)")
    periodo_final: Optional[str] = Field(None, description="Data final (YYYY-MM-DD)")


class WriteoffTaxaRecuperacaoResponse(BaseModel):
    """Response da taxa de recuperação histórica."""
    quantidade_contratos: int
    valor_total_baixado: float
    valor_total_recuperado: float
    taxa_recuperacao_media: float
    taxa_recuperacao_ponderada: float
    filtros_aplicados: Dict[str, Any]
    timestamp: str




# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load pipeline and classifier on startup."""
    global pipeline, classifier, rastreador_writeoff
    
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
    
    try:
        rastreador_writeoff = RastreadorWriteOff()
        logger.info("RastreadorWriteOff loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load RastreadorWriteOff: {e}")



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
        version="1.1.0",
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
# ENDPOINTS - EXPORTACAO BACEN
# =============================================================================

def _gerar_operacoes_mock() -> List[OperacaoECL]:
    """
    Gera 50 operações mockadas para teste de exportação.
    Inclui diversidade de produtos, stages e perfis de risco.
    """
    import random
    random.seed(42)  # Para reprodutibilidade
    
    # Configurações base por produto
    produtos_config = {
        "consignado": {
            "taxa_base": 18.5, "lgd_base": 0.35, "modalidade": "0304",
            "saldo_min": 5000, "saldo_max": 100000
        },
        "cartao_credito_rotativo": {
            "taxa_base": 350.0, "lgd_base": 0.80, "modalidade": "0401",
            "saldo_min": 1000, "saldo_max": 50000
        },
        "imobiliario": {
            "taxa_base": 9.5, "lgd_base": 0.10, "modalidade": "0201",
            "saldo_min": 100000, "saldo_max": 800000
        },
        "veiculo": {
            "taxa_base": 24.0, "lgd_base": 0.40, "modalidade": "0501",
            "saldo_min": 20000, "saldo_max": 150000
        },
        "pessoal": {
            "taxa_base": 45.0, "lgd_base": 0.70, "modalidade": "0203",
            "saldo_min": 2000, "saldo_max": 30000
        },
        "cheque_especial": {
            "taxa_base": 150.0, "lgd_base": 0.85, "modalidade": "0402",
            "saldo_min": 500, "saldo_max": 15000
        },
    }
    
    # Ratings e suas PDs base
    ratings_pd = {
        "A1": 0.005, "A2": 0.01, "A3": 0.02,
        "B1": 0.03, "B2": 0.05, "B3": 0.08,
        "C1": 0.12, "C2": 0.18, "C3": 0.25,
        "D": 0.35, "E": 0.50, "F": 0.70, "G": 0.85, "H": 0.95
    }
    
    operacoes = []
    
    # Gerar 50 operações
    for i in range(50):
        # CPF fictício
        cpf = str(10000000000 + i * 123456789 % 90000000000).zfill(11)
        
        # Selecionar produto
        produto = random.choice(list(produtos_config.keys()))
        config_prod = produtos_config[produto]
        
        # Gerar contrato
        contrato = f"{produto[:4].upper()}{2024}{str(i+1).zfill(5)}"
        
        # Valores
        saldo = round(random.uniform(config_prod["saldo_min"], config_prod["saldo_max"]), 2)
        limite = round(saldo * random.uniform(1.0, 1.5), 2)
        
        # Determinar stage e dias de atraso
        stage_choice = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        if stage_choice == 1:
            dias_atraso = random.randint(0, 15)
            rating = random.choice(["A1", "A2", "A3", "B1"])
        elif stage_choice == 2:
            dias_atraso = random.randint(16, 90)
            rating = random.choice(["B2", "B3", "C1", "C2"])
        else:
            dias_atraso = random.randint(91, 365)
            rating = random.choice(["C3", "D", "E", "F", "G", "H"])
        
        # Calcular PD e ECL
        pd_base = ratings_pd[rating]
        pd_ajustado = min(pd_base * (1 + dias_atraso * 0.005), 1.0)
        lgd = config_prod["lgd_base"]
        ead = saldo * random.uniform(1.0, 1.2)
        ecl = round(pd_ajustado * lgd * ead, 2)
        
        # Datas
        anos_antes = random.randint(1, 5)
        data_contratacao = date(2024 - anos_antes, random.randint(1, 12), random.randint(1, 28))
        prazo_anos = random.randint(1, 20) if produto == "imobiliario" else random.randint(1, 5)
        data_vencimento = date(2024 + prazo_anos, random.randint(1, 12), random.randint(1, 28))
        
        operacoes.append(OperacaoECL(
            cliente_id=cpf,
            contrato=contrato,
            produto=produto,
            saldo_utilizado=saldo,
            limite_total=limite,
            pd_ajustado=round(pd_ajustado, 4),
            lgd_final=lgd,
            ead=round(ead, 2),
            ecl_final=ecl,
            estagio_ifrs9=stage_choice,
            rating=rating,
            dias_atraso=dias_atraso,
            data_contratacao=data_contratacao,
            data_vencimento=data_vencimento,
            taxa_juros_efetiva=config_prod["taxa_base"] * random.uniform(0.9, 1.1)
        ))
    
    return operacoes


@app.post("/exportar_bacen", response_model=ExportacaoResponse, tags=["Regulatório BACEN"])
async def exportar_bacen(request: ExportacaoRequest):
    """
    Gera arquivo XML Doc3040 para exportação ao BACEN.
    
    O arquivo é gerado conforme Resolução CMN 4966/2021 com a tag
    ContInstFinRes4966 para dados de ECL.
    
    Returns:
        ZIP contendo XML Doc3040 em base64
    """
    try:
        # Parse data-base
        ano, mes = request.data_base.split("-")
        data_base = date(int(ano), int(mes), 1)
        # Ajustar para último dia do mês
        if mes == "12":
            data_base = date(int(ano), 12, 31)
        else:
            data_base = date(int(ano), int(mes) + 1, 1) 
            from datetime import timedelta
            data_base = data_base - timedelta(days=1)
        
        # Configuração
        config = ConfigExportacao(
            cnpj=request.cnpj.zfill(8)[:8],
            responsavel=ResponsavelInfo(
                nome=request.responsavel.nome,
                email=request.responsavel.email,
                telefone=request.responsavel.telefone
            ),
            metodologia=MetodologiaApuracao.COMPLETA if request.metodologia == "C" else MetodologiaApuracao.SIMPLIFICADA
        )
        
        # Obter operações (mock ou reais)
        if request.usar_dados_mock:
            operacoes = _gerar_operacoes_mock()
        else:
            # TODO: Integrar com dados reais do sistema
            operacoes = _gerar_operacoes_mock()
        
        # Gerar exportação
        exportador = ExportadorBACEN(config)
        result = exportador.exportar(
            operacoes=operacoes,
            data_base=data_base
        )
        
        # Converter ZIP para base64
        arquivo_base64 = base64.b64encode(result.arquivo_conteudo).decode('utf-8')
        
        # Converter erros para response
        erros = [
            ErroValidacaoResponse(
                codigo=e.codigo,
                mensagem=e.mensagem,
                linha=e.linha,
                campo=e.campo
            )
            for e in result.validacao.erros
        ]
        
        criticas = [
            ErroValidacaoResponse(
                codigo=c.codigo,
                mensagem=c.mensagem,
                linha=c.linha,
                campo=c.campo
            )
            for c in result.validacao.criticas
        ]
        
        # Converter XML para base64 para download direto
        xml_base64 = base64.b64encode(result.xml_content.encode('utf-8')).decode('utf-8')
        
        return ExportacaoResponse(
            sucesso=result.sucesso,
            arquivo_nome=result.arquivo_nome,
            arquivo_base64=arquivo_base64,
            xml_content_base64=xml_base64,
            validacao=ValidacaoResponse(
                status=result.validacao.status,
                valido=result.validacao.valido,
                erros=erros,
                criticas=criticas,
                timestamp=result.validacao.timestamp.isoformat()
            ),
            estatisticas={
                "total_clientes": result.total_clientes,
                "total_operacoes": result.total_operacoes,
                "ecl_total": result.ecl_total,
                "data_base": data_base.isoformat(),
                "metodologia": request.metodologia
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro na exportação BACEN: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validar_bacen", response_model=ValidacaoResponse, tags=["Regulatório BACEN"])
async def validar_xml_bacen(request: ValidarXMLRequest):
    """
    Valida arquivo XML Doc3040 contra schema e regras BACEN.
    
    Args:
        xml_content: Conteúdo XML codificado em base64
        
    Returns:
        Resultado da validação com status e erros
    """
    try:
        # Decodificar base64
        xml_content = base64.b64decode(request.xml_content).decode('utf-8')
        
        # Validar
        validador = ValidadorXSD()
        result = validador.validar(xml_content)
        
        # Converter erros
        erros = [
            ErroValidacaoResponse(
                codigo=e.codigo,
                mensagem=e.mensagem,
                linha=e.linha,
                campo=e.campo
            )
            for e in result.erros
        ]
        
        criticas = [
            ErroValidacaoResponse(
                codigo=c.codigo,
                mensagem=c.mensagem,
                linha=c.linha,
                campo=c.campo
            )
            for c in result.criticas
        ]
        
        return ValidacaoResponse(
            status=result.status,
            valido=result.valido,
            erros=erros,
            criticas=criticas,
            timestamp=result.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro na validação BACEN: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINTS - WRITE-OFF (Art. 49 CMN 4966)
# =============================================================================

@app.post("/writeoff/registrar-baixa", response_model=WriteoffBaixaResponse, tags=["Write-off"])
async def registrar_baixa(request: WriteoffBaixaRequest):
    """
    Registra uma baixa contábil (write-off).
    
    Inicia o acompanhamento de 5 anos conforme Art. 49 CMN 4966.
    """
    if not rastreador_writeoff:
        raise HTTPException(status_code=503, detail="RastreadorWriteOff não carregado")
    
    try:
        # Converter motivo
        motivo_map = {
            'inadimplencia_prolongada': MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            'falencia_rj': MotivoBaixa.FALENCIA_RECUPERACAO_JUDICIAL,
            'obito': MotivoBaixa.OBITO_SEM_ESPÓLIO,
            'prescricao': MotivoBaixa.PRESCRICAO,
            'acordo_judicial': MotivoBaixa.ACORDO_JUDICIAL,
            'cessao': MotivoBaixa.CESSAO_CREDITO,
            'outro': MotivoBaixa.OUTRO
        }
        motivo = motivo_map.get(request.motivo, MotivoBaixa.OUTRO)
        
        registro = rastreador_writeoff.registrar_baixa(
            contrato_id=request.contrato_id,
            valor_baixado=request.valor_baixado,
            motivo=motivo,
            provisao_constituida=request.provisao_constituida,
            estagio_na_baixa=request.estagio_na_baixa,
            cliente_id=request.cliente_id,
            produto=request.produto,
            observacoes=request.observacoes
        )
        
        from datetime import timedelta
        data_fim = registro.data_baixa + timedelta(days=5*365)
        
        return WriteoffBaixaResponse(
            sucesso=True,
            contrato_id=registro.contrato_id,
            valor_baixado=registro.valor_baixado,
            motivo=registro.motivo.value,
            data_baixa=registro.data_baixa.isoformat(),
            data_fim_acompanhamento=data_fim.isoformat(),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao registrar baixa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/writeoff/registrar-recuperacao", response_model=WriteoffRecuperacaoResponse, tags=["Write-off"])
async def registrar_recuperacao(request: WriteoffRecuperacaoRequest):
    """
    Registra uma recuperação pós-baixa.
    
    Acumula valores recuperados no período de 5 anos.
    """
    if not rastreador_writeoff:
        raise HTTPException(status_code=503, detail="RastreadorWriteOff não carregado")
    
    try:
        recuperacao = rastreador_writeoff.registrar_recuperacao(
            contrato_id=request.contrato_id,
            valor_recuperado=request.valor_recuperado,
            tipo=request.tipo,
            observacoes=request.observacoes
        )
        
        if not recuperacao:
            raise HTTPException(status_code=404, detail=f"Contrato {request.contrato_id} não possui baixa registrada")
        
        resumo = rastreador_writeoff.obter_resumo_contrato(request.contrato_id)
        
        return WriteoffRecuperacaoResponse(
            sucesso=True,
            contrato_id=request.contrato_id,
            valor_recuperado=request.valor_recuperado,
            total_recuperado=resumo.total_recuperado if resumo else request.valor_recuperado,
            taxa_recuperacao=resumo.taxa_recuperacao if resumo else 0,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar recuperação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/writeoff/relatorio/{contrato_id}", response_model=WriteoffResumoResponse, tags=["Write-off"])
async def obter_relatorio_contrato(contrato_id: str):
    """
    Obtém relatório de acompanhamento de um contrato baixado.
    """
    if not rastreador_writeoff:
        raise HTTPException(status_code=503, detail="RastreadorWriteOff não carregado")
    
    try:
        resumo = rastreador_writeoff.obter_resumo_contrato(contrato_id)
        
        if not resumo:
            raise HTTPException(status_code=404, detail=f"Contrato {contrato_id} não encontrado")
        
        return WriteoffResumoResponse(
            contrato_id=resumo.contrato_id,
            data_baixa=resumo.data_baixa.isoformat(),
            valor_baixado=resumo.valor_baixado,
            total_recuperado=resumo.total_recuperado,
            taxa_recuperacao=resumo.taxa_recuperacao,
            status=resumo.status.value,
            dias_desde_baixa=resumo.dias_desde_baixa,
            tempo_restante_dias=resumo.tempo_restante_dias,
            quantidade_recuperacoes=len(resumo.recuperacoes)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/writeoff/relatorio-consolidado", response_model=WriteoffConsolidadoResponse, tags=["Write-off"])
async def obter_relatorio_consolidado():
    """
    Obtém relatório consolidado de todos os write-offs.
    
    Inclui contratos em acompanhamento (últimos 5 anos).
    """
    if not rastreador_writeoff:
        raise HTTPException(status_code=503, detail="RastreadorWriteOff não carregado")
    
    try:
        estatisticas = rastreador_writeoff.calcular_taxa_recuperacao_historica()
        contratos_ativos = rastreador_writeoff.obter_contratos_em_acompanhamento()
        
        return WriteoffConsolidadoResponse(
            quantidade_contratos=estatisticas.get('quantidade_contratos', 0),
            contratos_em_acompanhamento=len(contratos_ativos),
            valor_total_baixado=estatisticas.get('valor_total_baixado', 0),
            valor_total_recuperado=estatisticas.get('valor_total_recuperado', 0),
            taxa_recuperacao_media=estatisticas.get('taxa_recuperacao_media', 0),
            taxa_recuperacao_ponderada=estatisticas.get('taxa_recuperacao_ponderada', 0),
            distribuicao_status=estatisticas.get('distribuicao_status', {}),
            contratos=[c.to_dict() for c in contratos_ativos[:50]],  # Top 50
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter relatório consolidado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/writeoff/taxa-recuperacao", response_model=WriteoffTaxaRecuperacaoResponse, tags=["Write-off"])
async def calcular_taxa_recuperacao(request: WriteoffTaxaRecuperacaoRequest):
    """
    Calcula taxa de recuperação histórica com filtros opcionais.
    
    Permite filtrar por produto, motivo e período.
    """
    if not rastreador_writeoff:
        raise HTTPException(status_code=503, detail="RastreadorWriteOff não carregado")
    
    try:
        # Converter motivo se fornecido
        motivo = None
        if request.motivo:
            motivo_map = {
                'inadimplencia_prolongada': MotivoBaixa.INADIMPLENCIA_PROLONGADA,
                'falencia_rj': MotivoBaixa.FALENCIA_RECUPERACAO_JUDICIAL,
                'obito': MotivoBaixa.OBITO_SEM_ESPÓLIO,
                'prescricao': MotivoBaixa.PRESCRICAO,
                'acordo_judicial': MotivoBaixa.ACORDO_JUDICIAL,
                'cessao': MotivoBaixa.CESSAO_CREDITO,
                'outro': MotivoBaixa.OUTRO
            }
            motivo = motivo_map.get(request.motivo)
        
        # Converter datas se fornecidas
        periodo_inicial = None
        periodo_final = None
        if request.periodo_inicial:
            periodo_inicial = datetime.fromisoformat(request.periodo_inicial)
        if request.periodo_final:
            periodo_final = datetime.fromisoformat(request.periodo_final)
        
        estatisticas = rastreador_writeoff.calcular_taxa_recuperacao_historica(
            produto=request.produto,
            motivo=motivo,
            periodo_inicial=periodo_inicial,
            periodo_final=periodo_final
        )
        
        return WriteoffTaxaRecuperacaoResponse(
            quantidade_contratos=estatisticas.get('quantidade_contratos', 0),
            valor_total_baixado=estatisticas.get('valor_total_baixado', 0),
            valor_total_recuperado=estatisticas.get('valor_total_recuperado', 0),
            taxa_recuperacao_media=estatisticas.get('taxa_recuperacao_media', 0),
            taxa_recuperacao_ponderada=estatisticas.get('taxa_recuperacao_ponderada', 0),
            filtros_aplicados={
                'produto': request.produto,
                'motivo': request.motivo,
                'periodo_inicial': request.periodo_inicial,
                'periodo_final': request.periodo_final
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao calcular taxa de recuperação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

