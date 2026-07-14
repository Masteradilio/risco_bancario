# Política quantitativa versionada

## Fonte canônica

A política ativa de modernização está em
`config/risk_policy/2026.07.1.json`. O schema executável é
`src.infrastructure.configuration.models.RiskPolicy`, versão `1.0.0`, e o
loader estrito está em `src.infrastructure.configuration.loader`.

Esta primeira política migra parâmetros demonstrativos existentes. O campo
`metadata.evidence_status` permanece `demonstrative`: a migração elimina
números mágicos efetivos e cria rastreabilidade, mas não constitui calibração,
validação independente ou aprovação regulatória.

## Conteúdo governado

- metadados: versão do schema e da política, vigência, autor, justificativa,
  status de evidência e referências de origem;
- convenções de moeda, precisão e arredondamento;
- faixas de rating e intervalos de PD de 12 meses;
- thresholds e eventos de staging/SICR;
- LGD base e multiplicador downturn por garantia;
- CCF por produto;
- cenários upside, base e downside, com pesos e multiplicadores de PD/LGD.

Os consumidores de compatibilidade em `shared/utils.py` e os pesos do gerenciador
legado de cenários passam a ler essa política. As assinaturas públicas antigas
foram preservadas para que a migração possa ocorrer de forma incremental.

## Validação e falha segura

O carregamento falha antes do cálculo quando houver, entre outros:

- campo desconhecido ou obrigatório ausente;
- janela de vigência invertida;
- faixa de rating com lacuna, sobreposição ou ordem inválida;
- PD, LGD ou CCF fora do domínio permitido;
- threshold de Stage 3 menor ou igual ao de Stage 2;
- eventos qualitativos repetidos;
- ausência ou duplicação dos três cenários;
- pesos de cenário que não somem exatamente um.

O loader canonicaliza o JSON por chave e gera SHA-256. `ECLResult` exige tanto
`configuration_version` quanto `configuration_hash`, tornando identificável a
configuração exata usada em cada resultado.

## Processo de mudança

1. Não editar retroativamente uma política já usada em resultado persistido.
2. Copiar o arquivo para uma nova versão e atualizar versão, vigência, autor,
   justificativa e referências.
3. Alterar o schema versionado somente quando o contrato estrutural mudar.
4. Rodar os testes de configuração, domínio e consumidores de compatibilidade.
5. Registrar impacto quantitativo, aprovação e evidência antes de promover
   `evidence_status` para `validated`.
6. Publicar arquivo, documentação, testes e changelog no mesmo commit.

Valores vindos de `float` devem ser convertidos explicitamente na fronteira. Na
política JSON, percentuais e multiplicadores são representados como strings
decimais para preservar a exatidão.
