# Relatório de Contexto, Auditoria Técnica e Estado-Alvo

## Projeto `risco_bancario`

**Documento de entrada obrigatório para o Codex**  
**Repositório:** `Masteradilio/risco_bancario`  
**Data de referência da revisão:** 13 de julho de 2026  
**Documento complementar:** `docs/MASTER_BACKLOG.md`

---

## 1. Finalidade deste documento

Este relatório contextualiza o Codex sobre o estado atual do projeto `risco_bancario`, explica por que o sistema ainda deve ser tratado como um protótipo técnico e define o estado-alvo necessário para transformá-lo em uma plataforma moderna, reproduzível, auditável e tecnicamente defensável de risco de crédito e perda esperada.

O Codex deve usar este documento como fonte de contexto arquitetural, quantitativo e regulatório. A execução das mudanças deve seguir exclusivamente o plano detalhado em `docs/MASTER_BACKLOG.md`.

O objetivo final é atingir nota 10/10 nas seguintes dimensões:

1. arquitetura e qualidade de software;
2. abrangência funcional;
3. realismo da modelagem de PD;
4. realismo da modelagem de LGD;
5. realismo da modelagem de EAD;
6. cálculo de ECL por fluxo, período e cenário;
7. classificação de estágios e SICR;
8. governança, validação e monitoramento de modelos;
9. aderência demonstrável ao escopo de impairment da IFRS 9 e aos requisitos aplicáveis da Resolução CMN nº 4.966/2021 e normas complementares;
10. geração e pré-validação de reportes regulatórios, incluindo o Documento 3040;
11. segurança, rastreabilidade, desempenho e experiência de uso;
12. qualidade como projeto público de portfólio.

### 1.1 Limite da expressão “100% conforme”

Nenhum software público, alimentado apenas por dados sintéticos e sem validação independente de uma instituição financeira, pode ser honestamente certificado como “100% conforme” para uso contábil ou envio oficial ao Banco Central.

Neste projeto, o objetivo “100% IFRS 9/CMN 4.966” deve ser interpretado como:

- cobertura funcional completa do escopo declarado;
- implementação rastreável dos requisitos;
- testes automatizados e evidências de cálculo;
- documentação de premissas, limitações e julgamentos;
- ausência de valores regulatórios inventados ou preenchidos silenciosamente;
- uso de leiautes, XSDs e críticas oficiais versionados;
- preparação para validação independente e homologação institucional.

O projeto nunca deve exibir selos como “certificado pelo BACEN”, “validador oficial” ou “conformidade garantida”. A expressão permitida após a conclusão é:

> Plataforma de referência, com dados sintéticos, alinhada ao modelo de perda esperada da IFRS 9 e aos requisitos aplicáveis da CMN 4.966, preparada para calibração, validação independente e homologação institucional.

---

## 2. Hierarquia obrigatória de fontes

Antes de implementar qualquer regra contábil ou regulatória, o Codex deve consultar, nesta ordem:

1. texto vigente da IFRS 9 e materiais oficiais da IFRS Foundation;
2. Resolução CMN nº 4.966/2021, em sua versão consolidada e vigente;
3. Resolução BCB nº 352/2023 e alterações vigentes;
4. instruções, leiautes, XSDs, críticas e manuais oficiais do SCR/Documento 3040;
5. demais normas BCB/CMN citadas pelos documentos oficiais;
6. documentos técnicos de organismos como BIS/Comitê de Basileia, apenas como orientação técnica;
7. literatura acadêmica para métodos estatísticos;
8. fontes secundárias apenas como apoio, nunca como autoridade normativa.

A IFRS Foundation identifica a IFRS 9 como norma vigente em 2026 e informa que o padrão cobre classificação e mensuração, impairment por perdas esperadas e outros aspectos de instrumentos financeiros. O repositório deve manter uma matriz de rastreabilidade que vincule cada requisito implementado ao documento oficial, versão, data de vigência, código, teste e evidência.

---

## 3. Visão geral do projeto atual

O repositório já contém uma plataforma extensa com:

- módulo PRINAD de classificação de risco e PD;
- motor de perda esperada;
- LGD segmentado;
- EAD e fatores de conversão de crédito;
- grupos homogêneos;
- cenários forward-looking;
- regras de estágio, cura, renegociação, write-off e arrasto;
- geração de XML do Documento 3040;
- APIs FastAPI;
- frontend React/Electron e cópias anteriores em Next.js;
- autenticação, RBAC, auditoria e agentes de IA;
- Docker Compose;
- testes unitários e de integração;
- documentação e arquivos de pesquisa.

