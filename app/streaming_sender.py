"""
PRINAD - Streaming Sender
Sends simulated client data to the API for real-time dashboard demonstration.
Includes bank system simulation with origin systems, credit products, and request types.
"""

import requests
import json
import time
import random
import argparse
from datetime import datetime
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ============================================================================
# CONFIGURAÇÃO DE PROPORÇÕES - SIMULAÇÃO DE SISTEMAS BANCÁRIOS
# ============================================================================

# Sistemas de origem das solicitações (proporções)
SISTEMAS_ORIGEM = [
    ('app_mobile', 0.50),           # 50%
    ('sis_agencia', 0.30),          # 30%
    ('terminal_eletronico', 0.15),  # 15%
    ('central_cliente', 0.05)       # 5%
]

# Produtos de crédito (proporções)
PRODUTOS_CREDITO = [
    ('consignado', 0.40),           # 40%
    ('banparacard', 0.20),          # 20%
    ('cartao_credito', 0.20),       # 20%
    ('imobiliario', 0.10),          # 10%
    ('antecipacao_13_sal', 0.05),   # 5%
    ('cred_veiculo', 0.03),         # 3%
    ('energia_solar', 0.02)         # 2%
]

# Tipo de solicitação (proporções)
TIPOS_SOLICITACAO = [
    ('Proposta', 0.70),             # 70%
    ('Contratacao', 0.30)           # 30%
]

# ============================================================================
# FUNÇÕES DE SELEÇÃO PONDERADA
# ============================================================================

def selecionar_ponderado(opcoes: List[tuple]) -> str:
    """
    Seleciona um valor baseado em pesos/proporções.
    
    Args:
        opcoes: Lista de tuplas (valor, peso)
    
    Returns:
        Valor selecionado
    """
    valores = [o[0] for o in opcoes]
    pesos = [o[1] for o in opcoes]
    return random.choices(valores, weights=pesos)[0]


def selecionar_sistema_origem() -> str:
    """Seleciona sistema de origem com proporções definidas."""
    return selecionar_ponderado(SISTEMAS_ORIGEM)


def selecionar_produto_credito() -> str:
    """Seleciona produto de crédito com proporções definidas."""
    return selecionar_ponderado(PRODUTOS_CREDITO)


def selecionar_tipo_solicitacao() -> str:
    """Seleciona tipo de solicitação com proporções definidas."""
    return selecionar_ponderado(TIPOS_SOLICITACAO)

# ============================================================================
# FUNÇÕES DE GERAÇÃO DE DADOS
# ============================================================================

def generate_random_cpf() -> str:
    """Generate a random CPF (for demo purposes)."""
    return ''.join([str(random.randint(0, 9)) for _ in range(11)])


