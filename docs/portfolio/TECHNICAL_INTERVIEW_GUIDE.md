# Guia para entrevista técnica

Este roteiro explica decisões verificáveis do projeto sem converter uma
demonstração sintética em alegação de experiência institucional ou conformidade.

## Apresentação em dois minutos

“Reconstruí um núcleo demonstrativo de impairment/ECL com arquitetura em camadas.
O domínio usa `Decimal`, datas e invariantes; os componentes PD, SICR, LGD e EAD
produzem evidências versionadas; a ECL é decomposta por período e cenário. A API
persiste resultado, versões e hashes, o frontend lê apenas essa evidência e o
pacote regulatório mantém bloqueios explícitos. O pipeline é reproduzível, mas os
modelos continuam não aprovados porque os dados são sintéticos e pequenos.”

## Perguntas e respostas

### Por que não usar um único DataFrame como contrato interno?

DataFrames são úteis nos adaptadores quantitativos, mas não expressam invariantes
de moeda, datas e estado. O domínio imutável torna erro de tipo e arredondamento
visíveis e evita acoplamento da regra ao transporte.

### Como a ECL é reconciliada?

Cada período conserva sobrevivência, PD marginal, LGD, EAD, CCF, desconto e ECL.
Os totais por cenário são ponderados, depois overlay e piso são registrados em
camadas separadas. O ledger e os hashes permitem repetir a soma do detalhe até o
valor final.

### Como o sistema trata Stage 1, 2 e 3?

Stage 1 limita a ECL a 12 meses; Stage 2 usa a curva lifetime; Stage 3 usa cash
shortfall descontado. A decisão de estágio possui baseline de originação,
gatilhos, cura e histórico. Não se presume PD de 100% como substituto universal
do cálculo de Stage 3.

### O que “forward-looking” significa aqui?

Curvas e cenários macroeconômicos são versionados, com pesos explícitos e análise
de sensibilidade. Não há pesos fixos apresentados como norma. Mudanças relevantes
alteram a linhagem e precisam de governança.

### Como segurança e auditoria funcionam?

JWTs são curtos e revogáveis; RBAC concede permissões específicas; ações críticas
exigem confirmação de uso único vinculada ao hash do payload. Eventos append-only
são encadeados por hash. Logs não substituem segregação de funções institucional.

### Por que PostgreSQL não cai automaticamente para SQLite?

Fallback silencioso mistura ambientes, mascara falhas e pode persistir evidência
no destino errado. O backend é escolhido explicitamente e uma configuração
incompleta falha fechada.

### Qual é a evidência de qualidade?

O gate executa formatação, lint, tipos, testes canônicos e legados, cobertura,
build frontend e verificações de segurança. Golden cases verificam fórmulas com
implementação independente; a jornada E2E verifica integração; OOT/backtesting e
model cards registram validade quantitativa. São provas complementares.

### O projeto está em conformidade com BCB/IFRS 9?

Não há alegação de certificação ou homologação. O projeto mapeia requisitos e
pré-valida artefatos derivados, mas faltam dados reais, validação independente,
aprovações institucionais, XSD oficial e críticas oficiais aplicáveis. A resposta
correta é apresentar o limitation register e os bloqueios do manifesto.

## Demonstração sugerida

1. Execute `scripts/e2e_pipeline.py` e mostre o status com bloqueios.
2. Abra `evidence/e2e/report.md` e o ledger reconciliado.
3. Mostre um golden case no JSON e na planilha independente.
4. Consulte a execução persistida no frontend.
5. Abra `evidence/regulatory/manifest.json` e explique requisitos parciais.
6. Encerre com o Limitation Register, não com uma afirmação de certificação.

## Pontos de aprofundamento

- imutabilidade e hashing de migrations;
- prevenção de leakage e separação temporal;
- definição de default, cura e SICR;
- LGD workout e cash flows descontados;
- CCF por produto/horizonte;
- fila limitada, idempotência e observabilidade;
- fronteira entre pré-validação técnica e homologação institucional.
