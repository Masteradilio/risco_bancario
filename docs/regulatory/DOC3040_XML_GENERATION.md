# Geração de XML candidato do Documento 3040

## Natureza da saída

`generate_xml_candidate()` produz XML determinístico para inspeção pelo
**pré-validador**. A saída usa o registry da data-base, mas recebe o status
`XSD_AND_CRITICS_PENDING` enquanto XSD e críticas não forem executados. Ela não deve ser
descrita como arquivo válido, homologado ou pronto para transmissão.

## Conteúdo gerado

O gerador em `src/regulatory/doc3040/generator.py` escreve somente valores do contrato de
entrada com linhagem:

- atributos do cabeçalho e total de clientes declarado;
- clientes e operações individualizadas;
- todos os vértices de vencimento fornecidos, ordenados pelo código oficial;
- garantias, informações adicionais e Sicor quando presentes;
- `ContInstFinRes4966`, motivos de estágio e perdas reconhecidas quando aplicáveis;
- agregações e seus vencimentos;
- grupos de IPOCs conectados.

Campos opcionais ausentes não são criados. Data de vencimento ausente permanece
indeterminada. O gerador não reparte saldos entre vértices, não estima renda, não calcula
valor justo, não deriva motivo de estágio e não cria fração de ECL para `Perda`.

## IPOC

Para uma operação nova no pacote sintético, `compose_ipoc()` aplica a concatenação
documentada nas instruções oficiais:

1. CNPJ da instituição, 8 posições;
2. modalidade, 4 posições;
3. tipo do cliente, 1 posição;
4. CPF com 11 posições para PF, raiz CNPJ com 8 para PJ ou código dos demais tipos com
   14 posições e zeros à esquerda;
5. código do contrato, de 1 a 40 posições, sem complemento.

O IPOC continua sendo uma entrada com origem, e o gerador compara seu valor com a
composição. Divergência interrompe a geração. O escopo sintético não tenta resolver
exceções históricas de manutenção/alteração de IPOC sem a respectiva trilha de eventos e
informações adicionais.

## Regras temporais do pacote 2026

O campo `Cosif` foi descontinuado a partir de janeiro de 2025 segundo o histórico do
leiaute. Por isso, ele permanece representado no catálogo histórico, mas deve ser
explicitamente `None` e é proibido pelo gerador para julho-outubro de 2026. Essa decisão
substitui o código legado, que injetava uma conta COSIF fixa.

O XML só pode ser gerado com uma versão cuja faixa contenha a data-base. A seleção não
faz fallback. O conteúdo e o SHA-256 são reprodutíveis para a mesma entrada.

## Totalizadores

`TotalCli` vem do controle de origem e é reconciliado com os clientes individualizados
quando não existem agregações. Havendo agregações, não pode ser inferior ao conjunto
individualizado; a reconciliação integral com a população não individualizada exige os
controles semânticos da Tarefa 12.4. `QtdCli`, `QtdOp` e vencimentos agregados também são
entradas com origem, nunca contagens fabricadas pelo gerador.

## Evidência

`tests/regulatory/test_doc3040_generator.py` verifica determinismo, seleção de leiaute,
composição IPOC, proibição de COSIF, todos os blocos aplicáveis, perda reconhecida exata,
agregações e ausência de vértices inventados. Golden files e categorias de erro serão
consolidados na Tarefa 12.5.
