# Histórico longitudinal sintético

`src/data/synthetic/longitudinal.py` transforma uma população originada em
snapshots mensais observáveis. A janela padrão vai de janeiro de 2016 a dezembro
de 2025.

Cada snapshot registra contrato/cliente, data-base, safra, meses desde
originação, saldo, limite, utilização, prestação, pagamento, atraso, score
comportamental, rating, modificação e versão de política. O rating consome as
faixas da configuração canônica `2026.07.1`.

O processo é determinístico por contrato, com substream própria. Sinais de risco
e atraso evoluem no tempo antes dos eventos de default, que só serão sorteados
na Tarefa 3.4. Extensões de prazo preservam vencimento antigo/novo, data, tipo e
indicador de concessão.

As saídas públicas não possuem `target`, `default_date`, `future_default` ou
campos `_latent`. O histórico não deve ser usado diretamente para treino: os
cortes por `observation_date` e targets futuros pertencem à Tarefa 3.6.
