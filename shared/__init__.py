"""Shared utilities package for risco_bancario."""

from .utils import (
    PRODUTOS_CREDITO,
    LGD_POR_PRODUTO,
    LIMITE_MAXIMO_MULTIPLO,
    PRAZO_MAXIMO_MESES,
    COMPROMETIMENTO_MAXIMO_RENDA,
    LIMITE_MINIMO_PERCENTUAL,
    COMPROMETIMENTO_GATILHO_MAXDEBT,
    BASE_DIR,
    DADOS_DIR,
    PRINAD_DIR,
    PROPENSAO_DIR,
    setup_logging,
    parse_month_from_filename,
    calcular_comprometimento_renda,
    calcular_limite_maximo_produto,
    get_lgd,
    calcular_ecl,
    get_ifrs9_stage
)

# Sistema de Logs de Auditoria (Art. 40, §1º CMN 4.966)
from .audit_logger import (
    AuditLogger,
    AuditLog,
    EventoAuditoria,
    get_audit_logger,
    audit_stage_migration,
    audit_ecl,
    audit_cure,
    audit_pd_adjust,
    audit_flush
)
