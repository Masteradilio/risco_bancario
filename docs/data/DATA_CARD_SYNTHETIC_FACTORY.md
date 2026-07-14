# Data card — fábrica sintética de risco de crédito

## Resumo

Esta fábrica produz uma carteira longitudinal inteiramente sintética para
desenvolvimento, teste e demonstração de componentes de risco de crédito e ECL.
Os dados não são dados reais, não contêm PII e não representam uma instituição.

## Composição

- clientes PF/PJ, contrapartes e grupos econômicos;
- contratos amortizados, rotativos, compromissos, garantias financeiras e POCI;
- cronogramas, garantias, limites, snapshots, pagamentos, atrasos e modificações;
- defaults, cobranças, recuperações, custos, curas, redefaults e write-offs;
- histórico macroeconômico sintético e quatro trajetórias prospectivas;
- datasets point-in-time de PD, hazard, LGD, EAD/CCF e SICR.

O relógio mensal cobre 2016–2025. Targets de doze meses usam observações apenas
até dezembro de 2024. Splits de desenvolvimento são separados por embargo anual;
2025 é backtesting futuro com targets nulos até a janela amadurecer.

## Geração e proveniência

A população e cada componente usam substreams determinísticas derivadas da seed
e do identificador da entidade. Políticas quantitativas e macroeconômicas têm
versão explícita; a configuração macro também carrega SHA-256. Valores monetários
usam `Decimal` e `ROUND_HALF_EVEN`.

## Usos pretendidos

- testes de unidade, integração, reconciliação e regressão;
- desenvolvimento dos pipelines de PD, LGD, EAD, SICR e ECL;
- casos de Stage 3, POCI, garantias, CCF e recuperação;
- demonstrações públicas sem exposição de dados bancários;
- insumos sintéticos de origem para o futuro mapeamento regulatório.

## Usos proibidos

- inferir comportamento de clientes ou carteiras reais;
- declarar performance, calibração ou conformidade institucional;
- substituir dados oficiais, séries econômicas observadas ou validação humana;
- usar OOT/backtesting para treino, tuning, calibração ou threshold;
- usar campos `target_*`, eventos futuros ou latentes como features.

## Qualidade e leakage

`assess_synthetic_quality` valida referências, unicidade temporal, ordem de
eventos, reconciliação de recuperação, maturidade/nulidade dos targets, presença
dos splits e schema de features. Também resume distribuição e correlação das dez
features numéricas de PD. Correlação é diagnóstico, não critério de seleção.

As latentes do desenho causal não são exportadas. As features usam apenas o
snapshot e a macroeconomia disponíveis na data de observação; targets são
derivados depois da simulação.

## Limitações

- Distribuições, relações causais, taxas de default e recuperação são hipóteses
  sintéticas, não estimativas calibradas.
- A LGD realizada do dataset é não descontada; desconto por EIR será adicionado
  nas fases quantitativas.
- O histórico macro é sintético e não deve ser confundido com série oficial.
- O backtesting de 2025 não pode ser pontuado enquanto os targets 12m não forem
  maturados por uma extensão futura da simulação.
- Os insumos de cliente/contrato/snapshot ainda não constituem um Documento 3040
  nem substituem leiaute, XSD, domínios e críticas oficiais.
- O insumo regulatório materializado é apenas fonte neutra; leiaute, XSD,
  domínios e críticas Doc3040 permanecem para a Fase 12.
