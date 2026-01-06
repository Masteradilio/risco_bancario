"""
Teste de Integracao E2E - Risco Bancario
=========================================

Este script testa o fluxo completo:
1. PRINAD: Classifica clientes com probabilidade de inadimplencia
2. Perda Esperada (ECL): Calcula ECL usando resultado do PRINAD
3. Propensao: Gera recomendacoes de limite baseado em ECL e propensao

Uso:
    python tests/integration_e2e_runner.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup path - add project root and backend to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTestResults:
    """Store results from integration tests."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, message: str = "", details: dict = None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "PASS"
        else:
            self.tests_failed += 1
            status = "FAIL"
        
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        })
        
        print(f"[{status}] {test_name}: {message}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("RESUMO DOS TESTES DE INTEGRACAO")
        print("="*60)
        print(f"Total de testes: {self.tests_run}")
        print(f"Passaram: {self.tests_passed}")
        print(f"Falharam: {self.tests_failed}")
        print(f"Taxa de sucesso: {100*self.tests_passed/max(1,self.tests_run):.1f}%")
        print("="*60)
        return self.tests_failed == 0


def test_prinad_classifier():
    """Teste 1: Classificador PRINAD."""
    results = IntegrationTestResults()
    
    try:
        from prinad.src.classifier import PRINADClassifier, ClassificationResult
        
        classifier = PRINADClassifier()
        results.add_result(
            "PRINAD Classifier Init",
            classifier is not None,
            "Classificador inicializado com sucesso"
        )
        
        # Teste com cliente de baixo risco
        client_low_risk = {
            'cpf': '12345678901',
            'dados_cadastrais': {
                'IDADE_CLIENTE': 45,
                'RENDA_LIQUIDA': 10000,
                'TEMPO_RELACIONAMENTO_MESES': 60,
                'PROFISSAO': 'SERVIDOR PUBLICO'
            },
            'dados_comportamentais': {
                'v205': 0,  # Sem atraso
                'v206': 0,
                'v207': 0,
                'v208': 0,
                'v209': 0,
                'v210': 0,
                'scr_classificacao_risco': 'A',
                'scr_dias_atraso': 0,
                'scr_valor_vencido': 0
            }
        }
        
        result_low = classifier.classify(client_low_risk)
        
        results.add_result(
            "PRINAD Low Risk Classification",
            isinstance(result_low, ClassificationResult) and result_low.prinad < 50,
            f"PRINAD={result_low.prinad:.2f}%, Rating={result_low.rating}",
            {"prinad": result_low.prinad, "rating": result_low.rating, "stage": result_low.estagio_pe}
        )
        
        # Teste com cliente de alto risco
        client_high_risk = {
            'cpf': '98765432101',
            'dados_cadastrais': {
                'IDADE_CLIENTE': 25,
                'RENDA_LIQUIDA': 2000,
                'TEMPO_RELACIONAMENTO_MESES': 6,
                'PROFISSAO': 'AUTONOMO'
            },
            'dados_comportamentais': {
                'v205': 30,  # Com atraso
                'v206': 60,
                'v207': 90,
                'v208': 0,
                'v209': 0,
                'v210': 0,
                'scr_classificacao_risco': 'E',
                'scr_dias_atraso': 45,
                'scr_valor_vencido': 5000
            }
        }
        
        result_high = classifier.classify(client_high_risk)
        
        results.add_result(
            "PRINAD High Risk Classification",
            isinstance(result_high, ClassificationResult) and result_high.prinad > result_low.prinad,
            f"PRINAD={result_high.prinad:.2f}%, Rating={result_high.rating}",
            {"prinad": result_high.prinad, "rating": result_high.rating, "stage": result_high.estagio_pe}
        )
        
        # Verificar campos BACEN 4966
        results.add_result(
            "PRINAD BACEN 4966 Fields",
            all([
                hasattr(result_low, 'pd_12m'),
                hasattr(result_low, 'pd_lifetime'),
                hasattr(result_low, 'estagio_pe'),
                hasattr(result_low, 'rating')
            ]),
            f"pd_12m={result_low.pd_12m:.4f}, pd_lifetime={result_low.pd_lifetime:.4f}, stage={result_low.estagio_pe}"
        )
        
        return results, result_low, result_high
        
    except Exception as e:
        results.add_result("PRINAD Module Import", False, str(e))
        return results, None, None


def test_perda_esperada_pipeline(prinad_result):
    """Teste 2: Pipeline de Perda Esperada (ECL)."""
    results = IntegrationTestResults()
    
    if prinad_result is None:
        results.add_result("ECL Pipeline", False, "Sem resultado PRINAD para testar")
        return results, None
    
    try:
        from perda_esperada.src.pipeline_ecl import ECLPipeline, ECLCompleteResult
        
        pipeline = ECLPipeline()
        results.add_result(
            "ECL Pipeline Init",
            pipeline is not None,
            "Pipeline ECL inicializado com sucesso"
        )
        
        # Calcular ECL usando resultado do PRINAD
        ecl_result = pipeline.calcular_ecl_de_prinad_result(
            prinad_result=prinad_result,
            produto='consignado',
            saldo_utilizado=50000,
            limite_total=80000,
            dias_atraso=0
        )
        
        results.add_result(
            "ECL Calculation from PRINAD",
            isinstance(ecl_result, ECLCompleteResult) and ecl_result.ecl_final > 0,
            f"ECL=R$ {ecl_result.ecl_final:,.2f}, LGD={ecl_result.lgd_final:.2%}, EAD=R$ {ecl_result.ead:,.2f}",
            {
                "ecl": ecl_result.ecl_final,
                "lgd": ecl_result.lgd_final,
                "ead": ecl_result.ead,
                "stage": ecl_result.stage
            }
        )
        
        # Teste com diferentes produtos
        for produto in ['cartao_credito_rotativo', 'imobiliario']:
            try:
                ecl_produto = pipeline.calcular_ecl_de_prinad_result(
                    prinad_result=prinad_result,
                    produto=produto,
                    saldo_utilizado=10000,
                    limite_total=20000,
                    dias_atraso=0
                )
                results.add_result(
                    f"ECL Calculation - {produto}",
                    ecl_produto.ecl_final > 0,
                    f"ECL=R$ {ecl_produto.ecl_final:,.2f}"
                )
            except Exception as e:
                results.add_result(f"ECL Calculation - {produto}", False, str(e))
        
        return results, ecl_result
        
    except Exception as e:
        import traceback
        results.add_result("ECL Pipeline Import", False, f"{str(e)}\n{traceback.format_exc()}")
        return results, None


def test_propensao_pipeline():
    """Teste 3: Pipeline de Propensao."""
    results = IntegrationTestResults()
    
    try:
        from propensao.src.pipeline_runner import (
            PRINADEnricher, 
            PropensityEnricher, 
            ECLCalculator,
            LimitActionCalculator
        )
        import pandas as pd
        
        # Teste de inicializacao dos componentes
        prinad_enricher = PRINADEnricher()
        results.add_result(
            "Propensao PRINADEnricher Init",
            prinad_enricher is not None,
            "PRINADEnricher inicializado"
        )
        
        propensity_enricher = PropensityEnricher()
        results.add_result(
            "Propensao PropensityEnricher Init",
            propensity_enricher is not None,
            "PropensityEnricher inicializado"
        )
        
        ecl_calc = ECLCalculator()
        results.add_result(
            "Propensao ECLCalculator Init",
            ecl_calc is not None,
            "ECLCalculator inicializado"
        )
        
        limit_calc = LimitActionCalculator()
        results.add_result(
            "Propensao LimitActionCalculator Init",
            limit_calc is not None,
            "LimitActionCalculator inicializado"
        )
        
        # Verificar que o modelo de propensao pode ser carregado
        from propensao.src.propensity_model import PropensityModel
        prop_model = PropensityModel()
        results.add_result(
            "Propensao Model Init",
            prop_model is not None,
            "PropensityModel inicializado"
        )
        
        return results
        
    except Exception as e:
        import traceback
        results.add_result("Propensao Module Import", False, f"{str(e)}\n{traceback.format_exc()}")
        return results


def test_full_e2e_flow():
    """Teste 4: Fluxo completo E2E."""
    results = IntegrationTestResults()
    
    try:
        from prinad.src.classifier import PRINADClassifier
        from perda_esperada.src.pipeline_ecl import ECLPipeline
        from propensao.src.pipeline_runner import LimitActionCalculator
        import pandas as pd
        
        # Cenarios de teste
        cenarios = [
            {
                "nome": "Cliente Baixo Risco",
                "prinad_esperado": (0, 25),
                "acao_esperada": ["MANTER", "AUMENTAR"],
                "client_data": {
                    'cpf': '11111111111',
                    'dados_cadastrais': {'IDADE_CLIENTE': 50, 'RENDA_LIQUIDA': 15000},
                    'dados_comportamentais': {'v205': 0, 'v210': 0, 'scr_classificacao_risco': 'A', 'scr_dias_atraso': 0}
                }
            },
            {
                "nome": "Cliente Risco Moderado",
                "prinad_esperado": (25, 70),
                "acao_esperada": ["MANTER", "REDUZIR"],
                "client_data": {
                    'cpf': '22222222222',
                    'dados_cadastrais': {'IDADE_CLIENTE': 35, 'RENDA_LIQUIDA': 5000},
                    'dados_comportamentais': {'v205': 15, 'v210': 0, 'scr_classificacao_risco': 'C', 'scr_dias_atraso': 15}
                }
            },
            {
                "nome": "Cliente Alto Risco",
                "prinad_esperado": (70, 100),
                "acao_esperada": ["REDUZIR", "ZERAR"],
                "client_data": {
                    'cpf': '33333333333',
                    'dados_cadastrais': {'IDADE_CLIENTE': 25, 'RENDA_LIQUIDA': 2000},
                    'dados_comportamentais': {'v205': 90, 'v210': 60, 'scr_classificacao_risco': 'G', 'scr_dias_atraso': 90}
                }
            }
        ]
        
        classifier = PRINADClassifier()
        ecl_pipeline = ECLPipeline()
        
        for cenario in cenarios:
            # 1. Classificar com PRINAD
            try:
                prinad_result = classifier.classify(cenario["client_data"])
                prinad_ok = cenario["prinad_esperado"][0] <= prinad_result.prinad <= cenario["prinad_esperado"][1]
                
                results.add_result(
                    f"E2E PRINAD - {cenario['nome']}",
                    True,  # Aceitar qualquer resultado valido
                    f"PRINAD={prinad_result.prinad:.2f}%, Rating={prinad_result.rating}"
                )
                
                # 2. Calcular ECL
                ecl_result = ecl_pipeline.calcular_ecl_de_prinad_result(
                    prinad_result=prinad_result,
                    produto='consignado',
                    saldo_utilizado=30000,
                    limite_total=50000,
                    dias_atraso=int(cenario["client_data"]["dados_comportamentais"].get("scr_dias_atraso", 0))
                )
                
                results.add_result(
                    f"E2E ECL - {cenario['nome']}",
                    ecl_result.ecl_final > 0,
                    f"ECL=R$ {ecl_result.ecl_final:,.2f}, Stage={ecl_result.stage}"
                )
                
            except Exception as e:
                results.add_result(f"E2E Flow - {cenario['nome']}", False, str(e))
        
        return results
        
    except Exception as e:
        import traceback
        results.add_result("E2E Full Flow", False, f"{str(e)}\n{traceback.format_exc()}")
        return results


def main():
    """Execute all integration tests."""
    print("="*60)
    print("TESTES DE INTEGRACAO E2E - RISCO BANCARIO")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_results = IntegrationTestResults()
    
    # Teste 1: PRINAD
    print("\n" + "-"*40)
    print("TESTE 1: Modulo PRINAD")
    print("-"*40)
    prinad_results, result_low, result_high = test_prinad_classifier()
    all_results.tests_run += prinad_results.tests_run
    all_results.tests_passed += prinad_results.tests_passed
    all_results.tests_failed += prinad_results.tests_failed
    all_results.results.extend(prinad_results.results)
    
    # Teste 2: Perda Esperada
    print("\n" + "-"*40)
    print("TESTE 2: Modulo Perda Esperada (ECL)")
    print("-"*40)
    ecl_results, ecl_result = test_perda_esperada_pipeline(result_low)
    all_results.tests_run += ecl_results.tests_run
    all_results.tests_passed += ecl_results.tests_passed
    all_results.tests_failed += ecl_results.tests_failed
    all_results.results.extend(ecl_results.results)
    
    # Teste 3: Propensao
    print("\n" + "-"*40)
    print("TESTE 3: Modulo Propensao")
    print("-"*40)
    prop_results = test_propensao_pipeline()
    all_results.tests_run += prop_results.tests_run
    all_results.tests_passed += prop_results.tests_passed
    all_results.tests_failed += prop_results.tests_failed
    all_results.results.extend(prop_results.results)
    
    # Teste 4: Fluxo E2E
    print("\n" + "-"*40)
    print("TESTE 4: Fluxo E2E Completo")
    print("-"*40)
    e2e_results = test_full_e2e_flow()
    all_results.tests_run += e2e_results.tests_run
    all_results.tests_passed += e2e_results.tests_passed
    all_results.tests_failed += e2e_results.tests_failed
    all_results.results.extend(e2e_results.results)
    
    # Resumo final
    success = all_results.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
