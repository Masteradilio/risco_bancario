# Escopo oficial do produto

## Propósito

`risco_bancario` é uma plataforma pública de referência para estudo, desenvolvimento e demonstração de impairment de instrumentos financeiros e perda de crédito esperada usando exclusivamente dados sintéticos. O produto deve permitir cálculo reproduzível, validação quantitativa, rastreabilidade e pré-validação regulatória sem alegar certificação, homologação ou adequação automática a uma instituição específica.

O núcleo do produto é o impairment/ECL da IFRS 9 e os requisitos aplicáveis da Resolução CMN nº 4.966/2021 e da Resolução BCB nº 352/2023. A aplicabilidade concreta depende do tipo de instituição, instrumento, data-base e versão normativa, e será controlada pela matriz de rastreabilidade da Fase 2.

## Princípios de fronteira

1. Dados e resultados são sintéticos ou demonstrativos até que exista adaptação institucional autorizada.
2. Cálculo econômico/contábil, overlay gerencial, piso regulatório e reporte são camadas separadas.
3. Nenhum módulo substitui julgamento contábil, validação independente ou homologação institucional.
4. Nenhum valor regulatório ausente pode ser inventado ou preenchido silenciosamente.
5. A implementação só é considerada suportada quando vinculada a fonte oficial vigente, código, teste e evidência.

## Escopo principal incluído

### Instrumentos e exposições

- ativos financeiros sujeitos ao modelo de impairment no perímetro declarado;
- recebíveis de arrendamento e ativos contratuais quando representados pelo schema do produto;
- compromissos de empréstimo e contratos de garantia financeira aos quais os requisitos de impairment sejam aplicáveis;
- exposições amortizadas, rotativas e coletivas;
- ativos adquiridos ou originados com problema de recuperação de crédito (POCI);
- modificações, renegociações, baixas e recuperações pós-baixa na extensão necessária ao ECL.

### Capacidades quantitativas

- fábrica longitudinal e reproduzível de dados sintéticos;
- PD de 12 meses e lifetime por estrutura temporal;
- LGD workout baseada em recuperações líquidas descontadas;
- EAD temporal e CCF comportamental;
- SICR, staging, default, cura, redefault e arrasto por contraparte;
- cenários forward-looking e ECL integral por cenário;
- Stage 1, Stage 2, Stage 3 e POCI;
- fluxos contratuais, taxa efetiva de juros, desconto e cash shortfall;
- cálculos individual e coletivo, overlays e pisos em camadas separadas;
- reconciliação, golden cases, backtesting e monitoramento.

### Governança e produto

- dados, modelos, políticas, cenários, configurações e resultados versionados;
- model cards, data cards, relatórios de validação e registro de limitações;
- APIs, persistência, frontend, RBAC, auditoria e observabilidade;
- Documento 3040 sintético, com geração e pré-validação por leiaute, XSD e críticas versionadas;
- pacote de evidências para revisão técnica e adaptação futura.

## Extensões incluídas com fronteira limitada

| Extensão | Incluído | Limite |
|---|---|---|
| Classificação e mensuração | Cadastro de business model, teste SPPI e classificação entre custo amortizado, FVOCI e FVTPL. | Apenas o necessário para determinar elegibilidade e integração com impairment; não é um subledger contábil completo. |
| Modificação e desreconhecimento | Eventos, cálculo de efeitos e integração com ECL. | Não substitui políticas contábeis institucionais nem cobre todos os instrumentos financeiros possíveis. |
| Disclosures | Reconciliações e demonstrativos sintéticos relacionados a risco de crédito e allowance. | Não produz demonstrações financeiras completas nem assegura publicação regulatória. |
| CMN 4.966 e BCB 352 | Requisitos aplicáveis ao perímetro e à população simulada, versionados por data-base. | Aplicabilidade institucional deve ser confirmada na matriz regulatória; o sistema não presume enquadramento universal. |
| Documento 3040 | Geração de exemplo e pré-validação com insumos sintéticos completos. | Não transmite arquivos, não emite protocolo oficial e não se apresenta como validador do Banco Central. |
| PRINAD | Desenvolvimento de PD/rating e insumos de staging sob governança de modelos. | Não é motor automático de concessão ou política universal de crédito. |
| PROLIMITE | Demonstração periférica de propensão, utilização e comportamento de limites. | Não integra o núcleo contábil; só pode fornecer EAD/CCF se houver modelo aprovado, versionado e testado. |
| Agente de IA | Consulta de evidências e resultados autorizados com citações internas. | Não decide crédito, não aprova modelo, não interpreta norma de forma vinculante e não afirma conformidade. |