def generate_random_client() -> Dict[str, Any]:
    """
    Generate random client data for testing.
    Creates realistic distributions of client profiles.
    """
    
    # Occupation options with weights
    ocupacoes = [
        ('ASSALARIADO', 0.4),
        ('AUTONOMO', 0.2),
        ('EMPRESARIO', 0.1),
        ('APOSENTADO', 0.15),
        ('SERVIDOR PUBLICO', 0.1),
        ('PENSIONISTA', 0.05)
    ]
    ocupacao = random.choices(
        [o[0] for o in ocupacoes],
        weights=[o[1] for o in ocupacoes]
    )[0]
    
    # Education options
    escolaridades = ['FUNDAM', 'MEDIO', 'SUPERIOR', 'POS']
    escolaridade = random.choice(escolaridades)
    
    # Generate income based on education and occupation
    base_income = {
        'FUNDAM': 1500,
        'MEDIO': 2500,
        'SUPERIOR': 5000,
        'POS': 8000
    }
    
    income_mult = {
        'SERVIDOR PUBLICO': 1.3,
        'EMPRESARIO': 1.5,
        'ASSALARIADO': 1.0,
        'AUTONOMO': 0.9,
        'APOSENTADO': 0.7,
        'PENSIONISTA': 0.6
    }
    
    renda_bruta = base_income[escolaridade] * income_mult.get(ocupacao, 1.0)
    renda_bruta *= random.uniform(0.7, 1.5)  # Add some variance
    renda_liquida = renda_bruta * random.uniform(0.75, 0.90)
    
    # Age based on occupation
    if ocupacao in ['APOSENTADO', 'PENSIONISTA']:
        idade = random.randint(55, 80)
    else:
        idade = random.randint(22, 60)
    
    # Generate behavioral data
    # Most clients are good (70% adimplentes)
    profile_type = random.choices(
        ['adimplente', 'atraso_curto', 'atraso_longo', 'inadimplente'],
        weights=[0.70, 0.15, 0.10, 0.05]
    )[0]
    
    comportamental = generate_behavioral_data(profile_type)
    
    # Selecionar dados da simulação bancária
    sistema_origem = selecionar_sistema_origem()
    produto_credito = selecionar_produto_credito()
    tipo_solicitacao = selecionar_tipo_solicitacao()
    
    return {
        'cpf': generate_random_cpf(),
        'dados_cadastrais': {
            'IDADE_CLIENTE': idade,
            'RENDA_BRUTA': round(renda_bruta, 2),
            'RENDA_LIQUIDA': round(renda_liquida, 2),
            'OCUPACAO': ocupacao,
            'ESCOLARIDADE': escolaridade,
            'ESTADO_CIVIL': random.choice(['SOLTEIRO', 'CASADO', 'DIVORCIADO', 'VIUVO']),
            'QT_DEPENDENTES': random.choices([0, 1, 2, 3, 4], weights=[0.3, 0.3, 0.25, 0.1, 0.05])[0],
            'TEMPO_RELAC': round(random.uniform(1, 120), 2),
            'TIPO_RESIDENCIA': random.choice(['PROPRIA', 'ALUGADA', 'CEDIDA']),
            'POSSUI_VEICULO': random.choice(['SIM', 'NAO']),
            'PORTABILIDADE': random.choice(['PORTADO', 'NAO PORTADO']),
            'COMP_RENDA': round(random.uniform(0.1, 0.8), 4)
        },
        'dados_comportamentais': comportamental,
        # Novos campos de simulação bancária
        'sistema_origem': sistema_origem,
        'produto_credito': produto_credito,
        'tipo_solicitacao': tipo_solicitacao
    }


def generate_behavioral_data(profile: str) -> Dict[str, float]:
    """
    Generate behavioral data based on client profile.
    
    Args:
        profile: One of 'adimplente', 'atraso_curto', 'atraso_longo', 'inadimplente'
    """
    
    # V-columns represent delinquency at different time thresholds
    data = {
        'v205': 0.0, 'v210': 0.0, 'v220': 0.0, 'v230': 0.0,
        'v240': 0.0, 'v245': 0.0, 'v250': 0.0, 'v255': 0.0,
        'v260': 0.0, 'v270': 0.0, 'v280': 0.0, 'v290': 0.0
    }
    
    if profile == 'adimplente':
        # Clean history - all zeros
        pass
    
    elif profile == 'atraso_curto':
        # Short-term delinquency (30-120 days)
        exposure = random.uniform(500, 5000)
        if random.random() > 0.5:
            data['v205'] = round(exposure * random.uniform(0.5, 1.0), 2)
        if random.random() > 0.6:
            data['v210'] = round(exposure * random.uniform(0.3, 0.8), 2)
        if random.random() > 0.7:
            data['v220'] = round(exposure * random.uniform(0.2, 0.5), 2)
    
    elif profile == 'atraso_longo':
        # Long-term delinquency (120-180 days)
        exposure = random.uniform(2000, 15000)
        data['v205'] = round(exposure * random.uniform(0.1, 0.3), 2)
        data['v210'] = round(exposure * random.uniform(0.2, 0.4), 2)
        data['v220'] = round(exposure * random.uniform(0.3, 0.5), 2)
        data['v230'] = round(exposure * random.uniform(0.4, 0.7), 2)
        data['v240'] = round(exposure * random.uniform(0.5, 0.8), 2)
        if random.random() > 0.5:
            data['v245'] = round(exposure * random.uniform(0.3, 0.6), 2)
    
    elif profile == 'inadimplente':
        # Severe delinquency (180+ days)
        exposure = random.uniform(5000, 50000)
        for col in data.keys():
            days = int(col.replace('v', ''))
            if days <= 290:
                weight = min(1.0, days / 360)
                data[col] = round(exposure * weight * random.uniform(0.7, 1.0), 2)
    
    return data


