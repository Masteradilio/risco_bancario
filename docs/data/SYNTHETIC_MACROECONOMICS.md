# Macroeconomia sintética e cenários

`src/data/synthetic/macroeconomics.py` gera um histórico mensal sintético e
trajetórias forward-looking. A configuração versionada está em
`config/synthetic/macroeconomic_scenarios/1.0.0.json`; seu SHA-256 acompanha a
saída para permitir reprodução e auditoria.

Nenhum valor é uma observação oficial ou uma previsão econômica. O termo
`observed` significa somente o caminho que o gerador apresenta aos demais
componentes como informação disponível naquela data.

## Histórico sintético

O histórico cobre janeiro de 2016 a dezembro de 2025 e alterna regimes
versionados de recessão, recuperação, choque e estabilidade. As trajetórias são
autocorrelacionadas e convergem gradualmente aos alvos do regime, com ruído
determinístico por seed.

Cada mês registra crescimento do PIB, inflação, taxa de política monetária,
desemprego e endividamento das famílias, em pontos percentuais. Também registra
uma pressão de risco derivada, usada apenas como sinal observável.

## Cenários prospectivos

Cada cenário possui 60 pontos mensais entre janeiro de 2026 e dezembro de 2030:

- `upside`, peso 15%;
- `base`, peso 70%;
- `downside`, peso 15%;
- `stress`, peso 0%.

Os três primeiros pesos reproduzem a política quantitativa canônica
`2026.07.1`. `stress` é uma trajetória de sensibilidade separada e não entra na
média ponderada de ECL. Sua inclusão ou ponderação contábil exigiria aprovação e
nova versão de política.

As trajetórias partem do último ponto histórico sintético e convergem de forma
suave para deslocamentos terminais versionados. A ordenação econômica é testada:
PIB diminui e desemprego aumenta entre `upside`, `base`, `downside` e `stress`.

## Relação não linear com risco

`risk_pressure` soma efeitos quadráticos apenas além de patamares adversos:
contração do PIB, inflação e juros elevados, desemprego e endividamento. Assim,
um choque severo cresce mais que proporcionalmente e não é apenas um
multiplicador linear de cenário. Essa função é hipótese sintética demonstrativa,
não modelo calibrado.

## Evidência de aceitação

Com `seed=91`, foram gerados 120 pontos históricos e 240 pontos prospectivos.
Sete testes verificam reprodução, periodicidade, presença das cinco variáveis,
quatro trajetórias, pesos, ordenação de severidade, não linearidade e ausência de
campos latentes.
