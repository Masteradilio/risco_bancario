# Motor SICR

`src/models/sicr/engine.py` é a fonte canônica da decisão de aumento
significativo de risco de crédito. Ele compara a lifetime PD atual com o baseline
persistido na originação e retorna decisão, métricas intermediárias, gatilhos,
supressões, razões e identificação da política.

## Política demonstrativa

`config/sicr_policy/2026.07.1.json` versiona hipóteses transparentes para testes:

- aumento absoluto de lifetime PD de 0,05;
- razão relativa de 2,00;
- downgrade de dois notches;
- backstop de 31 DPD;
- low-credit-risk habilitado para A1–A3 com lifetime PD atual até 0,02.

Esses números não são apresentados como limites IFRS 9, CMN ou BCB. O arquivo
declara `demonstrative_unvalidated`; calibração institucional, aprovação e
governança de mudança permanecem obrigatórias.

## Ordem de decisão

Gatilhos diretos são downgrade, atraso, watchlist, concessão/forbearance e evento
qualitativo. A isenção de baixo risco nunca os suprime. A isenção somente pode
suprimir gatilhos quantitativos de aumento absoluto/relativo quando habilitada,
solicitada, dentro dos ratings elegíveis e abaixo da PD máxima configurada.

A saída registra lifetime PD de origem/atual, variação absoluta, razão relativa,
notches, aplicação da isenção, gatilhos ativos/suprimidos, razões detalhadas,
versão, SHA-256 e status de evidência. Ausência de gatilho produz explicitamente
`no_sicr_trigger`.

Dez casos de teste cobrem PD absoluta/relativa, notch, watchlist, concessão,
evento qualitativo, backstop inclusivo, isenção, override e rastreabilidade.
