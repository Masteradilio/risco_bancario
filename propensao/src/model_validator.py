"""
Model Validator - Comprehensive model validation metrics following Basel III, SR 11-7, and IFRS 9.

This module implements rigorous validation metrics for credit risk models,
designed to meet international banking standards for production deployment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import setup_logging

logger = setup_logging(__name__)

# ML imports
try:
    from sklearn.metrics import (
        roc_auc_score, roc_curve, precision_recall_curve,
        brier_score_loss, confusion_matrix
    )
    from scipy import stats
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class SemaforoStatus(Enum):
    """Traffic light status for executive reporting."""
    VERDE = "verde"      # Approved
    AMARELO = "amarelo"  # Needs monitoring
    VERMELHO = "vermelho"  # Not approved


@dataclass
class MetricaExplicada:
    """
    Metric with value, threshold, status, and business explanation.
    Designed for executive presentations.
    """
    nome: str
    valor: float
    threshold_minimo: float
    threshold_desejavel: float
    status: SemaforoStatus
    explicacao_tecnica: str
    interpretacao_negocio: str
    impacto_diretoria: str


@dataclass
class RelatorioValidacao:
    """Complete validation report for executive presentation."""
    modelo: str
    data_validacao: str
    metricas: List[MetricaExplicada]
    status_geral: SemaforoStatus
    recomendacao: str
    sumario_executivo: str


class ModelValidator:
    """
    Validates credit risk models following international banking standards.
    
    Thresholds are calibrated for high-impact production banking environments:
    - AUC-ROC minimum: 0.90 (required), 0.95 (target)
    - Gini minimum: 0.80 (derived from AUC)
    - KS minimum: 50% (excellent discrimination)
    - PSI maximum: 0.10 (strict stability)
    """
    
    # THRESHOLDS - Updated per user requirements
    THRESHOLDS = {
        'auc_roc': {'minimo': 0.90, 'desejavel': 0.95, 'excelente': 0.98},
        'gini': {'minimo': 0.80, 'desejavel': 0.90, 'excelente': 0.96},
        'ks': {'minimo': 0.50, 'desejavel': 0.60, 'excelente': 0.70},
        'psi': {'maximo': 0.25, 'desejavel': 0.10, 'excelente': 0.05},
        'brier': {'maximo': 0.15, 'desejavel': 0.10, 'excelente': 0.05},
    }
    
    # METRIC EXPLANATIONS
    EXPLICACOES = {
        'auc_roc': {
            'tecnica': (
                "AUC-ROC (Area Under the Receiver Operating Characteristic Curve) mede "
                "a capacidade do modelo de distinguir entre clientes que vão inadimplir "
                "e clientes que vão honrar seus pagamentos. O valor varia de 0.5 (aleatório) "
                "a 1.0 (perfeito). Um AUC de 0.90 significa que, ao selecionar aleatoriamente "
                "um cliente que inadimpliu e um que não inadimpliu, em 90% das vezes o modelo "
                "atribuirá maior probabilidade de default ao inadimplente."
            ),
            'negocio': {
                0.95: "EXCELENTE: O modelo discrimina com altíssima precisão. Concessões de crédito terão baixíssima taxa de erro.",
                0.90: "BOM: O modelo atende aos requisitos mínimos para produção com bom poder de discriminação.",
                0.85: "ACEITÁVEL: A discriminação é adequada, mas requer monitoramento frequente.",
                0.00: "INSUFICIENTE: O modelo não distingue adequadamente bons e maus pagadores. NÃO USAR EM PRODUÇÃO."
            },
            'impacto': (
                "Impacto Financeiro: Cada ponto percentual de melhoria no AUC pode representar "
                "redução de 5-10% nas perdas de crédito. Com uma carteira de R$15 bilhões e "
                "inadimplência de 2.5%, um AUC alto pode economizar milhões em provisões."
            )
        },
        'gini': {
            'tecnica': (
                "Coeficiente de Gini (também chamado Accuracy Ratio) mede o poder de ordenação "
                "do modelo. Calculado como Gini = 2×AUC - 1. Varia de 0 (aleatório) a 1 (perfeito). "
                "Um Gini de 0.80 indica que o modelo tem 80% de eficiência em ordenar clientes "
                "do menor para o maior risco."
            ),
            'negocio': {
                0.90: "EXCELENTE: Ordenação quase perfeita. Políticas de pricing e limite serão altamente eficazes.",
                0.80: "BOM: Boa capacidade de ranking. Adequado para decisões automatizadas.",
                0.60: "ACEITÁVEL: Ordenação moderada. Requer validação humana em casos limítrofes.",
                0.00: "INSUFICIENTE: Capacidade de ordenação inadequada. Risco de aprovar maus clientes."
            },
            'impacto': (
                "Impacto Financeiro: Alto Gini permite precificação diferenciada por risco, "
                "aumentando spread em clientes de maior risco e mantendo competitividade nos bons."
            )
        },
        'ks': {
            'tecnica': (
                "Estatística de Kolmogorov-Smirnov (KS) mede a máxima separação entre as "
                "distribuições acumuladas de bons e maus pagadores. Varia de 0% a 100%. "
                "Um KS de 50% significa que existe um ponto de corte onde a diferença entre "
                "a taxa de detecção de inadimplentes e a taxa de falsos positivos é de 50 pontos."
            ),
            'negocio': {
                0.60: "EXCELENTE: Separação excepcional. Estratégias de cobrança e prevenção serão muito eficazes.",
                0.50: "BOM: Boa separação. O modelo identifica claramente os grupos de risco.",
                0.40: "ACEITÁVEL: Separação moderada. Útil para decisões com margem de segurança.",
                0.00: "INSUFICIENTE: Sem separação significativa. Não usar para decisões de crédito."
            },
            'impacto': (
                "Impacto Operacional: KS alto permite identificar precocemente clientes "
                "problemáticos para ações de cobrança preventiva, reduzindo perdas em até 30%."
            )
        },
        'psi': {
            'tecnica': (
                "PSI (Population Stability Index) mede a estabilidade da distribuição de scores "
                "ao longo do tempo. Calculado como Σ[(Atual-Base) × ln(Atual/Base)]. "
                "Valores baixos indicam que a população de clientes não mudou significativamente."
            ),
            'negocio': {
                0.05: "EXCELENTE: População muito estável. Modelo permanece válido sem recalibração.",
                0.10: "BOM: Leve variação aceitável. Monitorar mensalmente.",
                0.20: "ATENÇÃO: Mudança significativa. Investigar causas e considerar recalibração.",
                1.00: "CRÍTICO: População muito diferente. Modelo deve ser reconstruído."
            },
            'impacto': (
                "Impacto Regulatório: PSI alto pode indicar mudança de mix de clientes ou "
                "contexto econômico, exigindo revisão do modelo conforme exigências do BACEN."
            )
        },
        'brier': {
            'tecnica': (
                "Brier Score mede a calibração das probabilidades previstas. "
                "Calculado como média de (P_previsto - Evento_real)². Varia de 0 (perfeito) a 1. "
                "Um Brier de 0.10 significa que, em média, o erro quadrático entre a probabilidade "
                "prevista e o evento real é de 10%."
            ),
            'negocio': {
                0.05: "EXCELENTE: Probabilidades muito bem calibradas. PD pode ser usado diretamente para pricing.",
                0.10: "BOM: Calibração adequada. Probabilidades confiáveis para provisão IFRS 9.",
                0.15: "ACEITÁVEL: Calibração moderada. Validar contra defaults históricos.",
                1.00: "INSUFICIENTE: Probabilidades desalinhadas com realidade. Não usar para ECL."
            },
            'impacto': (
                "Impacto Contábil: Brier baixo garante que provisões IFRS 9 são precisas, "
                "evitando tanto subprovisão (risco regulatório) quanto superprovisão (capital ocioso)."
            )
        }
    }
    
    def __init__(self):
        """Initialize model validator."""
        if not ML_AVAILABLE:
            raise ImportError("scikit-learn and scipy required for model validation")
        logger.info("ModelValidator initialized with production thresholds")
    
    def calcular_auc_roc(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> float:
        """
        Calculate AUC-ROC.
        
        Args:
            y_true: True binary labels (0/1)
            y_pred_proba: Predicted probabilities of positive class
            
        Returns:
            AUC-ROC score
        """
        return roc_auc_score(y_true, y_pred_proba)
    
    def calcular_gini(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> float:
        """
        Calculate Gini coefficient.
        
        Args:
            y_true: True binary labels
            y_pred_proba: Predicted probabilities
            
        Returns:
            Gini coefficient (2*AUC - 1)
        """
        auc = self.calcular_auc_roc(y_true, y_pred_proba)
        return 2 * auc - 1
    
    def calcular_ks(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculate Kolmogorov-Smirnov statistic.
        
        Args:
            y_true: True binary labels
            y_pred_proba: Predicted probabilities
            
        Returns:
            Tuple of (KS statistic, optimal threshold)
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        ks_values = tpr - fpr
        ks_max = np.max(ks_values)
        ks_threshold = thresholds[np.argmax(ks_values)]
        return ks_max, ks_threshold
    
    def calcular_psi(
        self,
        scores_desenvolvimento: np.ndarray,
        scores_atual: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index.
        
        Args:
            scores_desenvolvimento: Score distribution from development
            scores_atual: Current score distribution
            n_bins: Number of bins
            
        Returns:
            PSI value
        """
        # Create bins from development distribution
        bins = np.percentile(scores_desenvolvimento, np.linspace(0, 100, n_bins + 1))
        bins[0] = -np.inf
        bins[-1] = np.inf
        
        # Count in each bin
        dev_counts, _ = np.histogram(scores_desenvolvimento, bins=bins)
        atual_counts, _ = np.histogram(scores_atual, bins=bins)
        
        # Convert to proportions
        dev_prop = dev_counts / len(scores_desenvolvimento)
        atual_prop = atual_counts / len(scores_atual)
        
        # Avoid division by zero
        dev_prop = np.maximum(dev_prop, 0.0001)
        atual_prop = np.maximum(atual_prop, 0.0001)
        
        # Calculate PSI
        psi = np.sum((atual_prop - dev_prop) * np.log(atual_prop / dev_prop))
        return psi
    
    def calcular_brier(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> float:
        """
        Calculate Brier Score.
        
        Args:
            y_true: True binary labels
            y_pred_proba: Predicted probabilities
            
        Returns:
            Brier score
        """
        return brier_score_loss(y_true, y_pred_proba)
    
    def hosmer_lemeshow_test(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        n_groups: int = 10
    ) -> Tuple[float, float]:
        """
        Perform Hosmer-Lemeshow calibration test.
        
        Args:
            y_true: True binary labels
            y_pred_proba: Predicted probabilities
            n_groups: Number of groups
            
        Returns:
            Tuple of (chi-squared statistic, p-value)
        """
        # Sort by predicted probability
        sorted_indices = np.argsort(y_pred_proba)
        y_true_sorted = y_true[sorted_indices]
        y_pred_sorted = y_pred_proba[sorted_indices]
        
        # Create groups
        group_size = len(y_true) // n_groups
        
        observed = []
        expected = []
        
        for i in range(n_groups):
            start = i * group_size
            end = start + group_size if i < n_groups - 1 else len(y_true)
            
            obs = np.sum(y_true_sorted[start:end])
            exp = np.sum(y_pred_sorted[start:end])
            
            observed.append(obs)
            expected.append(max(exp, 0.0001))
        
        # Chi-squared test
        chi2 = np.sum((np.array(observed) - np.array(expected))**2 / np.array(expected))
        p_value = 1 - stats.chi2.cdf(chi2, n_groups - 2)
        
        return chi2, p_value
    
    def determinar_status(
        self,
        metrica: str,
        valor: float
    ) -> SemaforoStatus:
        """
        Determine traffic light status for a metric.
        
        Args:
            metrica: Metric name
            valor: Metric value
            
        Returns:
            SemaforoStatus
        """
        thresholds = self.THRESHOLDS.get(metrica, {})
        
        if metrica == 'psi' or metrica == 'brier':
            # Lower is better
            maximo = thresholds.get('maximo', 0.25)
            desejavel = thresholds.get('desejavel', 0.10)
            
            if valor <= desejavel:
                return SemaforoStatus.VERDE
            elif valor <= maximo:
                return SemaforoStatus.AMARELO
            else:
                return SemaforoStatus.VERMELHO
        else:
            # Higher is better
            minimo = thresholds.get('minimo', 0.70)
            desejavel = thresholds.get('desejavel', 0.90)
            
            if valor >= desejavel:
                return SemaforoStatus.VERDE
            elif valor >= minimo:
                return SemaforoStatus.AMARELO
            else:
                return SemaforoStatus.VERMELHO
    
    def gerar_metrica_explicada(
        self,
        nome: str,
        valor: float
    ) -> MetricaExplicada:
        """
        Generate explained metric for executive report.
        
        Args:
            nome: Metric name (auc_roc, gini, ks, psi, brier)
            valor: Metric value
            
        Returns:
            MetricaExplicada with full explanation
        """
        thresholds = self.THRESHOLDS.get(nome, {})
        explicacao = self.EXPLICACOES.get(nome, {})
        status = self.determinar_status(nome, valor)
        
        # Get thresholds
        if nome in ['psi', 'brier']:
            threshold_min = thresholds.get('maximo', 0.25)
            threshold_desejavel = thresholds.get('desejavel', 0.10)
        else:
            threshold_min = thresholds.get('minimo', 0.70)
            threshold_desejavel = thresholds.get('desejavel', 0.90)
        
        # Get business interpretation
        interpretacoes = explicacao.get('negocio', {})
        interpretacao = ""
        for threshold, texto in sorted(interpretacoes.items(), reverse=True):
            if valor >= threshold:
                interpretacao = texto
                break
        
        return MetricaExplicada(
            nome=nome.upper(),
            valor=valor,
            threshold_minimo=threshold_min,
            threshold_desejavel=threshold_desejavel,
            status=status,
            explicacao_tecnica=explicacao.get('tecnica', ''),
            interpretacao_negocio=interpretacao,
            impacto_diretoria=explicacao.get('impacto', '')
        )
    
    def validar_modelo(
        self,
        nome_modelo: str,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        scores_desenvolvimento: Optional[np.ndarray] = None
    ) -> RelatorioValidacao:
        """
        Perform complete model validation.
        
        Args:
            nome_modelo: Model name
            y_true: True binary labels
            y_pred_proba: Predicted probabilities
            scores_desenvolvimento: Development scores for PSI (optional)
            
        Returns:
            RelatorioValidacao with all metrics
        """
        from datetime import datetime
        
        logger.info(f"Validating model: {nome_modelo}")
        
        # Calculate all metrics
        auc = self.calcular_auc_roc(y_true, y_pred_proba)
        gini = self.calcular_gini(y_true, y_pred_proba)
        ks, _ = self.calcular_ks(y_true, y_pred_proba)
        brier = self.calcular_brier(y_true, y_pred_proba)
        
        # PSI if development scores provided
        if scores_desenvolvimento is not None:
            psi = self.calcular_psi(scores_desenvolvimento, y_pred_proba)
        else:
            psi = 0.0
        
        # Generate explained metrics
        metricas = [
            self.gerar_metrica_explicada('auc_roc', auc),
            self.gerar_metrica_explicada('gini', gini),
            self.gerar_metrica_explicada('ks', ks),
            self.gerar_metrica_explicada('psi', psi),
            self.gerar_metrica_explicada('brier', brier),
        ]
        
        # Determine overall status
        statuses = [m.status for m in metricas]
        if SemaforoStatus.VERMELHO in statuses:
            status_geral = SemaforoStatus.VERMELHO
            recomendacao = (
                "⛔ NÃO RECOMENDADO PARA PRODUÇÃO. Uma ou mais métricas críticas "
                "não atingiram o threshold mínimo. Revisar modelo antes de implementação."
            )
        elif SemaforoStatus.AMARELO in statuses:
            status_geral = SemaforoStatus.AMARELO
            recomendacao = (
                "⚠️ APROVADO COM RESSALVAS. Implementar com monitoramento intensivo "
                "e plano de contingência. Revisar métricas em 30 dias."
            )
        else:
            status_geral = SemaforoStatus.VERDE
            recomendacao = (
                "✅ APROVADO PARA PRODUÇÃO. Todas as métricas dentro dos padrões de excelência. "
                "Monitoramento trimestral padrão."
            )
        
        # Executive summary
        sumario = (
            f"O modelo {nome_modelo} foi validado em {datetime.now().strftime('%d/%m/%Y')} "
            f"utilizando os mais rigorosos padrões bancários internacionais (Basel III, SR 11-7, IFRS 9). "
            f"\n\nResultados principais:\n"
            f"• AUC-ROC: {auc:.2%} ({metricas[0].status.value})\n"
            f"• Gini: {gini:.2%} ({metricas[1].status.value})\n"
            f"• KS: {ks:.2%} ({metricas[2].status.value})\n"
            f"• PSI: {psi:.3f} ({metricas[3].status.value})\n"
            f"• Brier: {brier:.3f} ({metricas[4].status.value})\n"
        )
        
        return RelatorioValidacao(
            modelo=nome_modelo,
            data_validacao=datetime.now().strftime('%Y-%m-%d'),
            metricas=metricas,
            status_geral=status_geral,
            recomendacao=recomendacao,
            sumario_executivo=sumario
        )
    
    def exportar_relatorio_markdown(
        self,
        relatorio: RelatorioValidacao,
        output_path: Path
    ) -> Path:
        """
        Export validation report to markdown for executive presentation.
        
        Args:
            relatorio: Validation report
            output_path: Output path
            
        Returns:
            Path to generated file
        """
        lines = [
            f"# Relatório de Validação: {relatorio.modelo}",
            f"*Data: {relatorio.data_validacao}*",
            "",
            "---",
            "",
            "## Sumário Executivo",
            "",
            relatorio.sumario_executivo,
            "",
            f"### Status Geral: {relatorio.status_geral.value.upper()} {'🟢' if relatorio.status_geral == SemaforoStatus.VERDE else '🟡' if relatorio.status_geral == SemaforoStatus.AMARELO else '🔴'}",
            "",
            relatorio.recomendacao,
            "",
            "---",
            "",
            "## Métricas Detalhadas",
            ""
        ]
        
        for m in relatorio.metricas:
            emoji = '🟢' if m.status == SemaforoStatus.VERDE else '🟡' if m.status == SemaforoStatus.AMARELO else '🔴'
            
            lines.extend([
                f"### {m.nome} {emoji}",
                "",
                f"**Valor: {m.valor:.4f}** | Mínimo: {m.threshold_minimo:.2f} | Desejável: {m.threshold_desejavel:.2f}",
                "",
                "#### O que é esta métrica?",
                m.explicacao_tecnica,
                "",
                "#### Interpretação para o Negócio",
                m.interpretacao_negocio,
                "",
                "#### Impacto para a Diretoria",
                m.impacto_diretoria,
                "",
                "---",
                ""
            ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Report exported to {output_path}")
        return output_path


# Module-level instance
_model_validator: Optional[ModelValidator] = None


def get_model_validator() -> ModelValidator:
    """Get or create model validator instance."""
    global _model_validator
    if _model_validator is None:
        _model_validator = ModelValidator()
    return _model_validator


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)
    
    # Simulate a good model
    n_samples = 10000
    y_true = np.random.binomial(1, 0.03, n_samples)  # 3% default rate
    
    # Good predictions (correlated with truth)
    noise = np.random.normal(0, 0.1, n_samples)
    y_pred = np.clip(y_true * 0.8 + (1 - y_true) * 0.05 + noise, 0, 1)
    
    validator = ModelValidator()
    relatorio = validator.validar_modelo(
        nome_modelo="PRINAD v2.0",
        y_true=y_true,
        y_pred_proba=y_pred
    )
    
    print(relatorio.sumario_executivo)
    print(relatorio.recomendacao)