A abrangência é um ponto forte. Entretanto, a implementação mistura protótipos, regras heurísticas, dados sintéticos circulares, constantes declaradas como regulatórias sem evidência suficiente e componentes duplicados. O sistema demonstra boa engenharia de produto, mas o núcleo quantitativo ainda não representa um motor bancário realista de ECL.

---

## 4. Avaliação inicial

| Dimensão | Nota atual estimada | Estado-alvo |
|---|---:|---:|
| Arquitetura de software | 7/10 | 10/10 |
| Abrangência funcional | 8/10 | 10/10 |
| Realismo da modelagem de PD | 2/10 | 10/10 |
| Realismo da modelagem de LGD | 3/10 | 10/10 |
| Realismo da modelagem de EAD | 3/10 | 10/10 |
| Motor de ECL | 3/10 | 10/10 |
| Staging/SICR | 4/10 | 10/10 |
| Forward-looking | 3/10 | 10/10 |
| Validação Doc3040 | 2/10 | 10/10 |
| Governança e validação quantitativa | 3/10 | 10/10 |
| Segurança e rastreabilidade | 7/10 | 10/10 |
| Potencial como portfólio | 8/10 | 10/10 |

Essas notas não são certificação. Elas servem para orientar a priorização técnica.

---

## 5. Pontos fortes que devem ser preservados

### 5.1 Boa decomposição funcional

O projeto já reconhece que perda esperada depende de PD, LGD, EAD, estágio, horizonte, cenário econômico e regras de recuperação. Essa visão modular é correta e deve ser mantida.

### 5.2 Plataforma, APIs e interface já existentes

Há uma base útil de FastAPI, frontend, autenticação, perfis, logs, dashboards e Docker. O trabalho principal deve substituir o núcleo quantitativo e reorganizar a arquitetura sem descartar funcionalidades válidas.

### 5.3 Preocupação com explicabilidade e observabilidade

O repositório já contém SHAP, métricas, PSI, backtesting inicial, relatórios e trilhas de auditoria. Esses componentes devem evoluir para uma governança quantitativa completa.

### 5.4 Cobertura de temas regulatórios relevantes

Cura, write-off, arrasto por contraparte, múltiplos cenários, grupos homogêneos e reportes já aparecem no código. O backlog deve transformar essas ideias em implementações consistentes, testáveis e documentadas.

---

## 6. Fraquezas críticas do estado atual

### 6.1 O ECL é calculado como produto escalar

O fluxo principal usa essencialmente:

```text
ECL = PD ajustada × LGD × EAD
```

Esse cálculo é útil para ilustração, mas não representa um motor completo de IFRS 9. O estado-alvo deve calcular, por cenário e período:

```text
ECL = soma_cenarios(
        peso_cenario ×
        soma_periodos(
            PD_marginal × LGD_periodo × EAD_periodo × fator_desconto
        )
      )
```

O cálculo deve considerar:

- fluxo contratual;
- amortização;
- juros e tarifas;
- prepagamento;
- utilização adicional de limites;
- probabilidade marginal de default;
- recuperação esperada;
- garantias e custos;
- prazo de recuperação;
- taxa efetiva de juros original;
- pesos e não linearidades de cenários.

### 6.2 Inconsistência entre LGD exibida e ECL calculado

No pipeline atual, o ECL pode ser calculado antes da aplicação do fator forward-looking de LGD, enquanto o objeto final exibe uma LGD já multiplicada por esse fator. Isso permite que:

```text
PD exibida × LGD exibida × EAD exibida != ECL exibido
```

Essa inconsistência deve ser eliminada e coberta por testes de reconciliação.

### 6.3 Forward-looking baseado em spreads fixos

Os cenários atuais usam pesos e multiplicadores fixos para PD e LGD. Os indicadores macroeconômicos são coletados, mas não dirigem de modo estatisticamente estimado as curvas de risco.

O estado-alvo deve:

