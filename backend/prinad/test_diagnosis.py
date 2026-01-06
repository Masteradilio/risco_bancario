"""Test script for diagnosis"""
import sys, time
sys.path.insert(0, 'src')
from classifier import PRINADClassifier

c = PRINADClassifier()

# Test different profiles
profiles = [
    {'name': 'Bom', 'idade': 40, 'renda': 8000, 'v205': 0, 'scr_risco': 'A', 'scr_dias': 0},
    {'name': 'Medio', 'idade': 28, 'renda': 2500, 'v205': 1000, 'scr_risco': 'C', 'scr_dias': 45},
    {'name': 'Alto', 'idade': 22, 'renda': 1500, 'v205': 5000, 'scr_risco': 'F', 'scr_dias': 120},
]

print("="*60)
print("TESTE DE VARIAÇÃO DE PRINAD E LATÊNCIA")
print("="*60)

for p in profiles:
    start = time.time()
    result = c.classify({
        'cpf': '12345678901',
        'dados_cadastrais': {
            'IDADE_CLIENTE': p['idade'],
            'RENDA_BRUTA': p['renda'],
            'RENDA_LIQUIDA': p['renda'] * 0.85,
            'OCUPACAO': 'ASSALARIADO',
            'ESCOLARIDADE': 'MEDIO',
            'scr_classificacao_risco': p['scr_risco'],
            'scr_dias_atraso': p['scr_dias'],
            'scr_valor_vencido': p['scr_dias'] * 100,
        },
        'dados_comportamentais': {'v205': p['v205'], 'v210': 0}
    })
    elapsed = (time.time() - start) * 1000
    print(f"{p['name']}: PRINAD={result.prinad}% Rating={result.rating} PD_Base={result.pd_base}% Pen={result.penalidade_historica} Tempo={elapsed:.0f}ms")

print("="*60)