def send_to_api(api_url: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send client data to the API.
    
    Args:
        api_url: Base API URL
        client_data: Client data dictionary
        
    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            f"{api_url}/predict",
            json=client_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def run_streaming(api_url: str, interval: float, count: int = -1, verbose: bool = True):
    """
    Run continuous streaming of random clients.
    
    Args:
        api_url: Base API URL
        interval: Seconds between requests
        count: Number of requests (-1 for infinite)
        verbose: Print results
    """
    
    print(f"\n{'='*70}")
    print("PRINAD Streaming Sender - Simulação de Sistemas Bancários")
    print(f"{'='*70}")
    print(f"API URL: {api_url}")
    print(f"Interval: {interval}s")
    print(f"Count: {'Infinite' if count < 0 else count}")
    print(f"{'='*70}")
    print("\nProporções configuradas:")
    print("  Sistemas: 50% app_mobile | 30% sis_agencia | 15% terminal | 5% central")
    print("  Produtos: 40% consignado | 20% banparacard | 20% cartao | outros")
    print("  Tipos: 70% Proposta | 30% Contratação")
    print(f"{'='*70}\n")
    
    # Check API health first
    try:
        health = requests.get(f"{api_url}/health", timeout=5).json()
        print(f"API Status: {health.get('status')}")
        print(f"Model Loaded: {health.get('model_loaded')}\n")
    except Exception as e:
        print(f"⚠️ Could not reach API: {e}")
        print("Make sure the API is running: python src/api.py\n")
        return
    
    sent = 0
    successes = 0
    errors = 0
    
    rating_counts = {}
    sistema_counts = {}
    produto_counts = {}
    tipo_counts = {}
    
    try:
        while count < 0 or sent < count:
            # Generate random client
            client_data = generate_random_client()
            
            # Send to API
            result = send_to_api(api_url, client_data)
            sent += 1
            
            if 'error' in result:
                errors += 1
                if verbose:
                    print(f"[{sent}] ❌ Error: {result['error']}")
            else:
                successes += 1
                rating = result.get('rating', 'Unknown')
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
                
                # Count bank simulation fields
                sistema = client_data.get('sistema_origem', 'Unknown')
                produto = client_data.get('produto_credito', 'Unknown')
                tipo = client_data.get('tipo_solicitacao', 'Unknown')
                
                sistema_counts[sistema] = sistema_counts.get(sistema, 0) + 1
                produto_counts[produto] = produto_counts.get(produto, 0) + 1
                tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
                
                if verbose:
                    prinad = result.get('prinad', 0)
                    
                    # Color based on risk
                    if prinad < 20:
                        color = '🟢'
                    elif prinad < 50:
                        color = '🟡'
                    elif prinad < 70:
                        color = '🟠'
                    else:
                        color = '🔴'
                    
                    print(f"[{sent}] {color} CPF: ***{client_data['cpf'][-4:]} | "
                          f"PRINAD: {prinad:5.1f}% | Rating: {rating} | "
                          f"Sistema: {sistema} | Produto: {produto} | Tipo: {tipo}")
            
            # Wait before next request
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⛔ Streaming stopped by user")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total Sent: {sent}")
    print(f"Successes: {successes}")
    print(f"Errors: {errors}")
    
    print(f"\n📊 Rating Distribution:")
    for rating in ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'D']:
        cnt = rating_counts.get(rating, 0)
        pct = (cnt / successes * 100) if successes > 0 else 0
        bar = '█' * int(pct / 5)
        print(f"  {rating}: {cnt:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\n🏦 Sistemas de Origem:")
    for sistema, cnt in sorted(sistema_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / successes * 100) if successes > 0 else 0
        print(f"  {sistema}: {cnt:4d} ({pct:5.1f}%)")
    
    print(f"\n💳 Produtos de Crédito:")
    for produto, cnt in sorted(produto_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / successes * 100) if successes > 0 else 0
        print(f"  {produto}: {cnt:4d} ({pct:5.1f}%)")
    
    print(f"\n📝 Tipos de Solicitação:")
    for tipo, cnt in sorted(tipo_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / successes * 100) if successes > 0 else 0
        print(f"  {tipo}: {cnt:4d} ({pct:5.1f}%)")
    
    print(f"{'='*70}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Send simulated client data to PRINAD API'
    )
    parser.add_argument(
        '--api-url', '-u',
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=5.0,
        help='Seconds between requests (default: 5.0)'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=-1,
        help='Number of requests to send (-1 for infinite)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress per-request output'
    )
    
    args = parser.parse_args()
    
    run_streaming(
        api_url=args.api_url,
        interval=args.interval,
        count=args.count,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