- gerar ou receber trajetórias macroeconômicas por período;
- estimar a relação entre macroeconomia e PD/LGD/EAD por segmento;
- calcular o ECL integral de cada cenário;
- ponderar os valores de ECL, e não apenas multiplicadores médios;
- permitir pesos configuráveis, versionados e aprovados;
- medir sensibilidade e não linearidade.

### 6.4 Base de PD sintética e circular

O gerador atual cria um perfil latente de risco e usa esse mesmo perfil para gerar tanto as variáveis explicativas quanto o target. Isso produz separação artificial e métricas muito elevadas, sem representar capacidade preditiva real.

O novo gerador deve criar uma população longitudinal de contratos e clientes. O default deve emergir de uma dinâmica temporal probabilística, com variáveis observáveis disponíveis na data de observação, e não de uma classe estática que simultaneamente determina features e target.

### 6.5 Vazamento entre calibração, seleção de limiar e teste

O modelo atual usa o conjunto de teste para calibração e também para seleção do threshold e reporte final. O estado-alvo deve separar:

- treino;
- validação de hiperparâmetros;
- calibração;
- teste out-of-time;
- backtesting futuro.

A PD é uma probabilidade e deve ser avaliada principalmente por calibração, além de discriminação.

### 6.6 PD lifetime aproximada por maturidade fixa

A PD lifetime atual pode ser derivada de uma PD de 12 meses com maturidade fixa de cinco anos. Isso ignora o prazo real do contrato, a estrutura temporal da PD, risco concorrente, amortização, cura e efeitos macroeconômicos.

O estado-alvo deve produzir curvas mensais de:

- hazard;
- PD marginal;
- PD acumulada;
- sobrevivência;
- lifetime PD por contrato.

### 6.7 SICR baseado em limites absolutos

O estágio principal é definido por atraso ou nível absoluto de PRINAD. SICR exige comparação do risco atual com o risco no reconhecimento inicial, considerando a vida remanescente.

O novo motor deve usar:

- lifetime PD na originação;
- lifetime PD atual;
- variação absoluta e relativa;
- downgrade de rating;
- atraso como backstop;
- watchlist;
- renegociação/concessão;
- eventos qualitativos;
- arrasto por contraparte;
- low-credit-risk exemption configurável;
- cura e período de observação;
- justificativa completa e versão da política.

### 6.8 Stage 3 tratado como Stage 2 com maior severidade

O estado-alvo deve calcular Stage 3 por déficit de caixa:

```text
perda = valor contábil bruto
        - valor presente dos recebimentos e recuperações esperados
```

O fluxo deve considerar cobranças, acordos, garantias, custos legais, tempo de recuperação, write-off, recuperações pós-baixa e juros sobre base líquida quando aplicável.

### 6.9 LGD baseada em tabelas e heurísticas

O projeto possui constantes de LGD por produto/garantia e árvores de decisão, mas não um modelo de workout LGD baseado em recuperações descontadas.

O estado-alvo deve gerar e modelar:

- eventos de default;
- fluxos de recuperação;
- tipo e valor de garantia;
- haircuts;
- custos de cobrança e execução;
- tempo até recuperação;
- curas;
- write-offs;
- downturn e forward-looking;
- LGD realizada e estimada.

### 6.10 EAD estática

A EAD atual é principalmente saldo utilizado mais limite não utilizado multiplicado por CCF fixo. O estado-alvo deve projetar:

- saldo amortizado por período;
- drawdown antes do default;
- cancelamento de limite;
- comportamento de utilização;
- prepagamento;
- CCF estimado por segmento e horizonte;
- EAD marginal no período do default.

### 6.11 Reporte Doc3040 demonstrativo

O gerador atual contém diversos valores default e aproximações. Existe inclusive lógica que registra uma fração arbitrária do ECL como perda reconhecida. A validação principal é estrutural e não garante aprovação oficial.

O novo módulo deve:

- usar schema de entrada completo;
- rejeitar campos ausentes;
- nunca inventar dados regulatórios;
- carregar XSD e críticas por versão/data de vigência;
- validar domínios, totalizadores e consistência semântica;
- gerar arquivo apenas quando todas as dependências estiverem disponíveis;
- produzir relatório de reconciliação;
- identificar-se como pré-validador até homologação externa.

### 6.12 Testes atuais são predominantemente estruturais

Os testes verificam existência de campos, faixas e componentes, mas não demonstram correção quantitativa.

O estado-alvo precisa de:

- golden cases calculados manualmente;
- testes de propriedades matemáticas;
- reconciliação contrato/carteira/contabilidade;
- testes de cenários;
- testes de desconto;
- backtesting de PD, LGD, EAD e ECL;
- validação out-of-time;
- testes XSD e críticas oficiais;
- testes de carga e E2E.

### 6.13 Documentação superestima conformidade

O projeto atribui percentuais de conformidade sem metodologia independente. Há também exemplos matemáticos incorretos em documentos de pesquisa.

Todo conteúdo deve ser revisado. Percentuais autodeclarados devem ser removidos e substituídos por uma matriz de evidências.

### 6.14 Duplicação e inconsistência arquitetural

Há múltiplas versões do PRINAD, frontends de backup, constantes repetidas e regras de estágio diferentes em módulos distintos. Isso cria risco de divergência.

O estado-alvo deve possuir uma única implementação canônica para cada conceito e manter componentes antigos apenas em diretório `legacy/`, até a remoção definitiva.

---

## 7. Estado-alvo quantitativo

### 7.1 PD

O módulo de PD deve produzir curvas por contrato ou segmento:

- hazard mensal;
- sobrevivência;
- PD marginal;
- PD acumulada em 12 meses;
- PD acumulada lifetime;
- PD PIT por cenário;
- rating e faixa de calibração;
- intervalos de confiança quando aplicável.

Métodos aceitos:

- regressão logística temporal;
- discrete-time hazard;
- survival analysis;
- matrizes de transição;
- gradient boosting com calibração, desde que interpretável e validado.

Deve existir um baseline simples e explicável antes de modelos complexos.

### 7.2 LGD

A LGD deve ser baseada no valor presente das recuperações líquidas:

```text
LGD = 1 - VP(recuperações líquidas) / EAD no default
```

O sistema deve suportar:

- LGD de cura;
- LGD de write-off;
- modelos one-stage e two-stage;
- garantias;
- custos;
- tempo de recuperação;
- cenários macroeconômicos;
- downturn como análise separada do ECL contábil.

### 7.3 EAD

A EAD deve ser projetada por período e produto:

- operações amortizadas;
- cartões e limites rotativos;
- cheque especial;
- compromissos não sacados;
- garantias financeiras;
- pré-pagamento;
- drawdown;
- CCF comportamental.

### 7.4 ECL

O motor deve calcular:

- Stage 1: lifetime losses associadas a eventos de default possíveis nos próximos 12 meses;
- Stage 2: lifetime ECL;
- Stage 3: lifetime cash shortfall com recuperação descontada;
- POCI: abordagem específica de perdas ao longo da vida;
- ECL individual e coletivo;
- ECL por cenário e consolidado;
- ECL bruto, overlays e ECL final;
- provisão mínima regulatória separada do cálculo econômico/contábil quando aplicável.

### 7.5 Taxa de desconto

Os déficits de caixa devem ser descontados pela taxa efetiva de juros original ou aproximação apropriada, com regras específicas para instrumentos variáveis, modificados e POCI.

---

## 8. Estado-alvo de dados sintéticos

Como não haverá dados bancários reais, a fábrica de dados sintéticos é parte central do produto.

Ela deve gerar um histórico longitudinal, determinístico e reproduzível contendo:

### 8.1 Entidades

- clientes PF e PJ;
- contrapartes e grupos econômicos;
- contratos;
- produtos;
- limites;
- garantias;
- pagamentos;
- atrasos;
- reestruturações;
- ratings;
- dados de originação;
- eventos de default;
- cobranças;
- recuperações;
- write-offs;
- indicadores macroeconômicos;
- versões de política e modelo.

### 8.2 Dimensão temporal

- safras mensais de originação;
- snapshots mensais;
- horizonte mínimo de 8 a 10 anos;
- ciclos de expansão, estabilidade, recessão e recuperação;
- mudanças de comportamento antes do default;
- defaults e recuperações em períodos futuros.

### 8.3 Prevenção de vazamento

- features devem usar apenas informação disponível na data de observação;
- targets devem ser derivados de eventos posteriores;
- variáveis latentes do gerador não podem ser entregues ao modelo;
- o gerador deve ser separado dos pipelines de modelagem;
- deve existir um teste automático de temporal leakage.

### 8.4 Datasets obrigatórios

