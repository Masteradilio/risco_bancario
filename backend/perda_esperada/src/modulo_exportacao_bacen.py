#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Exportação Regulatória BACEN - Doc3040
=================================================

Gera arquivos XML no formato Doc3040 do Sistema de Informações de Crédito (SCR)
conforme Resolução CMN 4966/2021 e Instrução Normativa BCB 414.

Funcionalidades:
- Geração de XML Doc3040 com tag ContInstFinRes4966
- Validação contra schema XSD oficial
- Compactação ZIP para envio via STA
- Particionamento de arquivos grandes

Referências:
- https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040
- SCR3040_Leiaute.xls
- SCR_InstrucoesDePreenchimento_Doc3040.pdf

Autor: Sistema ECL
Data: Janeiro 2025
"""

import os
import io
import zipfile
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from xml.etree import ElementTree as ET
from xml.dom import minidom
import hashlib
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

class MetodologiaApuracao(Enum):
    """Metodologia de apuração de perdas esperadas."""
    COMPLETA = "C"
    SIMPLIFICADA = "S"


class ClassificacaoAtivoFinanceiro(Enum):
    """Categoria contábil do instrumento financeiro."""
    CUSTO_AMORTIZADO = "1"
    VJORA = "2"  # Valor Justo por Outros Resultados Abrangentes
    VJR = "3"    # Valor Justo por Resultado


class CarteiraProvisaoMinima(Enum):
    """Carteira para fins de provisão mínima (Res. BCB 352)."""
    C1 = "C1"  # Até 15 dias
    C2 = "C2"  # 16 a 30 dias
    C3 = "C3"  # 31 a 60 dias
    C4 = "C4"  # 61 a 90 dias
    C5 = "C5"  # Acima de 90 dias


class MotivoAlocacaoEstagio(Enum):
    """Motivos de alocação em estágios (Art. 37-39 Res. 4966)."""
    RISCO_NAO_AUMENTOU = "01"           # Estágio 1
    AUMENTO_SIGNIFICATIVO = "02"         # Estágio 2
    DETERIORACAO_CREDITICIA = "03"       # Estágio 3


class MotivoDaPerda(Enum):
    """Motivos de reconhecimento de perda."""
    REESTRUTURACAO = "1"
    ABATIMENTO_CONCESSAO = "2"
    OUTRO_MOTIVO = "3"


# Mapeamento de produtos para modalidade SCR
MAPEAMENTO_MODALIDADE_SCR = {
    "consignado": "0304",
    "cartao_credito_rotativo": "0401",
    "imobiliario": "0201",
    "veiculo": "0501",
    "energia_solar": "0206",
    "pessoal": "0203",
    "cheque_especial": "0402",
}

# Mapeamento de dias de atraso para carteira de provisão mínima
def obter_carteira_provisao(dias_atraso: int) -> CarteiraProvisaoMinima:
    """Determina a carteira de provisão mínima baseado nos dias de atraso."""
    if dias_atraso <= 15:
        return CarteiraProvisaoMinima.C1
    elif dias_atraso <= 30:
        return CarteiraProvisaoMinima.C2
    elif dias_atraso <= 60:
        return CarteiraProvisaoMinima.C3
    elif dias_atraso <= 90:
        return CarteiraProvisaoMinima.C4
    else:
        return CarteiraProvisaoMinima.C5


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ResponsavelInfo:
    """Informações do responsável pelo envio."""
    nome: str
    email: str
    telefone: str


@dataclass
class ConfigExportacao:
    """Configuração para exportação BACEN."""
    cnpj: str  # 8 dígitos
    responsavel: ResponsavelInfo
    metodologia: MetodologiaApuracao = MetodologiaApuracao.COMPLETA
    metodologia_diferenciada_tje: bool = False


@dataclass
class ClienteInfo:
    """Informações do cliente para exportação."""
    tipo: str  # "1" = PF, "2" = PJ
    codigo: str  # CPF (11 dígitos) ou CNPJ raiz (8 dígitos)
    autorizado: bool = True
    porte: str = "1"  # 1=Grande, 2=Médio, 3=Pequeno, 4=Micro
    tipo_controle: str = "01"
    inicio_relacionamento: Optional[date] = None
    faturamento_anual: Optional[float] = None
    conglomerado_economico: str = "000000"


@dataclass
class OperacaoECL:
    """Dados de uma operação de crédito com ECL calculado."""
    # Identificação
    cliente_id: str
    contrato: str
    produto: str
    
    # Valores
    saldo_utilizado: float
    limite_total: float
    
    # ECL calculado
    pd_ajustado: float
    lgd_final: float
    ead: float
    ecl_final: float
    
    # Classificação
    estagio_ifrs9: int  # 1, 2 ou 3
    rating: str
    dias_atraso: int = 0
    
    # Datas
    data_contratacao: Optional[date] = None
    data_vencimento: Optional[date] = None
    
    # Opcionais
    taxa_juros_efetiva: float = 0.0
    classificacao_ativo: ClassificacaoAtivoFinanceiro = ClassificacaoAtivoFinanceiro.CUSTO_AMORTIZADO
    grupo_homogeneo: str = "GH1"
    piso_aplicado: bool = False
    
    # Metadados
    cosif: str = "1.6.2.10.01.10-2"
    cep: str = "01310100"
    natureza_operacao: str = "01"
    origem_recursos: str = "0101"
    indexador: str = "01"
    variacao_cambial: str = "978"  # BRL


@dataclass
class ValidacaoErro:
    """Erro de validação."""
    codigo: str
    mensagem: str
    linha: Optional[int] = None
    campo: Optional[str] = None


@dataclass
class ValidacaoResult:
    """Resultado de validação."""
    status: str  # "SUCESSO", "ERRO", "REJEITADO"
    valido: bool
    erros: List[ValidacaoErro] = field(default_factory=list)
    criticas: List[ValidacaoErro] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExportacaoResult:
    """Resultado da exportação."""
    sucesso: bool
    arquivo_nome: str
    arquivo_conteudo: bytes  # ZIP
    xml_content: str  # XML puro
    validacao: ValidacaoResult
    total_clientes: int
    total_operacoes: int
    ecl_total: float
    data_geracao: datetime = field(default_factory=datetime.now)


# =============================================================================
# CLASSE PRINCIPAL: ExportadorBACEN
# =============================================================================

class ExportadorBACEN:
    """
    Gera arquivo XML Doc3040 com dados ECL conforme Resolução CMN 4966/2021.
    
    Uso:
        exportador = ExportadorBACEN(config)
        result = exportador.exportar(operacoes, data_base=date(2025, 1, 31))
    """
    
    # Namespace e versão
    XML_VERSION = "1.0"
    XML_ENCODING = "UTF-8"
    
    def __init__(self, config: ConfigExportacao):
        """
        Inicializa o exportador.
        
        Args:
            config: Configuração com CNPJ, responsável e metodologia.
        """
        self.config = config
        self._validar_config()
    
    def _validar_config(self):
        """Valida configuração."""
        if len(self.config.cnpj) != 8:
            raise ValueError(f"CNPJ deve ter 8 dígitos, recebido: {self.config.cnpj}")
        if not self.config.cnpj.isdigit():
            raise ValueError("CNPJ deve conter apenas dígitos")
    
    def exportar(
        self,
        operacoes: List[OperacaoECL],
        data_base: date,
        remessa: int = 1,
        parte: int = 1,
        ultima_parte: bool = True
    ) -> ExportacaoResult:
        """
        Gera arquivo de exportação completo.
        
        Args:
            operacoes: Lista de operações com ECL calculado
            data_base: Data-base da remessa (último dia do mês)
            remessa: Número sequencial da remessa
            parte: Número da parte (para arquivos particionados)
            ultima_parte: Se esta é a última parte
            
        Returns:
            ExportacaoResult com arquivo ZIP e estatísticas
        """
        logger.info(f"Iniciando exportação BACEN - Data-base: {data_base}")
        
        # Agrupar operações por cliente
        operacoes_por_cliente = self._agrupar_por_cliente(operacoes)
        
        # Gerar XML
        xml_content = self._gerar_xml(
            operacoes_por_cliente,
            data_base,
            remessa,
            parte,
            ultima_parte
        )
        
        # Validar XML
        validacao = self.validar_xml(xml_content)
        
        # Gerar estatísticas
        ecl_total = sum(op.ecl_final for op in operacoes)
        
        # Compactar
        filename = f"Doc3040_{self.config.cnpj}_{data_base.strftime('%Y%m')}_R{remessa}P{parte}.xml"
        zip_content = self._compactar_zip(xml_content, filename)
        
        logger.info(f"Exportação concluída: {len(operacoes)} operações, ECL Total: R$ {ecl_total:,.2f}")
        
        return ExportacaoResult(
            sucesso=validacao.valido,
            arquivo_nome=filename.replace('.xml', '.zip'),
            arquivo_conteudo=zip_content,
            xml_content=xml_content,
            validacao=validacao,
            total_clientes=len(operacoes_por_cliente),
            total_operacoes=len(operacoes),
            ecl_total=ecl_total
        )
    
    def _agrupar_por_cliente(self, operacoes: List[OperacaoECL]) -> Dict[str, List[OperacaoECL]]:
        """Agrupa operações por cliente."""
        resultado = {}
        for op in operacoes:
            if op.cliente_id not in resultado:
                resultado[op.cliente_id] = []
            resultado[op.cliente_id].append(op)
        return resultado
    
    def _gerar_xml(
        self,
        operacoes_por_cliente: Dict[str, List[OperacaoECL]],
        data_base: date,
        remessa: int,
        parte: int,
        ultima_parte: bool
    ) -> str:
        """Gera conteúdo XML Doc3040."""
        
        # Criar elemento raiz
        root = ET.Element("Doc3040")
        
        # Atributos do cabeçalho
        root.set("CNPJ", self.config.cnpj)
        root.set("DtBase", data_base.strftime("%Y-%m"))
        root.set("Remessa", str(remessa))
        root.set("Parte", str(parte))
        root.set("TpArq", "F" if ultima_parte else "")
        root.set("NomeResp", self.config.responsavel.nome)
        root.set("EmailResp", self.config.responsavel.email)
        root.set("TelResp", self.config.responsavel.telefone.replace("-", "").replace(" ", ""))
        root.set("TotalCli", str(len(operacoes_por_cliente)))
        root.set("MetodApPE", self.config.metodologia.value)
        root.set("MetodDifTJE", "S" if self.config.metodologia_diferenciada_tje else "N")
        
        # Adicionar clientes e operações
        for cliente_id, operacoes in operacoes_por_cliente.items():
            cli_element = self._criar_elemento_cliente(cliente_id, operacoes)
            root.append(cli_element)
        
        # Formatar XML
        xml_string = ET.tostring(root, encoding='unicode')
        
        # Adicionar declaração XML e formatar
        xml_declaration = f'<?xml version="{self.XML_VERSION}" encoding="{self.XML_ENCODING}"?>\n'
        
        # Pretty print
        try:
            dom = minidom.parseString(xml_string)
            formatted = dom.toprettyxml(indent="  ")
            # Remover declaração duplicada
            lines = formatted.split('\n')[1:]  # Remove primeira linha (declaração)
            xml_content = xml_declaration + '\n'.join(lines)
        except Exception:
            xml_content = xml_declaration + xml_string
        
        return xml_content
    
    def _criar_elemento_cliente(self, cliente_id: str, operacoes: List[OperacaoECL]) -> ET.Element:
        """Cria elemento <Cli> com dados do cliente."""
        
        # Determinar tipo (PF ou PJ)
        tipo = "1" if len(cliente_id.replace(".", "").replace("-", "")) == 11 else "2"
        codigo = cliente_id.replace(".", "").replace("-", "")[:8] if tipo == "2" else cliente_id.replace(".", "").replace("-", "")
        
        cli = ET.Element("Cli")
        cli.set("Tp", tipo)
        cli.set("Cd", codigo.zfill(11 if tipo == "1" else 8))
        cli.set("Autorzc", "S")
        cli.set("PorteCli", "3")  # Pequeno (padrão)
        cli.set("TpCtrl", "01")
        cli.set("IniRelactCli", operacoes[0].data_contratacao.strftime("%Y-%m-%d") if operacoes[0].data_contratacao else "2020-01-01")
        cli.set("CongEcon", "000000")
        
        # Adicionar operações
        for op in operacoes:
            op_element = self._criar_elemento_operacao(op)
            cli.append(op_element)
        
        return cli
    
    def _criar_elemento_operacao(self, op: OperacaoECL) -> ET.Element:
        """Cria elemento <Op> com ContInstFinRes4966."""
        
        # Obter modalidade SCR
        modalidade = MAPEAMENTO_MODALIDADE_SCR.get(op.produto, "0203")
        
        # Gerar IPOC único
        ipoc = self._gerar_ipoc(op, modalidade)
        
        op_elem = ET.Element("Op")
        op_elem.set("DetCli", op.cliente_id.replace(".", "").replace("-", "").zfill(14))
        op_elem.set("Contrt", op.contrato[:50])
        op_elem.set("NatuOp", op.natureza_operacao)
        op_elem.set("Mod", modalidade)
        op_elem.set("OrigemRec", op.origem_recursos)
        op_elem.set("Indx", op.indexador)
        op_elem.set("VarCamb", op.variacao_cambial)
        op_elem.set("DtVencOp", op.data_vencimento.strftime("%Y-%m-%d") if op.data_vencimento else "2030-12-31")
        op_elem.set("CEP", op.cep)
        op_elem.set("TaxEft", f"{op.taxa_juros_efetiva:.2f}")
        op_elem.set("DtContr", op.data_contratacao.strftime("%Y-%m-%d") if op.data_contratacao else "2024-01-01")
        op_elem.set("ProvConsttd", f"{op.ecl_final:.2f}")
        op_elem.set("Cosif", op.cosif)
        op_elem.set("IPOC", ipoc)
        
        # Adicionar vencimentos (simplificado)
        venc = ET.SubElement(op_elem, "Venc")
        venc.set("v110", f"{op.saldo_utilizado:.2f}")
        
        # Adicionar ContInstFinRes4966 (ECL)
        ecl_elem = self._criar_elemento_ecl(op)
        op_elem.append(ecl_elem)
        
        return op_elem
    
    def _criar_elemento_ecl(self, op: OperacaoECL) -> ET.Element:
        """Cria elemento <ContInstFinRes4966> com dados ECL."""
        
        # Carteira de provisão mínima
        carteira = obter_carteira_provisao(op.dias_atraso)
        
        # Valor justo = bruto - provisão
        valor_justo = op.saldo_utilizado - op.ecl_final
        
        # Renda do mês (simplificado: taxa mensal * saldo)
        taxa_mensal = op.taxa_juros_efetiva / 12 / 100
        renda_mes = op.saldo_utilizado * taxa_mensal
        
        ecl = ET.Element("ContInstFinRes4966")
        ecl.set("ClassificacaoAtivoFinanceiro", op.classificacao_ativo.value)
        ecl.set("EstagioDo", str(op.estagio_ifrs9))
        ecl.set("QtdTitulos", "1")
        ecl.set("VlrContabilBruto", f"{op.saldo_utilizado:.2f}")
        ecl.set("VlrPerdaAcumulada", f"{op.ecl_final:.2f}")
        ecl.set("VlrJusto", f"{valor_justo:.2f}")
        ecl.set("TaxaJurosEfetiva", f"{op.taxa_juros_efetiva:.2f}")
        ecl.set("RendaMes", f"{renda_mes:.2f}")
        ecl.set("AlocacaoEstag1", "01" if op.estagio_ifrs9 == 1 else "05")
        ecl.set("CarteiraProvisaoMin", carteira.value)
        ecl.set("TratRiscoCredito", "01")
        
        # Elemento de estágio
        estagio = ET.SubElement(ecl, "Estagio")
        motivo = MotivoAlocacaoEstagio.RISCO_NAO_AUMENTOU if op.estagio_ifrs9 == 1 \
            else MotivoAlocacaoEstagio.AUMENTO_SIGNIFICATIVO if op.estagio_ifrs9 == 2 \
            else MotivoAlocacaoEstagio.DETERIORACAO_CREDITICIA
        estagio.set("MotivoAlocacao", motivo.value)
        estagio.set("DataBaseAlocacao", datetime.now().strftime("%Y-%m-%d"))
        
        # Elemento de perda (se houver)
        if op.ecl_final > 0 and op.estagio_ifrs9 >= 2:
            perda = ET.SubElement(ecl, "Perda")
            perda.set("MotivoDaPerda", MotivoDaPerda.OUTRO_MOTIVO.value)
            perda.set("VlrPerda", f"{op.ecl_final / 2:.2f}")  # Metade como perda reconhecida
        
        return ecl
    
    def _gerar_ipoc(self, op: OperacaoECL, modalidade: str) -> str:
        """Gera IPOC único para a operação."""
        # IPOC = CNPJ(8) + Modalidade(4) + TipoCliente(1) + CódigoCliente(14) + Contrato
        tipo = "1" if len(op.cliente_id.replace(".", "").replace("-", "")) <= 11 else "2"
        codigo = op.cliente_id.replace(".", "").replace("-", "").zfill(14)
        contrato = op.contrato[:20]
        
        ipoc = f"{self.config.cnpj}{modalidade}{tipo}{codigo}{contrato}"
        return ipoc[:50]  # Limitar a 50 caracteres
    
    def validar_xml(self, xml_content: str) -> ValidacaoResult:
        """
        Valida XML contra regras básicas.
        
        Para validação completa com XSD, usar ValidadorXSD.
        """
        erros = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Verificar tag raiz
            if root.tag != "Doc3040":
                erros.append(ValidacaoErro(
                    codigo="E001",
                    mensagem="Tag raiz deve ser 'Doc3040'",
                    campo="root"
                ))
            
            # Verificar atributos obrigatórios
            atributos_obrigatorios = ["CNPJ", "DtBase", "Remessa", "NomeResp", "EmailResp"]
            for attr in atributos_obrigatorios:
                if not root.get(attr):
                    erros.append(ValidacaoErro(
                        codigo="E002",
                        mensagem=f"Atributo obrigatório ausente: {attr}",
                        campo=attr
                    ))
            
            # Verificar clientes
            clientes = root.findall("Cli")
            if not clientes:
                erros.append(ValidacaoErro(
                    codigo="E003",
                    mensagem="Nenhum cliente (<Cli>) encontrado no documento",
                    campo="Cli"
                ))
            
            # Verificar ContInstFinRes4966 em cada operação
            for cli in clientes:
                for op in cli.findall("Op"):
                    ecl = op.find("ContInstFinRes4966")
                    if ecl is None:
                        erros.append(ValidacaoErro(
                            codigo="E004",
                            mensagem=f"Operação sem ContInstFinRes4966",
                            campo="ContInstFinRes4966",
                            linha=None
                        ))
                    else:
                        # Verificar campos ECL
                        campos_ecl = ["EstagioDo", "VlrContabilBruto", "VlrPerdaAcumulada"]
                        for campo in campos_ecl:
                            if not ecl.get(campo):
                                erros.append(ValidacaoErro(
                                    codigo="E005",
                                    mensagem=f"Campo ECL obrigatório ausente: {campo}",
                                    campo=campo
                                ))
        
        except ET.ParseError as e:
            erros.append(ValidacaoErro(
                codigo="E000",
                mensagem=f"Erro de parse XML: {str(e)}",
                linha=e.position[0] if hasattr(e, 'position') else None
            ))
        
        # Determinar status
        if not erros:
            status = "SUCESSO"
            valido = True
        else:
            status = "ERRO" if any(e.codigo.startswith("E0") for e in erros) else "REJEITADO"
            valido = False
        
        return ValidacaoResult(
            status=status,
            valido=valido,
            erros=erros
        )
    
    def _compactar_zip(self, xml_content: str, filename: str) -> bytes:
        """Compacta XML em arquivo ZIP."""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename, xml_content.encode('utf-8'))
        
        return buffer.getvalue()


# =============================================================================
# CLASSE: ValidadorXSD
# =============================================================================

class ValidadorXSD:
    """
    Valida XML Doc3040 contra schema XSD oficial do BACEN.
    
    Nota: Para validação completa, é necessário baixar o XSD oficial de:
    https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040
    """
    
    def __init__(self, xsd_path: Optional[str] = None):
        """
        Inicializa o validador.
        
        Args:
            xsd_path: Caminho para arquivo XSD (opcional)
        """
        self.xsd_path = xsd_path
        self._schema = None
        
        if xsd_path and os.path.exists(xsd_path):
            self._carregar_schema()
    
    def _carregar_schema(self):
        """Carrega schema XSD."""
        try:
            from lxml import etree
            with open(self.xsd_path, 'rb') as f:
                schema_doc = etree.parse(f)
                self._schema = etree.XMLSchema(schema_doc)
            logger.info(f"Schema XSD carregado: {self.xsd_path}")
        except ImportError:
            logger.warning("lxml não disponível, validação XSD desabilitada")
        except Exception as e:
            logger.error(f"Erro ao carregar schema: {e}")
    
    def validar(self, xml_content: str) -> ValidacaoResult:
        """
        Valida XML contra schema XSD.
        
        Args:
            xml_content: Conteúdo XML como string
            
        Returns:
            ValidacaoResult com status e erros
        """
        erros = []
        
        # Validação básica sem lxml
        if self._schema is None:
            return self._validar_basico(xml_content)
        
        try:
            from lxml import etree
            
            # Parse document
            doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # Validar contra schema
            if self._schema.validate(doc):
                return ValidacaoResult(
                    status="SUCESSO",
                    valido=True
                )
            else:
                for error in self._schema.error_log:
                    erros.append(ValidacaoErro(
                        codigo=f"XSD-{error.type}",
                        mensagem=error.message,
                        linha=error.line,
                        campo=None
                    ))
                
                return ValidacaoResult(
                    status="ERRO",
                    valido=False,
                    erros=erros
                )
        
        except Exception as e:
            return ValidacaoResult(
                status="ERRO",
                valido=False,
                erros=[ValidacaoErro(
                    codigo="XSD-PARSE",
                    mensagem=str(e)
                )]
            )
    
    def _validar_basico(self, xml_content: str) -> ValidacaoResult:
        """Validação básica sem XSD."""
        erros = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Regras de crítica semântica (SCR3040_Criticas.xls)
            for cli in root.findall("Cli"):
                for op in cli.findall("Op"):
                    ecl = op.find("ContInstFinRes4966")
                    if ecl is not None:
                        # Crítica: VlrContabilBruto >= VlrPerdaAcumulada
                        bruto = float(ecl.get("VlrContabilBruto", "0"))
                        perda = float(ecl.get("VlrPerdaAcumulada", "0"))
                        
                        if perda > bruto:
                            erros.append(ValidacaoErro(
                                codigo="CRIT-001",
                                mensagem="VlrPerdaAcumulada não pode ser maior que VlrContabilBruto",
                                campo="VlrPerdaAcumulada"
                            ))
                        
                        # Crítica: Estágio válido
                        estagio = ecl.get("EstagioDo", "0")
                        if estagio not in ["1", "2", "3"]:
                            erros.append(ValidacaoErro(
                                codigo="CRIT-002",
                                mensagem=f"Estágio inválido: {estagio}. Deve ser 1, 2 ou 3",
                                campo="EstagioDo"
                            ))
            
            return ValidacaoResult(
                status="SUCESSO" if not erros else "ERRO",
                valido=len(erros) == 0,
                erros=erros,
                criticas=erros  # Neste caso básico, são as mesmas
            )
        
        except Exception as e:
            return ValidacaoResult(
                status="ERRO",
                valido=False,
                erros=[ValidacaoErro(
                    codigo="PARSE",
                    mensagem=str(e)
                )]
            )


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("EXPORTADOR BACEN - Doc3040 ECL")
    print("=" * 60)
    
    # Configuração
    config = ConfigExportacao(
        cnpj="12345678",
        responsavel=ResponsavelInfo(
            nome="João da Silva",
            email="joao.silva@banco.com",
            telefone="1133334444"
        ),
        metodologia=MetodologiaApuracao.COMPLETA
    )
    
    # Criar operações de exemplo
    operacoes = [
        OperacaoECL(
            cliente_id="12345678901",
            contrato="CRED2024001",
            produto="consignado",
            saldo_utilizado=50000.00,
            limite_total=60000.00,
            pd_ajustado=0.02,
            lgd_final=0.35,
            ead=50000.00,
            ecl_final=350.00,
            estagio_ifrs9=1,
            rating="A2",
            dias_atraso=0,
            data_contratacao=date(2024, 1, 15),
            data_vencimento=date(2027, 1, 31),
            taxa_juros_efetiva=18.5
        ),
        OperacaoECL(
            cliente_id="98765432101",
            contrato="CART2024002",
            produto="cartao_credito_rotativo",
            saldo_utilizado=15000.00,
            limite_total=20000.00,
            pd_ajustado=0.08,
            lgd_final=0.80,
            ead=18000.00,
            ecl_final=1152.00,
            estagio_ifrs9=2,
            rating="B3",
            dias_atraso=45,
            data_contratacao=date(2023, 6, 1),
            data_vencimento=date(2025, 12, 31),
            taxa_juros_efetiva=350.0
        )
    ]
    
    # Exportar
    exportador = ExportadorBACEN(config)
    result = exportador.exportar(
        operacoes=operacoes,
        data_base=date(2025, 1, 31)
    )
    
    # Mostrar resultado
    print(f"\n✅ Exportação {'bem-sucedida' if result.sucesso else 'com erros'}")
    print(f"   Arquivo: {result.arquivo_nome}")
    print(f"   Tamanho: {len(result.arquivo_conteudo):,} bytes")
    print(f"   Clientes: {result.total_clientes}")
    print(f"   Operações: {result.total_operacoes}")
    print(f"   ECL Total: R$ {result.ecl_total:,.2f}")
    print(f"   Validação: {result.validacao.status}")
    
    if result.validacao.erros:
        print("\n⚠️ Erros encontrados:")
        for erro in result.validacao.erros:
            print(f"   [{erro.codigo}] {erro.mensagem}")
    
    # Salvar arquivo para teste
    with open(result.arquivo_nome, 'wb') as f:
        f.write(result.arquivo_conteudo)
    print(f"\n📦 Arquivo salvo: {result.arquivo_nome}")
