# Histórico de estágio, cura e redefault

`src/models/sicr/history.py` implementa a máquina canônica de transição e um
ledger imutável por contrato. Cada registro preserva sequência, data efetiva,
estágio anterior/novo, razões, decisão de cura, redefault e versões/hashes das
políticas de default e SICR.

## Regras de transição

- qualquer decisão Stage 3 ativa leva ou mantém o contrato em Stage 3;
- Stage 3 sem evidência de cura permanece Stage 3;
- cura incompleta ou antes do período mínimo permanece Stage 3, com todas as
  condições bloqueadoras;
- cura elegível retorna a Stage 2 se ainda houver SICR, ou Stage 1 caso contrário;
- novo Stage 3 após uma saída de Stage 3 recebe `redefault_after_cure`.

A decisão de cura reutiliza a política canônica: ausência de vencidos, período
de pagamentos tempestivos (ou exceção de baixa frequência), obrigações atendidas
e capacidade integral evidenciada. Logo, critérios quantitativos e qualitativos
são cumulativos e a cura prematura é bloqueada.

O ledger rejeita contrato divergente, sequência não contígua, data não crescente
e estágio anterior incompatível com o último estado. Sete testes cobrem entrada
em Stage 3, bloqueios, retorno a Stage 1/2, redefault e integridade do histórico.