1. `clients.parquet`;
2. `contracts.parquet`;
3. `monthly_snapshots.parquet`;
4. `payments.parquet`;
5. `delinquencies.parquet`;
6. `defaults.parquet`;
7. `recoveries.parquet`;
8. `collateral.parquet`;
9. `limits_and_drawdowns.parquet`;
10. `macro_scenarios.parquet`;
11. `writeoffs.parquet`;
12. `regulatory_reporting_input.parquet`;
13. datasets derivados para treino, validação, calibração, OOT e backtesting.

### 8.5 Golden datasets

Devem existir pequenas carteiras com resultados conhecidos manualmente:

- empréstimo amortizado Stage 1;
- contrato Stage 2 com lifetime ECL;
- contrato Stage 3 com recuperações;
- cartão rotativo com CCF;
- contrato com garantia;
- contrato modificado;
- POCI;
- carteira com três cenários;
- operação com provisão mínima;
- arquivo Doc3040 válido e arquivos inválidos por regra.

---

## 9. Estado-alvo arquitetural

Estrutura recomendada:

```text
src/
├── domain/
│   ├── contracts/
│   ├── counterparties/
│   ├── cashflows/
│   ├── staging/
│   └── scenarios/
├── data/
│   ├── synthetic/
│   ├── validation/
│   └── contracts/
├── models/
│   ├── pd/
│   ├── lgd/
│   ├── ead/
│   └── sicr/
├── ecl/
│   ├── discounting/
│   ├── calculation/
│   ├── stage3/
│   └── overlays/
├── regulatory/
│   ├── cmn4966/
│   ├── bcb352/
│   ├── doc3040/
│   └── traceability/
├── validation/
│   ├── model_risk/
│   ├── backtesting/
│   ├── reconciliation/
│   └── monitoring/
├── application/
│   ├── services/
│   ├── api/
│   └── jobs/
└── infrastructure/
    ├── persistence/
    ├── observability/
    └── security/
```

Princípios obrigatórios:

- uma única fonte de verdade para cada regra;
- modelos de domínio tipados;
- uso de `Decimal` para valores monetários e política explícita de arredondamento;
- datas de referência e versões em todos os resultados;
- separação entre cálculo econômico, overlay gerencial, piso regulatório e reporte;
- regras configuráveis fora do código;
- nenhuma dependência silenciosa de mock;
- nenhuma chamada externa dentro do cálculo determinístico sem cache/versionamento;
- reprodutibilidade por seed, versão de dados e versão de modelo.

---

## 10. Estado-alvo de governança

Cada modelo deve possuir:

- model card;
- objetivo e uso permitido;
- população e exclusões;
- definição de target;
- dados e período;
- metodologia;
- hiperparâmetros;
- calibração;
- limitações;
- resultados de validação;
- testes de sensibilidade;
- critérios de aprovação;
- data de vigência;
- responsável;
- versão;
- trilha de mudança;
- plano de monitoramento;
- critérios de recalibração e retreinamento.

O sistema deve separar:

- desenvolvimento;
- validação independente simulada;
- aprovação;
- implantação;
- monitoramento;
- desativação.

Como o projeto é individual, a “validação independente” deve ser simulada por um pipeline separado, com regras que impeçam a aprovação automática pelo mesmo processo de desenvolvimento.

---

## 11. Estado-alvo regulatório

### 11.1 Matriz de rastreabilidade

Cada requisito deve possuir:

- identificador interno;
- norma;
- artigo/parágrafo;
- resumo;
- aplicabilidade;
- implementação;
- teste;
- evidência;
- status;
- versão da norma;
- data de revisão.

### 11.2 Versionamento regulatório

O repositório deve guardar metadados de versão, não cópias não autorizadas de conteúdo protegido. XSDs e arquivos públicos permitidos podem ser armazenados conforme licença e política da fonte.

### 11.3 Doc3040

A geração deve ser bloqueada quando:

- o leiaute não estiver configurado;
- o XSD não estiver disponível;
- campos obrigatórios estiverem ausentes;
- houver falha de reconciliação;
- a versão do leiaute não corresponder à data-base;
- existirem críticas semânticas impeditivas.

---

## 12. Estado-alvo de testes

A suíte deve conter:

### 12.1 Testes unitários

- fórmulas;
- curvas;
- desconto;
- arredondamento;
- staging;
- cashflows;
- cenários;
- exportação.

