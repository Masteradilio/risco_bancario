# Baseline de risco na originação

`src/models/sicr/origination.py` define o registro canônico e persistível usado
como referência futura do SICR. Cada contrato possui no máximo um baseline.

## Conteúdo obrigatório

- identificador do contrato;
- data de reconhecimento e maturidade contratual original;
- PD 12m e rating na originação;
- lifetime PD calculada até o prazo original;
- nome e versão do modelo;
- versão e SHA-256 da política;
- status de aprovação e hash do próprio registro.

A lifetime PD usa a estrutura temporal canônica da Fase 5 e nunca uma maturidade
fixa arbitrária. Para contratos com menos de 12 meses, a PD do horizonte termina
na maturidade; para prazos maiores, a lifetime PD acumula os meses restantes.

## Persistência e integridade

`OriginationBaselineLedger` usa schema `1.0.0`, rejeita contratos duplicados e
é serializado em JSON canônico. Cada registro possui SHA-256 calculado sem o
próprio hash. A leitura recalcula o digest e falha fechada quando conteúdo foi
alterado. Essa persistência de artefato é o contrato canônico; integração com
banco transacional pertence à fase de infraestrutura/persistência.

O baseline aceita status explícito. Enquanto a PD sintética atual estiver
reprovada no OOT, o valor padrão é `not_approved`; persistir a referência não a
transforma em modelo aprovado.

Oito casos de teste cobrem prazo original curto/longo, metadados, round-trip
determinístico, hash, adulteração, unicidade e falha fechada.
