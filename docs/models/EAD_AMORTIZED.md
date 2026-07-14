# EAD de produtos amortizados

`src/models/ead/amortized.py` calcula a EAD no período de default a partir do
cronograma contratual canônico. A regra está em
`config/ead_policy/2026.07.1.json`, com status `demonstrative_unvalidated` e hash
SHA-256 propagado aos resultados.

## Convenção temporal e componentes

O gerador sintético registra o default antes do pagamento agendado na data de
default. A EAD é, portanto, o saldo de abertura da última competência observável
cujo fim é estritamente anterior ao default. Essa convenção reproduz o saldo que
estava disponível ao processo de default e impede usar uma amortização posterior ao
evento.

Para produtos amortizados, a política atual inclui somente principal sacado. Juros
corridos e parcela não utilizada são excluídos explicitamente porque não compõem a
EAD dos eventos sintéticos. Isso é uma convenção do dataset, não uma conclusão
contábil ou regulatória geral; uma fonte institucional deve definir os componentes
da exposição e revalidar a política.

Defaults anteriores à originação falham. Defaults posteriores ao fim do cronograma
recebem EAD zero. O período, saldo de abertura, principal agendado, ajustes, versão e
hash permanecem auditáveis.

## Prepagamento e modificação

O motor consome diretamente `PrepaymentResult` e `ModificationResult` do domínio:

- prepagamento parcial substitui o cronograma original pelo cronograma recalculado;
- prepagamento total zera exposições posteriores;
- modificação substitui o cronograma na data efetiva e preserva ganho/perda e
  indicação de baixa;
- eventos posteriores ao default são ignorados;
- modificação após prepagamento total falha de forma fechada.

No histórico sintético, `term_extension` contém datas e concessão, mas não novos
fluxos reamortizados. O dataset de aceite apenas identifica esse evento e não inventa
um cronograma revisado. O teste canônico de modificação usa o resultado completo do
motor de contratos da Fase 4.

## Evidência de aceite

Com seed 91, há 24 defaults iniciais de produtos amortizados: 8 vehicle finance, 8
mortgages e 8 acquired distressed. A EAD total é R$ 3.090.369,67, média de
R$ 128.765,40 e faixa de R$ 6.505,66 a R$ 435.343,11. Todos os 24 valores projetados
reconciliam ao centavo com a EAD registrada; um contrato possui extensão de prazo
pré-default.

Sete testes cobrem saldo por período, prepagamento parcial e total, modificação,
eventos futuros, originação/maturidade, linhagem e reconciliação da carteira. Os
resultados são sintéticos e não constituem validação de uma definição institucional
de EAD.