### 12.2 Testes quantitativos

- monotonicidade;
- limites de PD/LGD/EAD;
- reconciliação;
- calibração;
- discriminação;
- estabilidade;
- backtesting;
- sensibilidade;
- benchmark contra cálculo manual.

### 12.3 Testes de integração

- dados → modelos → ECL → persistência → API → reporte;
- reprocessamento idempotente;
- versionamento;
- falhas externas;
- migrações de banco.

### 12.4 Testes E2E

- execução de uma carteira sintética completa;
- visualização de resultados;
- aprovação simulada;
- exportação;
- auditoria.

### 12.5 Testes não funcionais

- carga;
- concorrência;
- segurança;
- dependências;
- recuperação de falhas;
- observabilidade.

---

## 13. Critérios objetivos para nota 10/10

### 13.1 Arquitetura 10/10

- sem implementações canônicas duplicadas;
- domínio tipado e modular;
- ADRs e diagramas atualizados;
- cobertura mínima acordada;
- CI verde;
- migrações e APIs versionadas.

### 13.2 PD 10/10

- dados longitudinais sem leakage;
- split temporal;
- calibração independente;
- curvas mensais;
- OOT e backtesting;
- model card e validação.

### 13.3 LGD 10/10

- workout LGD descontada;
- recuperações, custos e garantias;
- cura/write-off;
- backtesting e segmentação;
- cenários e sensibilidade.

### 13.4 EAD 10/10

- projeção temporal;
- CCF estimado;
- produtos amortizados e rotativos;
- drawdown e prepagamento;
- backtesting.

### 13.5 ECL 10/10

- cálculo período a período;
- desconto pela EIR;
- cenários completos;
- Stage 1, 2, 3 e POCI;
- individual e coletivo;
- reconciliação e golden cases.

### 13.6 Regulação 10/10

- matriz de rastreabilidade completa;
- regras versionadas;
- nenhum valor inventado;
- pré-validação XSD e semântica;
- evidências por requisito;
- revisão de vigência automatizada ou documentada.

### 13.7 Produto 10/10

- instalação em um comando;
- demo reproduzível;
- interface clara;
- documentação para recrutador, desenvolvedor, cientista de dados e auditor;
- resultados explicitamente sintéticos;
- relatório final de limitações.

---

## 14. Regras permanentes para o Codex

1. Não declarar conformidade sem evidência.
2. Não inventar artigos, percentuais, pisos, códigos, XSDs ou regras.
3. Não utilizar fontes secundárias como autoridade normativa.
4. Não manter duas implementações oficiais para a mesma regra.
5. Não usar o conjunto de teste para treino, tuning, calibração ou seleção de threshold.
6. Não expor variáveis latentes do gerador sintético aos modelos.
7. Não preencher campos regulatórios ausentes com defaults silenciosos.
8. Não apagar o legado antes de concluir testes de equivalência ou registrar a remoção.
9. Não alterar fórmulas sem atualizar documentação, testes, model cards e matriz regulatória.
10. Sempre atualizar `docs/MASTER_BACKLOG.md`, `CHANGELOG.md` e os documentos afetados.
11. Sempre executar testes de regressão antes de concluir uma tarefa.
12. Sempre registrar premissas e decisões relevantes em ADRs.
13. Sempre produzir commits pequenos, rastreáveis e com mensagens descritivas.
14. Nunca incluir dados pessoais reais, segredos ou artefatos proprietários no repositório.

---

## 15. Resultado esperado

Ao final do backlog, o repositório deverá permitir que qualquer avaliador execute uma carteira sintética completa e acompanhe:

1. geração longitudinal dos dados;
2. construção dos datasets de modelagem;
3. treinamento, calibração e validação de PD, LGD, EAD e SICR;
4. geração de curvas por período e cenário;
5. classificação de estágio;
6. cálculo de ECL descontado;
7. aplicação separada de overlays e requisitos regulatórios;
8. reconciliação;
9. monitoramento e backtesting;
10. geração e pré-validação de reporte regulatório;
11. visualização por API e frontend;
12. trilha de auditoria e pacote de evidências.

Esse resultado transformará o projeto de uma POC extensa, porém heurística, em uma plataforma de referência quantitativa e regulatória de alto nível para portfólio, estudos, entrevistas e futura adaptação a dados institucionais.