## Fora do escopo inicial

- hedge accounting e designação/efetividade de relações de proteção;
- contabilidade completa de passivos financeiros, derivativos e instrumentos patrimoniais;
- subledger, razão contábil, fechamento ou demonstrações financeiras completas;
- capital regulatório, RWA, modelos IRB, ICAAP, risco de mercado e risco de liquidez;
- precificação, concessão automática, cobrança operacional ou decisão comercial autônoma;
- integração real com SCR, core banking, bureaus, Open Finance ou dados pessoais;
- transmissão oficial ao Banco Central, recepção de protocolo ou substituição dos validadores oficiais;
- parecer jurídico ou contábil, certificação de auditoria e homologação institucional;
- operação multi-instituição em produção, alta disponibilidade e tratamento de PII real antes de revisão específica de segurança e privacidade.

## Itens futuros condicionados

| Item | Condição para entrada no escopo |
|---|---|
| Adaptadores para dados reais | Contrato de dados, base legal, controles de privacidade, segurança e qualidade aprovados. |
| Homologação institucional | Calibração local, validação independente, testes de aceitação e aprovação formal da instituição. |
| Transmissão regulatória | Leiaute vigente, credenciais, ambiente homologado e processo operacional aprovado. |
| Novos produtos e jurisdições | Análise de aplicabilidade, fontes oficiais, schemas, modelos e golden cases próprios. |
| Hedge accounting | Backlog, arquitetura, especialistas e pacote de testes específicos; não é consequência automática da conclusão do núcleo ECL. |

## Fronteiras dos módulos

| Módulo-alvo | Responsabilidade | Não deve fazer |
|---|---|---|
| Domínio de contratos e cashflows | Representar contratos, garantias, cronogramas, EIR, modificações e fluxos. | Depender de API, banco, frontend ou regra regulatória hard-coded. |
| Dados sintéticos | Gerar entidades e eventos longitudinais reproduzíveis. | Exportar variáveis latentes como features ou usar eventos futuros na data de observação. |
| Modelos PD/LGD/EAD/SICR | Treinar, calibrar, inferir e produzir evidências versionadas. | Usar OOT para desenvolvimento ou aprovar automaticamente o próprio modelo. |
| Motor ECL | Calcular perdas por período, cenário e contrato, incluindo Stage 3 e POCI. | Inventar entrada, misturar overlay/piso ou consultar serviço externo durante cálculo determinístico. |
| Regulação | Resolver regras por versão/data-base e manter rastreabilidade. | Declarar conformidade ou gerar reporte incompleto com defaults silenciosos. |
| Validação | Executar golden cases, reconciliação, backtesting, monitoramento e aprovação simulada independente. | Alterar o modelo avaliado ou aprová-lo sem critérios objetivos. |
| Aplicação/APIs | Orquestrar casos de uso, jobs e contratos de entrada/saída. | Reimplementar fórmula ou política de domínio. |
| Infraestrutura | Persistência, segurança, observabilidade e integrações. | Tornar o cálculo dependente de estado externo não versionado. |
| Frontend | Exibir dados, decomposição, evidências e limitações com origem explícita. | Exibir mock silencioso ou induzir interpretação de certificação. |

## Critério de conclusão do produto

O produto só alcança o escopo declarado quando todas as tarefas aplicáveis do `docs/MASTER_BACKLOG.md` estão concluídas, as regressões estão verdes, a matriz regulatória identifica implementação e evidência, e as limitações remanescentes estão publicadas. Até lá, cada funcionalidade conserva o status demonstrativo indicado por seus testes e documentos.

## Fontes oficiais consultadas

Consulta realizada em 14 de julho de 2026:

- [IFRS Foundation — IFRS 9 Financial Instruments](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/);
- [Banco Central do Brasil — Resolução CMN nº 4.966/2021](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN);
- [Banco Central do Brasil — Resolução BCB nº 352/2023](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB).

Esses links orientam o escopo, mas não substituem a matriz de rastreabilidade, a conferência da versão vigente nem os textos publicados no DOU e no Sisbacen.
