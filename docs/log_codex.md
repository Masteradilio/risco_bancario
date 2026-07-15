PROMPT DO USUARIO:

Leia integralmente `docs/PROJECT_AUDIT_AND_TARGET_STATE.md` e `docs/MASTER_BACKLOG.md`. Assuma a modernização do projeto seguindo a ordem, as regras de execução, os critérios de aceite e a Definition of Done definidos nesses documentos. Comece pela Fase 0, inspecione o estado real do repositório, atualize o plano quando necessário e execute uma tarefa por vez, sempre com testes, documentação, atualização do backlog e changelog, commit e push. Use o ambiente venv do projeto para executar os comandos de terminal que forem necessários. Sua meta estará cumprida quando o backlog for executado por completo, todos os testes de regressão passarem, changelog atualizado e repositório github sincronizado com a main.


RESPOSTA DO CODEX:

Vou assumir a modernização como uma meta contínua e começar pela Fase 0, seguindo os dois documentos como contrato de execução. Primeiro vou registrar a meta, ler integralmente os documentos, conferir memória relevante e confrontar o backlog com o estado real do repositório antes de tocar em qualquer arquivo.


A tarefa já possui uma meta ativa no sistema; vou reutilizá-la em vez de criar uma segunda. Agora sigo com a leitura integral e o inventário do repositório.


A primeira inspeção revelou dois fatos importantes: a main está limpa em relação ao remoto, mas os dois documentos de governança estão ainda não rastreados; portanto, eles fazem parte do estado de trabalho que preciso preservar e integrar. A saída combinada ficou truncada, então vou reler ambos em blocos controlados e extrair exatamente as regras da Fase 0, sem depender de resumo parcial.




Os documentos foram lidos integralmente. A primeira unidade de trabalho será somente a Tarefa 0.1: preservar o commit-base, medir a suíte atual no venv, inventariar componentes e produzir um baseline verificável. Não vou antecipar 0.2 ou 0.3; ao fechar 0.1, atualizarei backlog/changelog, farei commit e push antes de seguir.




O commit-base é 265cb64, idêntico a origin/main, e o ambiente do projeto é venv com Python 3.13.7. Vou agora criar a referência imutável de preservação e a branch descritiva da Tarefa 0.1; depois executo a suíte exatamente nesse ambiente e registro as falhas como evidência, sem “consertá-las” fora do escopo do baseline.




O baseline já detectou 232 testes coletáveis e 8 erros de coleta. As causas imediatas são ambiente incompleto (python-jose e matplotlib ausentes apesar de declarados) e um teste diagnóstico com import absoluto inválido. Vou separar as suítes por módulo para distinguir falha de infraestrutura de regressões funcionais e também verificar build/lint do frontend, configuração Docker e imports dos serviços.




O retrato funcional está claro: DDL e PRINAD passam; perda esperada tem 92 aprovações e 10 falhas de integração; Propensão nem coleta por dependência ausente; PRINAD v2 tem 5 erros por fixtures inexistentes; frontend não compila e o lint não está instalável a partir do manifesto atual. Vou completar o inventário com contagens e uma tentativa controlada de build dos containers, depois escrever o relatório e fechar apenas a Tarefa 0.1.




O inventário final também confirmou 558 arquivos rastreados, 4 serviços declarados no Compose, 2 frontends concorrentes, 3 conjuntos de artefatos/modelos duplicados e 27 scripts SQL. O Docker Desktop não está ativo e o Compose aponta para um frontend/Dockerfile inexistente; ambos serão registrados como bloqueios reproduzíveis, não mascarados. Agora vou materializar o baseline, marcar somente 0.1 e atualizar o changelog.




Editou arquivos


A verificação documental passou (git diff --check sem erros; apenas aviso de CRLF já esperado no Windows). O relatório preserva todas as falhas como preexistentes e não altera código. Vou fazer o commit pequeno da Tarefa 0.1 e publicar a branch antes de iniciar 0.2, exatamente como exige o fluxo do backlog.




A Tarefa 0.1 está commitada em 51f4276 e publicada em origin/codex/phase-0-baseline; a tag de restauração também está no remoto. Inicio agora somente a Tarefa 0.2: confrontar o README e os módulos reais, definir fronteiras incluídas/excluídas/futuras e criar o glossário oficial, com linguagem regulatória conservadora.




A inspeção confirma que o README hoje sugere cobertura integral e mistura impairment, classificação/mensuração, Basileia e otimização comercial. Para a definição de escopo, vou checar somente fontes oficiais atuais da IFRS Foundation e do Banco Central/CMN; isso evita cristalizar no glossário uma interpretação regulatória desatualizada.




Pesquisou na web


As fontes oficiais confirmam a fronteira correta: a IFRS 9 é mais ampla que impairment e também cobre classificação/mensuração e hedge; por isso o núcleo deste produto será impairment/ECL, com classificação e mensuração apenas como extensão necessária, enquanto hedge accounting ficará explicitamente fora do escopo inicial. A Resolução BCB 352 também teve alterações posteriores, então o documento exigirá verificação de vigência em vez de congelar regras no texto de escopo.




Editou arquivos


Os documentos de escopo e glossário foram criados, e o README agora declara explicitamente o núcleo, as extensões limitadas e as exclusões. Vou validar links locais, coerência das fronteiras, whitespace e a regressão funcional que já estava verde no baseline; se nada novo quebrar, faço o commit e push exclusivos da Tarefa 0.2.




A regressão passou com 118 testes aprovados e 7 ignorados. A validação de links encontrou um defeito preexistente no README: ele aponta para LICENSE, que não existe. Como isso impede a documentação da tarefa de ficar verificável, vou remover apenas esse link quebrado e repetir a checagem, sem ampliar o escopo.




Editou um arquivo


A Tarefa 0.2 foi concluída em 9593349, com 118 testes aprovados, 7 ignorados, documentação verificada e push realizado. Inicio a Tarefa 0.3 com uma varredura temática completa: selos/alegações, percentuais autodeclarados, dashboards e datasets sem rótulo sintético, além de fórmulas e exemplos matemáticos incorretos. Documentos oficiais arquivados serão preservados como fontes, não reescritos.




A varredura encontrou alegações explícitas em 27 arquivos, incluindo código ativo, frontend legado, testes e SQL — não apenas documentação. Também há métricas mockadas sem rótulo em dashboards e respostas do agente. Vou tratar primeiro as superfícies públicas e executáveis, depois documentos legados, e só marcarei 0.3 quando uma segunda varredura não encontrar promessas institucionais remanescentes.




Editou arquivos


Encontrei um risco mais sério do que texto promocional: a ferramenta do agente devolve “CONFORME” a partir de um checklist hard-coded com artigos, pisos e prazos sem rastreabilidade. Vou preservar a assinatura para não quebrar integrações, mas bloquear essa conclusão: ela passará a retornar “NÃO AVALIADO” e a identificar saídas como sintéticas até a matriz regulatória e o pré-validador versionado existirem.




Editou arquivos


A segunda frente é matemática: os documentos legados tratam PD × LGD × EAD como fórmula completa, descrevem Stage 3 como “LGD máxima” e contêm erros de ordem de grandeza (por exemplo, 8% × 40% × 10.000 foi publicado como 3.200, quando é 320). Vou corrigir os exemplos objetivos e marcar aproximações legadas como didáticas, sem reescrever ainda o motor quantitativo — isso pertence às fases posteriores.




Editou arquivos


As superfícies públicas agora usam rótulos sintéticos globais, o agente não pode mais emitir “CONFORME”, e os exemplos matemáticos inconsistentes foram corrigidos. Vou executar uma verificação proporcional: sintaxe Python, contratos de saída das ferramentas bloqueadas, regressão verde conhecida, build frontend para comparar com o baseline e varredura final de alegações. Só depois atualizo o backlog e changelog da 0.3.




A validação confirmou 118 testes aprovados e 7 ignorados, guardrails do agente funcionando e nenhuma alegação proibida na varredura final. O build frontend continua falhando exatamente nas categorias já registradas no baseline; não surgiu erro novo causado pelos rótulos adicionados. Vou registrar essa evidência, concluir a 0.3 no backlog e preparar o commit único da tarefa.




Editou arquivos


A suíte unitária de perda esperada também fechou com 82 testes aprovados. Com isso, a Tarefa 0.3 tem evidência em três camadas: 200 testes aprovados no total das suítes executadas, guardrails específicos aprovados e varredura textual sem promessas proibidas. Vou commitá-la e publicá-la agora; em seguida a Fase 0 estará encerrada e começo a Tarefa 1.1.




Contexto compactado automaticamente



A Fase 0 está concluída e publicada até o commit c1132b5. Vou iniciar a Tarefa 1.1 estritamente como mapeamento: identificar duplicações, divergências e fontes canônicas propostas, sem ainda mover ou excluir implementações.




O inventário confirma duas duplicações estruturais principais: PRINAD aparece em duas árvores quase espelhadas, inclusive com artefatos binários repetidos, e a interface existe em Vite/React e em um backup Next.js. Agora estou cruzando isso com os pontos de entrada reais e com as regras divergentes de rating, PD e estágio para não escolher uma “fonte canônica” apenas pelo nome da pasta.




Editou arquivos


As fontes ficaram definidas em dois níveis: a árvore operacional de transição e o destino em src/. Isso evita validar por acidente as regras atuais: por exemplo, encontrei quatro critérios incompatíveis de estágio e rating D começando em 85 em um módulo e 90 em outro. O documento registra essas divergências e proíbe resolvê-las silenciosamente nesta tarefa. Agora vou validar o inventário, a documentação e a regressão PRINAD antes do commit.




A Tarefa 1.1 passou nas verificações (118 passed, 7 skipped) e foi publicada no commit 1061f1f. Inicio agora a Tarefa 1.2: criar o domínio tipado e isolado, com invariantes para dinheiro, datas, percentuais e resultados ECL, sem dependências de FastAPI, banco, CSV ou frontend.




Editou arquivos


O primeiro núcleo do domínio já está verde: 8 testes cobrem imutabilidade, Decimal, arredondamento half-even, percentuais, UTC, coerência temporal, cenários e separação dos componentes ECL. A inspeção de imports também confirmou que src/domain não depende de FastAPI, pandas, NumPy, Pydantic, banco ou CSV. Vou completar o esqueleto da arquitetura-alvo e então atualizar os artefatos de controle da tarefa.




Editou arquivos


A Tarefa 1.2 foi publicada no commit cadd33f, com 126 passed, 7 skipped. Passo à Tarefa 1.3: retirar parâmetros materiais do novo núcleo e colocá-los em uma política JSON versionada, com vigência, autoria, justificativa, validação estrita e hash determinístico propagável ao resultado ECL. As divergências legadas continuarão explicitamente marcadas como demonstrativas, não “resolvidas” por conveniência.




Editou arquivos


A política estrita já rejeita pesos que não somam 1, faixas de rating descontínuas, CCF fora de [0,1], thresholds de estágio invertidos e campos não rastreados. Vou agora conectar os consumidores legados centrais a essa política, mantendo suas APIs por compatibilidade; assim o JSON deixa de ser apenas documentação e passa a ser a fonte efetiva dos parâmetros migrados.




Editou arquivos


A política agora é a fonte efetiva para rating/PD, staging, LGD, CCF e cenários, inclusive através dos adaptadores legados. Ela permanece marcada como demonstrative, com origem e justificativa explícitas; o hash SHA-256 e a versão são obrigatórios no contrato de resultado ECL. Estou na regressão final da Tarefa 1.3 antes de publicar o commit.




A Tarefa 1.3 foi publicada no commit 9057302; as regressões ficaram verdes (18 + 28 + 94 testes aprovados, 7 ignorados). Inicio a Tarefa 1.4 para padronizar Python, dependências, lint, tipos, cobertura e comandos únicos de setup/teste — incluindo corrigir as dependências ausentes que hoje bloqueiam a coleta global.




Editou arquivos


O setup reproduzível está instalando no venv as dependências declaradas no novo pyproject.toml, inclusive python-jose, matplotlib, Ruff, Black, MyPy e cobertura. A etapa é mais demorada porque o ambiente não tinha algumas dependências pesadas já declaradas pelo projeto; não houve erro até aqui.




Editou arquivos


A Fase 1 foi concluída e publicada até 82e273b. O comando único de qualidade está verde: Black, Ruff, MyPy, cobertura de 90,37%, 18 testes canônicos e 118 testes de regressão aprovados (7 ignorados). Vou iniciar a primeira tarefa da Fase 2, mantendo a mesma disciplina de um item por commit.




Pesquisou na web


A consulta oficial mostrou um ponto importante para a rastreabilidade: a página atual do Documento 3040 publica leiaute, instruções, críticas, validador e exemplos, mas o XSD explicitamente listado ali é do documento 3045. Vou registrar essa distinção sem inventar um “XSD 3040” e exigir verificação de versão antes de qualquer implementação de exportação.




Editou arquivos


A Tarefa 2.1 foi publicada no commit cef3e28, com fontes oficiais verificadas em 14/07/2026 e regressão verde. Inicio a Tarefa 2.2 transformando essas fontes em requisitos atômicos com aplicabilidade, código, teste e evidência — sem marcar como implementado aquilo que ainda está apenas planejado.




Editou arquivos


A matriz já separa claramente planned, partial e not_applicable: nenhum requisito quantitativo foi promovido artificialmente a “implementado”. Os itens parciais apontam para testes existentes; hedge accounting e transmissão oficial do 3040 têm justificativas explícitas de não aplicabilidade. Um teste de contrato da matriz está verde e impede IDs duplicados, fontes órfãs e N/A sem justificativa.




Editou arquivos


A Tarefa 2.2 foi publicada em b51beb8, com 22 requisitos rastreados e 5 testes de contrato verdes. Na Tarefa 2.3 vou tornar essa matriz executável: testes com IDs regulatórios, relatório automático e um gate de release que, neste momento, deve falhar corretamente porque os requisitos obrigatórios ainda estão planejados/parciais.




Editou arquivos


O gate regulatório está funcionando como deveria: detectou 20 bloqueadores entre os 22 requisitos e retornou falha de release. Isso não é uma regressão; é a evidência de que o projeto ainda não pode alegar cobertura regulatória completa. Corrigi o comando geral para incluir os 11 testes regulatórios sem desativar esse bloqueio de promoção.




A Fase 2 está concluída e publicada até 77bb99f; o comando geral agora executa 29 testes canônicos/regulatórios, 118 de regressão e mantém o gate de release vermelho por evidência incompleta. Inicio a Tarefa 3.1 com o desenho causal e temporal do gerador, antes de produzir qualquer dataset.




Editou arquivos


A verificação detectou apenas formatação Black no novo teste de contrato. O commit de conteúdo já foi publicado, então vou corrigir em um commit complementar e só considerar a Tarefa 3.1 concluída depois de o comando completo ficar verde.




Editou um arquivo


A Tarefa 3.1 agora está realmente verde e publicada até c7a23f1: 32 testes canônicos/regulatórios/de desenho e 118 de regressão passaram. Inicio a Tarefa 3.2 implementando somente população e contratos — PF/PJ, grupos, produtos, cronogramas, garantias, compromissos, garantias financeiras e POCI — sem antecipar snapshots ou defaults.




Editou arquivos


O gerador de população está operacional e determinístico. Na carteira de teste ele produz 16 clientes, 32 contratos, 1.536 parcelas e 8 garantias, cobrindo oito produtos e os quatro tipos de facilidade; POCI, compromissos e garantias financeiras aparecem por construção, sem depender de sorte favorável. Agora vou registrar o contrato da implementação e rodar a qualidade completa.




Editou arquivos


A Tarefa 3.2 foi publicada em ba72117, com 39 testes canônicos e 118 de regressão verdes. Inicio a Tarefa 3.3: gerar a série mensal ativa, safras, migração observável de risco e modificações; datas de default continuarão fora desta tarefa e serão derivadas desses estados na 3.4.




Editou arquivos


A série mensal está coerente na carteira de teste: 2.431 snapshots entre janeiro/2016 e dezembro/2025, 62 safras, 10 faixas de rating, atrasos até 120 dias e 6 modificações. Rating usa a política versionada, e as tabelas públicas não expõem target, data futura de default ou latentes.




Editou arquivos


A Tarefa 3.3 foi publicada em 3da8f96, com 46 testes canônicos e 118 de regressão verdes. Inicio a Tarefa 3.4 usando os snapshots como causa observável: defaults só surgem após deterioração, e cobranças, garantias, recuperações, cura, redefault e write-off serão eventos posteriores reconciliáveis.




Editou arquivos


Contexto compactado automaticamente



Continuando pela tarefa 3.4: a estrutura dos eventos de crédito já foi implementada; agora vou validar tipagem, determinismo e reconciliações, corrigir o que aparecer e só então documentar e registrar a tarefa no backlog/changelog.




Editou um arquivo


A primeira bateria encontrou um único problema de cobertura do cenário: a amostra fixa produzia curas, mas nenhum redefault. Vou tornar esse caso raro deterministicamente representado e ajustar sua ordem temporal para que o redefault anteceda a baixa subsequente.




Editou arquivos


Os cenários agora estão cobertos de forma explícita: seis fluxos mensais por default, custos operacionais e judiciais identificados, execução de garantia, cura, redefault, baixa e recuperação pós-baixa. A amostra de aceitação gerou 10 defaults iniciais, 2 redefaults e 69 recuperações, com reconciliação financeira testada.




Editou arquivos


A validação completa da tarefa 3.4 passou: 53 testes canônicos com 94,27% de cobertura e 118 testes de regressão aprovados (7 skips já conhecidos). Vou registrar este incremento isoladamente no Git e, após o push, avançar para a tarefa 3.5.




A tarefa 3.4 foi commitada e enviada no commit 5af32b0. Iniciei a 3.5 inspecionando primeiro os contratos de cenário, a política versionada e qualquer macroeconomia legada, para reutilizar conceitos sem criar uma segunda regra canônica.




Editou arquivos


A implementação da 3.5 já passou nos testes focados. Ela preserva os três pesos probabilísticos canônicos (15%/70%/15%) e trata stress como trajetória de sensibilidade com peso zero, evitando alterar silenciosamente a política de ECL; todo o histórico continua claramente rotulado como sintético, não como série oficial observada.




Editou arquivos


A regressão da tarefa 3.5 também está verde: 60 testes canônicos, 94,26% de cobertura, e os mesmos 118 testes legados aprovados com 7 skips conhecidos. Vou fechar esse incremento em commit próprio e seguir para a construção dos datasets da tarefa 3.6.




Editou arquivos


A inspeção dos dados de aceitação revelou uma lacuna real: a amostra tinha datasets de EAD, mas nenhum default em produto com limite não utilizado, portanto nenhum target de CCF. Vou corrigir o gerador para garantir cobertura determinística desse caso sem usar informação futura como feature.




Editou arquivos


A lacuna de CCF foi fechada: a carteira fixa agora contém 11 defaults iniciais e ao menos um default em exposição com limite, permitindo um target de CCF verificável. Os datasets ficaram com cortes temporais disjuntos e sem campos de resultado futuro nas features de PD/SICR.




A tarefa 3.6 passou na regressão completa: 67 testes canônicos, 95,07% de cobertura, 118 regressões aprovadas e 7 skips conhecidos. Vou publicar o commit da tarefa e então executar a última tarefa da Fase 3, dedicada a integridade, anti-leakage, distribuição e data cards.




A tarefa 3.6 foi publicada no commit 3adb28b. Na 3.7 vou transformar os guardrails em validações executáveis: chaves e temporalidade entre tabelas, detector de features futuras, diagnósticos de distribuição/correlação e documentação de cada campo e limitação.




Editou arquivos


A auditoria cruzada dos dois documentos revelou uma lacuna no backlog original: o estado-alvo exige Parquets obrigatórios e manifesto reproduzível, mas nenhuma tarefa os materializava. Registrei a nova tarefa 3.8 no próprio backlog; a 3.7 permanece isolada e já passou nos 8 testes focados.




A tarefa 3.7 foi publicada no commit 6088181 com 75 testes canônicos verdes e 94,32% de cobertura. Começo agora a 3.8, materializando os artefatos exigidos pelo estado-alvo e verificando primeiro as bibliotecas já disponíveis no venv.




Editou arquivos


A materialização determinística passou nos 5 testes: 24 Parquets mais manifesto, com hashes, schemas e contagens; duas execuções idênticas geraram os mesmos bytes. O insumo regulatório ficou deliberadamente neutro — contém apenas dados-fonte sintéticos e nenhum COSIF/IPOC/CEP ou código Doc3040 inventado.




Editou arquivos


A Fase 3 está aceita: 81 testes canônicos passaram com 93,67% de cobertura; 118 regressões legadas passaram e 7 skips conhecidos permaneceram. O pacote versionado está presente no repositório e seus hashes foram revalidados. Vou publicar a tarefa 3.8 antes de iniciar a Fase 4.




Editou um arquivo


A Fase 3 foi publicada no commit f8821a0. Inicio a Fase 4 pela tarefa 4.1, comparando o cronograma sintético atual, os modelos canônicos de contrato/fluxo e os motores financeiros legados antes de escolher o ponto único de implementação.




Editou arquivos


O núcleo financeiro passou nos 8 testes focados, mas o MyPy apontou que a normalização feita no __post_init__ não estreita automaticamente os tipos de entrada DecimalInput. Vou explicitar esses valores normalizados no motor antes da regressão completa.




Editou arquivos


A tarefa 4.1 está funcional: Price, SAC e bullet reconciliam saldo; taxa variável usa resets explícitos; tarifas entram na EIR; e calendário/convenção de dias são configuráveis. Os 8 testes focados e a tipagem estrita passaram, então sigo para a regressão integral antes do commit.




A regressão completa da tarefa 4.1 passou: 89 testes canônicos, 93,23% de cobertura, 118 regressões aprovadas e 7 skips conhecidos. Vou publicar o incremento e avançar para produtos rotativos na tarefa 4.2.




A tarefa 4.1 foi publicada no commit 37009cc; a Fase 4 agora segue na branch codex/phase-4-contract-engine. Para a 4.2, vou modelar limite e saldo como estados separados, com drawdown limitado à disponibilidade, cancelamento apenas da parcela não utilizada e pagamento mínimo auditável.




Editou arquivos


A tarefa 4.2 passou nos 6 testes focados e na tipagem: drawdowns são limitados à disponibilidade, cancelamentos não atravessam o saldo, pagamentos são alocados a juros/principal e shortfalls ficam explícitos. Vou executar agora a regressão integral.




A tarefa 4.2 foi publicada no commit dfbb6cd. Inicio a 4.3 separando dois eventos: prepagamento, que reduz/encerra o saldo e reprojeta o prazo remanescente; e modificação, que calcula ganho/perda e distingue continuidade com EIR original de baixa com novo reconhecimento.




Editou arquivos


A tarefa 4.3 passou nos 5 testes focados. O motor não decide arbitrariamente a baixa: essa decisão é um input de política; sem baixa, a EIR original é preservada, e com baixa são exigidos valor justo e nova EIR. Vou validar agora toda a regressão.




A tarefa 4.3 foi publicada no commit 0bb645b; a regressão alcançou 100 testes canônicos verdes. A última tarefa da Fase 4 será um pacote golden independente, com contratos pequenos e valores esperados linha a linha para detectar regressões de fórmula e arredondamento.




Editou arquivos


Os golden cases estáticos passaram nos 3 testes: nove linhas de Price/SAC/bullet conferidas campo a campo com tolerância de R$ 0,01, além das identidades de fluxo e saldo. Vou rodar a regressão completa para aceitar a Fase 4.




A Fase 4 foi publicada no commit 8a3ed7a, com 103 testes canônicos e golden cases aceitos. Inicio a Fase 5 em branch própria; como a tarefa 5.1 formaliza conceitos contábeis/regulatórios, vou validar a política contra fontes oficiais e a matriz de rastreabilidade antes de codificá-la.




Pesquisou na web


A leitura oficial confirma dois guardrails centrais: default deve ser consistente com a gestão interna e não posterior ao backstop de 90 dias da IFRS 9; no escopo CMN/BCB, “atraso superior a 90 dias” implica operacionalmente 91 dias, além dos indicadores qualitativos de improvável pagamento. Critérios de cura precisam ser verificáveis; o período operacional não será apresentado como exigência normativa.




Editou arquivos


A política formal já passou nos 8 testes focados. A integração encontrou duas inconsistências anteriores que precisam ser corrigidas nesta mesma tarefa: o gerador disparava default exatamente em 90 dias (a política CMN usa “superior a 90”) e o dataset padrão de PD incluía POCI. Vou alinhar ambos e regenerar o pacote sintético versionado.




Editou arquivos


A primeira regressão revelou que o script de qualidade ainda não incluía tests/models nem o novo pacote de PD no MyPy. Corrigi o próprio gate; agora a tarefa só será aceita com esses testes realmente integrados à suíte canônica.




Editou um arquivo


A regressão corrigida passou com os testes de PD realmente incluídos: 111 testes canônicos, 93,01% de cobertura, 118 regressões aprovadas e 7 skips conhecidos. Também registrei a alteração BCB 504/2025 no catálogo de fontes para sustentar a exceção de cura de baixa frequência.




A tarefa 5.1 foi publicada no commit 28f9d97. Inicio a 5.2 verificando primeiro a prevalência de default por split, porque um baseline logístico/hazard só é defensável se treino, validação e calibração contiverem eventos suficientes; se algum corte não suportar estimação, isso deve aparecer como bloqueio mensurável, não ser mascarado.




A prevalência por split mostrou um bloqueio concreto: o OOT tinha zero defaults não-POCI, tornando discriminação e calibração impossíveis. A causa é o gerador concentrar eventos nos contratos POCI. Vou adicionar choques de cobertura determinísticos em contratos longos não-POCI, distribuídos por safra, mantendo-os independentes das features futuras.




Editou arquivos


Os dois baselines treinam de forma determinística. Na validação, a logística 12m teve ROC AUC 0,755 e Brier 0,177; o hazard teve apenas 3 eventos, ROC AUC 0,611 e forte subestimação. Esses números serão registrados como diagnóstico sintético preliminar, não como performance aprovada. A escala R1–R5 foi derivada dos quintis de PD na calibração e traz taxa observada por faixa.




Editou arquivos


A regressão da tarefa 5.2 passou: 116 testes canônicos, 93,09% de cobertura, 118 regressões aprovadas e 7 skips conhecidos. O pacote sintético regenerado agora possui eventos não-POCI em todos os splits; as métricas permanecem qualificadas como preliminares.




A tarefa 5.2 foi publicada no commit 873eb6b. Na 5.3, vou manter OOT/backtesting intocados: gradient boosting será ajustado no treino e calibrado apenas no split de calibração; a comparação de candidatos usará evidência de validação pré-calibração e o registry marcará todos como challengers até a avaliação temporal formal.




Editou arquivos


Contexto compactado automaticamente



Continuando na Tarefa 5.3: vou confirmar se a documentação e os registros foram aplicados após a interrupção, executar a regressão completa no venv e só então consolidar commit e push antes de avançar.




A Tarefa 5.3 passou pela suíte completa: 121 testes canônicos, cobertura de 93,22%, além de 118 testes legados aprovados e 7 skips esperados. O challenger calibrado permanece explicitamente não promovido; agora vou validar o diff final e sincronizar esse incremento.




A Tarefa 5.3 foi commitada (73d0e0d) e enviada ao remoto. Inicio agora a Tarefa 5.4, primeiro auditando os cortes temporais e as janelas de desfecho para eliminar vazamento, manter calibração separada do OOT e definir a técnica de calibração por evidência — sem reutilizar o OOT já consumido.




A auditoria encontrou um problema real no desenho anterior: os cinco blocos eram ordenados, mas adjacentes, de modo que janelas de target de 12 meses atravessavam o bloco seguinte. Vou corrigir o plano da Tarefa 5.4 com “purged time splits”: anos de embargo entre treino, validação, calibração e OOT; backtesting futuro ficará identificável, mas sem rótulo 12m falsamente completo. Isso altera a fábrica e exige regenerar o pacote Parquet e atualizar as evidências anteriores.




Editou arquivos


O protocolo purgado está implementado e o pacote sintético foi regenerado. A evidência é conservadora: isotonic venceu a seleção interna, mas colapsou no OOT da logística para AUC 0,50 e PD constante; mantive o resultado como blocker e não reabri a escolha usando o teste. Agora executo a regressão completa da Tarefa 5.4.




A Tarefa 5.4 passou integralmente: 126 testes canônicos, cobertura de 93,12%, 118 testes legados aprovados e 7 skips esperados. O manifesto confirma modelagem 0.2.0, 1.026 linhas e targets futuros nulos no Parquet. Vou consolidar e enviar essa tarefa antes de iniciar as curvas de PD.




A Tarefa 5.4 foi commitada (27764ec) e enviada ao remoto. Inicio a Tarefa 5.5: construir curvas mensais coerentes de hazard, sobrevivência, PD marginal/acumulada e lifetime PD limitada ao prazo contratual, preservando o blocker de calibração — as curvas serão demonstrativas, não “corrigidas” com OOT.




Antes de codificar 5.5, a revisão cruzada encontrou registros históricos da Fase 3 ainda descrevendo os cortes antigos. Vou corrigir essa inconsistência documental como complemento da 5.4 e sincronizá-la separadamente; o código e os dados já estão corretos.




Editou arquivos


A Tarefa 5.5 passou: 134 testes canônicos, cobertura de 93,12%, 118 testes legados aprovados e 7 skips esperados. As curvas reconciliam a PD do horizonte, respeitam o prazo real e propagam explicitamente o status de entrada não aprovada. Vou validar o diff e sincronizar.




A Tarefa 5.5 foi commitada (7fd7b6c) e enviada. Inicio a Tarefa 5.6 com uma restrição importante: o backtesting de 2025 está corretamente sem targets maduros. Vou implementar validação quantitativa e PSI com o modelo congelado, publicar o status de backtesting como pendente — não fabricar métricas — e fechar a Fase 5 com model card apenas se os critérios documentais e de regressão forem satisfeitos.




Editou arquivos


A Tarefa 5.6 e a Fase 5 passaram pela regressão completa: 140 testes canônicos, cobertura de 93,48%, 118 legados aprovados e 7 skips esperados. O model card registra reprovação, PSI 6,7903 e ausência de champion aprovado; o backtesting continua controlado como pendente, sem métricas falsas. Vou sincronizar esse fechamento.




A Tarefa 5.6 foi commitada (fff51bc) e enviada; a Fase 5 está concluída tecnicamente, mas sem alegar aprovação do modelo. Antes da Fase 6, vou verificar a topologia Git e promover o marco para main somente por fast-forward, preservando todo o histórico de tarefas.




O marco da Fase 5 foi promovido por fast-forward e origin/main agora aponta para fff51bc; a nova branch codex/phase-6-staging já está publicada. Inicio a Tarefa 6.1 criando um ledger versionado de baseline na originação, com PD/rating, modelo, política, hash e lifetime PD calculada sobre o prazo original — mantendo status não aprovado quando a origem for o modelo sintético atual.




Editou arquivos


A Tarefa 6.1 passou: 148 testes canônicos, cobertura de 93,58%, 118 legados aprovados e 7 skips esperados. O ledger rejeita duplicidade e adulteração, e a lifetime PD usa a maturidade original. Vou consolidar e sincronizar antes de iniciar o motor SICR.




A Tarefa 6.1 foi commitada (a7a6021) e enviada. Inicio a Tarefa 6.2: um motor SICR único e explicável, comparando lifetime PD atual versus originação, com variações absoluta/relativa, downgrade, watchlist, eventos qualitativos, atraso, low-credit-risk exemption configurável e razões completas. Thresholds serão versionados e explicitamente demonstrativos, não apresentados como requisitos normativos.




Editou arquivos


A Tarefa 6.2 passou: 158 testes canônicos, cobertura de 93,42%, 118 legados aprovados e 7 skips esperados. A isenção de baixo risco só suprime gatilhos quantitativos e toda decisão carrega razões e hash da política. Vou sincronizar esse incremento.




A Tarefa 6.2 foi commitada (8f99c5e) e enviada. Inicio a Tarefa 6.3 integrando o default operacional já versionado à classificação contábil de Stage 3, incluindo unlikeliness-to-pay, concessão em dificuldade e arrasto por contraparte com exceções explícitas e rastreáveis.




Editou arquivos


A Tarefa 6.3 passou: 167 testes canônicos, cobertura de 93,47%, 118 legados aprovados e 7 skips esperados. Default operacional e Stage 3 agora compartilham a mesma decisão; contágio só ocorre no nível configurado e exceções desconhecidas falham fechadas. Vou sincronizar.




A Tarefa 6.3 foi commitada (bc04878) e enviada. Inicio a Tarefa 6.4 com uma máquina de transição e ledger imutável: Stage 3 só sai mediante cura quantitativa/qualitativa e período de observação; transições preservam razões, continuidade temporal e identificam redefault após cura.




Editou arquivos


A Tarefa 6.4 passou: 174 testes canônicos, cobertura de 93,32%, 118 legados aprovados e 7 skips esperados. O ledger impede saltos temporais/de estado; cura elegível retorna a Stage 1 ou 2 conforme SICR residual e redefault é marcado. Vou sincronizar.




A Tarefa 6.4 foi commitada (8fab715) e enviada. Inicio a Tarefa 6.5: fluxo POCI separado, credit-adjusted EIR calculada sobre fluxos esperados na originação e variação subsequente da lifetime ECL descontada pela mesma taxa, com golden cases manuais para perda adicional e melhora.




Editou arquivos


A Tarefa 6.5 passou: 180 testes canônicos, cobertura de 93,23%, 118 legados aprovados e 7 skips esperados. Os golden cases reconciliam EIR ajustada de 10%, perda adicional de 10 e ganho de impairment de 5. Vou sincronizar.




A Tarefa 6.5 foi commitada (e6c6c54) e enviada. Inicio a Tarefa 6.6 validando o comportamento de staging sintético: estabilidade por período, migrações, sensibilidade de thresholds, comparação entre regra relativa e regra absoluta legada, além de falsos positivos/negativos contra eventos futuros. A evidência será marcada como proxy, pois a calibração de PD continua reprovada.




Editou arquivos


A Tarefa 6.6 e a Fase 6 passaram: 186 testes canônicos, cobertura de 93,46%, 118 legados aprovados e 7 skips esperados. A validação revelou regra relativa degenerada no OOT (recall zero), registrada como reprovação; os critérios de arquitetura e rastreabilidade da fase estão cumpridos sem mascarar o blocker empírico. Vou sincronizar e promover o marco para main.




A Fase 6 foi promovida por fast-forward; origin/main está em a98ce67. A branch codex/phase-7-lgd-workout está publicada. Vou agora decompor a Fase 7 pela ordem do backlog e começar pela definição do dataset de workout LGD.







Editou 217 arquivos+11.661-740Revisar alteraçõesDesfazerRevisar

changelog.mdchangelog.md+65-1
docs/MASTER_BACKLOG.mddocs/MASTER_BACKLOG.md+553-208
docs/baseline/CURRENT_STATE_BASELINE.mddocs/baseline/CURRENT_STATE_BASELINE.md+155-0
Mostrar mais 214 arquivos





Retomando pela Tarefa 7.1. Vou confirmar branch/worktree após a interrupção e executar a Fase 7 em sequência: dataset workout, LGD realizada, modelagem, garantias e validação, mantendo cada tarefa isolada em teste, documentação, commit e push.




Editou arquivos


A Tarefa 7.1 passou: 192 testes canônicos, cobertura de 93,51%, 118 legados aprovados e 7 skips esperados. O dataset registra 32 defaults, 7 janelas censuradas e reconcilia eventos somente até o cutoff. Vou sincronizar antes da LGD realizada.




A Tarefa 7.1 foi commitada (e462f70) e enviada. Na Tarefa 7.2 vou calcular valor presente de recuperações brutas e custos separadamente pela EIR contratual; curas reconhecerão o valor residual restaurado sem dupla contagem, e LGD fora de 0–100% será preservada como valor bruto e limitada por política versionada.




Editou arquivos


Contexto compactado automaticamente



Retomando a Tarefa 7.2. Vou primeiro confirmar exatamente quais partes do patch ficaram gravadas após a interrupção; depois completo testes e documentação antes da validação integral, commit e push.




O patch parcial está íntegro: política versionada, cálculo e API pública existem. Agora vou fechar a unidade com testes manuais de desconto, cura, censura e limites; também vou eliminar a conversão intermediária para float para manter o cálculo financeiro em Decimal.




Editou arquivos


Os testes focados passaram (13 no conjunto LGD). Na carteira sintética, há 25 workouts completos e 7 censurados; a LGD média limitada dos completos é 52,28%, mas isso permanece evidência demonstrativa, não calibração institucional. Vou registrar fórmula, política, linhagem e essa limitação antes do gate completo.




Editou arquivos


O gate completo passou: 199 testes canônicos, 93,46% de cobertura, além de 118 testes legados aprovados e 7 ignorados já conhecidos. Vou fazer a revisão final do diff da Tarefa 7.2 e, sem misturar a próxima tarefa, criar e publicar o commit.




A Tarefa 7.2 foi concluída e publicada no commit 20b82c7. O repositório está limpo; avanço agora, isoladamente, para a Tarefa 7.3 (modelagem LGD), começando por inspecionar os requisitos exatos e os padrões já usados nos modelos de PD.




O perfil real tem apenas 25 workouts fechados (15 até 2021 para treino e 10 entre 2022–2023 para validação), com seis perdas exatamente em 100% e nenhuma LGD zero. Portanto, vou avaliar um candidato one-inflated, não beta puro, e manter todos os modelos como demonstrativos/não aprovados. As features serão point-in-time: produto, garantia/LTV, atraso e prazo no default, além do macro observado na data.




Editou arquivos


A comparação temporal já está estável: o Ridge one-stage teve o menor RMSE (0,4520), por margem pequena sobre two-stage (0,4533) e one-inflated (0,4555). Isso autoriza apenas levá-lo provisoriamente à validação da Tarefa 7.5; não há base para aprovação com 15 casos de treino e 10 de holdout.




Editou arquivos


Os contratos focados, tipagem estrita e formatação passaram. Vou executar agora o gate integral da Tarefa 7.3; se permanecer verde, reviso somente esse diff e publico o commit antes de iniciar garantias.




A Tarefa 7.3 foi publicada no commit 759d1e5, após 206 testes canônicos (93,58% de cobertura) e a regressão legada verde. Inicio agora a Tarefa 7.4, mantendo separada a projeção de garantias da recuperação workout já observada.




A política de garantia será explícita e separada do cash flow observado: valor atualizado desde a avaliação, enforceability, haircut, custo e prazo de execução. Na reconciliação, recuperações de collateral_execution serão excluídas da base e substituídas pela projeção, limitada ao headroom da EAD; assim, valor projetado e caixa observado nunca são somados.




Editou arquivos


A política e os golden cases passaram. Na carteira completa há 20 defaults com garantia (11 veículos, 9 imóveis) e 12 sem garantia; no cenário base, a recuperação líquida descontada projetada média é R$ 101.573,44, ou 68,11% da EAD dos casos garantidos. O caixa de garantia já observado fica apenas como benchmark excluído, nunca como parcela adicional.




Editou arquivos


Os testes focados confirmam os quatro controles de aceite, inclusive a substituição — não soma — do fluxo de garantia observado. Executarei o gate completo da Tarefa 7.4 e, se verde, publicarei essa unidade antes da validação final da fase.




A Tarefa 7.4 foi publicada no commit f6da679 com 213 testes canônicos verdes. Na validação final da fase, vou congelar critérios antes de medir: holdout mínimo, MAE/RMSE, calibração, volumes por coorte/produto e amostra downturn. Com apenas 10 casos de validação, o resultado será necessariamente uma avaliação técnica não aprovada, ainda que algum indicador pontual pareça bom.




Editou arquivos


O relatório reproduz um problema importante: o holdout de 2022–2023 já foi usado para escolher o menor RMSE na Tarefa 7.3, portanto não é uma validação independente nem OOT intocado. Vou registrar isso como blocker formal, além dos limites de amostra e erro; os defaults de 2024–2025 ainda estão censurados e não podem ser usados para fabricar uma conclusão.




Editou arquivos


A validação focada passou e formalizou oito blockers, incluindo OOT não independente. Vou executar o gate integral da Tarefa 7.5; depois reviso o diff, publico o commit e só então faço a promoção da Fase 7 para main.




O gate integral passou: 220 testes canônicos, 92,81% de cobertura, 118 legados aprovados e 7 ignorados conhecidos. Antes do commit, acrescentei à revisão um guardrail: uma política marcada demonstrative_unvalidated jamais pode retornar approved, mesmo que os limites numéricos fossem satisfeitos.




Editou arquivos


A Tarefa 7.5 foi publicada no commit 28a078a. A Fase 7 está completa tecnicamente, com o modelo explicitamente not_approved; vou agora promover por fast-forward a fase validada para main, sincronizar o GitHub e abrir a branch da Fase 8.




A Fase 7 está sincronizada em main no commit 28a078a; a branch codex/phase-8-ead-ccf também já está no remoto. Inicio a Tarefa 8.1 inspecionando os requisitos e os motores de cronograma/modificação já existentes, para reutilizar saldos contratuais em vez de criar uma segunda lógica de EAD.




A inspeção confirmou a convenção real do gerador: a EAD de default amortizado é o saldo de abertura da última competência observável antes do default — isto é, antes do pagamento agendado na data de default. Vou versionar essa regra e construir o motor sobre o cronograma canônico, aplicando resultados reais de prepagamento/modificação quando efetivos antes do default.




Editou arquivos


O motor passou os sete testes: cronograma, prepagamento parcial/total, modificação, corte temporal, maturidade e reconciliação sintética. Os 24 defaults amortizados iniciais reconciliam exatamente com a EAD registrada; uma extensão de prazo pré-default é identificada, sem reamortização inventada porque o gerador sintético não fornece novos fluxos para esse evento.




Editou arquivos


A Tarefa 8.1 está documentada e os checks focados estão verdes. O gate completo está em execução; ele agora também inclui tipagem estrita do novo pacote src/models/ead.




O gate completo passou: 227 testes canônicos, 92,67% de cobertura, 118 legados aprovados e 7 ignorados conhecidos. Vou revisar o diff exclusivo da Tarefa 8.1 e publicá-lo antes de iniciar CCF rotativo.




A Tarefa 8.1 foi publicada no commit e5115c7. Avanço para a Tarefa 8.2: vou inspecionar tanto o histórico sintético de utilização quanto o motor rotativo canônico, especialmente o comportamento de redução/cancelamento de limite, antes de definir o dataset e os modelos de CCF.




O estado real tem só um default rotativo na carteira de aceite, insuficiente para estimar qualquer CCF. Para não transformar uma constante em “modelo”, usarei uma carteira de desenvolvimento sintética maior e determinística (seed 91, 400 clientes), mantendo a carteira principal intacta. O modelo será Ridge por produto, utilização, horizonte e status de limite, com status demonstrativo; reduções/cancelamentos serão cobertos pelo contrato canônico, mas não alegados como estimados se não aparecerem nos dados.




Editou arquivos


O dataset ficou com 12 defaults e 25 linhas: 15 cartões, 10 overdrafts; 12 horizontes de 3 meses, 12 de 6 e apenas 1 de 12 meses. O CCF médio é 5,68%; todos os limites históricos ficaram inalterados. Logo, o motor trata redução/cancelamento e os testes provam isso, mas o efeito desses eventos não é estimável nesta amostra — ficará como limitação formal.




Editou arquivos


Os checks focados passaram. Vou executar o gate integral da Tarefa 8.2; a validação temporal das quatro linhas reservadas continuará na Tarefa 8.4, sem reinterpretar as métricas in-sample como aprovação.




Editou um arquivo


A Tarefa 8.2 foi publicada no commit 84417b8. Para compromissos e garantias, o gerador atual não produz utilizações/defaults observáveis — o saldo permanece zero e o detector de default exclui saldo zero. Assim, a Tarefa 8.3 será uma projeção paramétrica versionada, explicitamente not_estimated, separando compromisso de empréstimo e chamada de garantia, sem fingir calibração empírica.




Editou arquivos


Os golden cases passaram. Na carteira principal existem 10 compromissos e 10 garantias: em 12 meses e multiplicador-base, a probabilidade parametrizada média é 38,73% para compromissos e 26,20% para garantias, com EAD média de R$ 31.489,89 e R$ 46.934,74. Esses números são hipóteses condicionais de utilização, não PD nem estimativas observadas.




Editou arquivos


Os checks focados passaram e confirmam que a projeção aumenta monotonicamente com horizonte/risco, respeita reduções/cancelamentos e mantém linhagem. Vou executar o gate integral da Tarefa 8.3 antes do commit.




A Tarefa 8.3 foi publicada no commit aa01841. Resta a validação da Fase 8: vou congelar critérios, medir separadamente a reconciliação determinística de EAD amortizada e o holdout temporal do CCF, além de testar sensibilidades de utilização/limite e publicar o model card sem promover componentes parametrizados.




O holdout CCF tem só quatro linhas (dois defaults, horizontes 3/6 meses). As previsões variam, mas duas observações têm CCF zero e não há horizonte 12 meses nem limite alterado. A validação poderá registrar MAE/RMSE, porém a aprovação será bloqueada por volume, cobertura temporal/segmental, ausência de eventos de limite e componentes off-balance não estimados.




Editou arquivos


Para evitar que a validação regenere 24 taxas efetivas apenas para ler saldos já materializados, vou usar diretamente os ScheduleRecord sintéticos no dataset de reconciliação. O golden case do motor canônico continua cobrindo prepagamento/modificação; essa otimização preserva exatamente a regra e reduz o gate em cerca de 20 segundos.




Editou arquivos


A validação consolidada está reproduzível: EAD amortizada reconcilia exatamente 24 casos, mas isso é identidade metodológica do gerador, não performance preditiva. No holdout CCF, MAE é 0,03972 e RMSE 0,05489 em apenas quatro linhas. As sensibilidades respondem; a direção de utilização do Ridge é inversa e fica apenas diagnóstica, enquanto o efeito de limite off-balance é monotônico por construção.




Editou arquivos


Contexto compactado automaticamente



Retomando a Tarefa 8.4. Vou primeiro confirmar se a atualização documental foi aplicada integralmente; em seguida fecho a validação completa, commit, push e promoção da Fase 8 antes de iniciar a Fase 9.




A atualização está íntegra: relatório, model card, backlog, changelog e rastreabilidade refletem a decisão not_approved sem confundir reconciliação técnica com validação institucional. Agora vou executar os gates focados e, depois, a regressão completa da Fase 8.




A Fase 8 passou integralmente: 248 testes canônicos, 92,43% de cobertura, e regressão legada com 118 aprovados/7 ignorados. Vou revisar o diff final, registrar a Tarefa 8.4 e promover a branch para main; depois abro a Fase 9.




A Fase 8 foi promovida para main no commit e9f28ed, e a branch codex/phase-9-forward-looking já está publicada. Inicio agora a Tarefa 9.1, levantando primeiro o contrato exato do backlog e os componentes macro/ECL existentes para implementar apenas o próximo incremento.




O repositório já tem quatro trajetórias sintéticas mensais, mas ainda faltam o contrato canônico de trajetória, a governança de aprovação e o cache verificável exigidos pela Tarefa 9.1. Vou preservar essa fonte existente e envolvê-la em um serviço tipado, sem criar uma segunda verdade macroeconômica.




Editou arquivos


O núcleo da Tarefa 9.1 está implementado e os 7 testes focados passaram. O serviço agora rejeita pesos inválidos, exige metadados para qualquer estado aprovado e só aceita fontes externas depois de um snapshot content-addressed com SHA-256; a configuração atual permanece explicitamente not_approved. Vou registrar essas evidências e então rodar a regressão completa.




Editou arquivos


A Tarefa 9.1 passou na regressão completa: 255 testes canônicos, 92,04% de cobertura, e 118 testes legados aprovados/7 ignorados. Vou registrar e publicar este incremento isoladamente antes de avançar para as relações macro-risco da Tarefa 9.2.




A Tarefa 9.1 foi publicada no commit 782465f. Na Tarefa 9.2, vou usar parametrização transparente — não “estimação” artificial — porque a fonte é sintética. Os coeficientes serão versionados, segmentados e não lineares, produzindo fatores separados para PD, LGD, EAD e CCF ao longo de cada trajetória.




Editou arquivos


A Tarefa 9.2 também passou: 262 testes canônicos, 92,06% de cobertura, e regressão legada estável. Os fatores terminais mantêm ordenação econômica nos quatro componentes, mas a documentação registra que isso decorre da parametrização sintética e não constitui calibração. Vou publicar este commit isolado e seguir para o ECL por cenário.




A Tarefa 9.2 foi publicada no commit f377fb5. Para a Tarefa 9.3, o incremento será um motor mensal genérico de cenário: ajusta hazard, LGD, saldo sacado e CCF por período, calcula a perda integral de cada trajetória e só então pondera os ECLs. O detalhamento por Stage e os golden cases completos permanecem corretamente reservados à Fase 10.




Editou arquivos


O motor da Tarefa 9.3 já passa nos 7 testes focados. Um caso manual neutro de dois meses resulta em R$ 14,25 por cenário; no caso demonstrativo adverso de três meses, o ECL é calculado separadamente (R$ 20,21 / 20,97 / 22,89) e só depois ponderado para R$ 21,14, com stress de R$ 27,37 fora da média. Vou documentar essa reconciliação e validar o repositório inteiro.




Editou arquivos


A Tarefa 9.3 passou na regressão completa: 269 testes canônicos, 92,17% de cobertura, e 118/7 na suíte legada. Vou publicar o motor por cenário agora; a próxima unidade será a Tarefa 9.4, isolando sensibilidades, stress e overlays gerenciais do cálculo modelado.




A Tarefa 9.3 foi publicada no commit 8029c2c. Na Tarefa 9.4, vou manter duas separações rígidas: sensibilidades e stress serão execuções derivadas e versionadas, enquanto overlays serão registros gerenciais posteriores ao ECL econômico, com aprovação, vigência e reversão completas — sem alterar as curvas do modelo.




Editou arquivos


A Tarefa 9.4 passou nos testes focados. No caso de seis meses, o ECL base é R$ 121,51; mudanças de pesos elevam para R$ 125,61/R$ 130,65, choques de trajetória para R$ 133,51/R$ 137,22, e o stress separado chega a R$ 187,54. O framework de overlay preserva o ECL econômico e mantém valor, motivo, aprovador, vigência e reversão em registro próprio.




Editou arquivos


A Fase 9 fechou com 276 testes canônicos, 92,27% de cobertura, e regressão legada 118 aprovada/7 ignorada. Vou registrar a Tarefa 9.4, publicar e promover a fase para main; em seguida abro a branch da Fase 10 e começo pela Tarefa 10.1.




A Fase 9 está em main no commit 9935ada, e a branch da Fase 10 já está publicada. Inicio a Tarefa 10.1 com um wrapper Stage 1 por contrato: restringirá eventos de default aos próximos 12 meses, usará LGD lifetime condicional ao default e descontará cada período pela EIR original antes de delegar ao motor de cenários já reconciliado.




Editou arquivos


A implementação Stage 1 passou nos 7 testes focados. No caso de 12 meses, EIR original de 12% e saldo decrescente, os ECLs por cenário são R$ 33,60 / 36,95 / 46,45, ponderando para R$ 37,87; o stress separado é R$ 76,60. O desconto cai de 0,99060040 no primeiro mês para 0,89285714 no décimo segundo.




Editou arquivos


A Tarefa 10.1 passou na regressão completa: 283 testes canônicos, 92,30% de cobertura, e 118/7 na suíte legada. Vou publicar este incremento isoladamente e então avançar para Stage 2 lifetime, incluindo prazo remanescente, prepagamento/extensão esperados e modos individual/coletivo.




Editou arquivos


Stage 2 passou nos 7 testes focados. No caso lifetime de 18 meses, o ECL ponderado é R$ 74,00; prepagamento esperado de 3% a.m. reduz para R$ 60,39. Um prazo contratual de 12 meses produz R$ 57,14, enquanto extensão esperada de 6 meses com probabilidade de 50% eleva para R$ 65,57. Os modos individual e coletivo preservam o mesmo cálculo e diferem apenas na governança do agrupamento.




Editou arquivos


A Tarefa 10.2 passou integralmente: 290 testes canônicos, 92,37% de cobertura, e 118/7 na regressão legada. Vou publicar Stage 2 agora. A próxima tarefa será Stage 3 por cash shortfall, onde recuperações, garantias, custos, cura e write-off precisam aparecer como fluxos explícitos — sem reutilizar indevidamente a fórmula PD × LGD × EAD.




Stage 2 foi publicado no commit 70211a8. Para Stage 3, vou usar projeções de caixa específicas por cenário: fluxo contratual menos recebimentos do devedor e recuperações, mais custos, tudo descontado pela EIR original. Garantia, colateral, cura, write-off e recuperação pós-baixa ficarão em campos separados; juros serão calculados sobre o valor contábil líquido, sem transformar write-off em uma segunda perda.




Editou arquivos


Stage 3 passou nos 8 testes focados. O golden case reconcilia R$ 100 contratuais − R$ 60 recebidos − R$ 20 de colateral + R$ 5 de custos = R$ 25 de cash shortfall. Um caso multi-cenário produz R$ 20/40/60/80 e ECL ponderado de R$ 40. Write-off de R$ 100 não duplica a perda; recuperação pós-baixa de R$ 20 reduz o ECL para R$ 80. Juros de 12% sobre valor líquido de R$ 800 resultam em R$ 8 mensais.




Editou arquivos


A Tarefa 10.3 passou na regressão completa: 298 testes canônicos, 92,45% de cobertura, e 118/7 na suíte legada. Vou publicar este incremento. Em seguida avanço para 10.4, integrando o fluxo POCI existente ao cálculo lifetime por cenário e à apresentação separada de perda/ganho.




Stage 3 foi publicado no commit 8b0359c. A Tarefa 10.4 aproveitará o cálculo POCI já validado, acrescentando a camada que falta: fluxos lifetime por cenário, ponderação das mudanças desde o reconhecimento inicial, stress separado e apresentação explícita como ganho/perda de impairment POCI, sempre pela credit-adjusted EIR.




Editou arquivos


A integração POCI passou: 13 testes focados (6 existentes + 7 novos). No golden case, preço R$ 80 e fluxo inicial esperado R$ 88 contra R$ 110 contratual produzem credit-adjusted EIR de 10% e ECL inicial R$ 20. Os cenários atuais geram R$ 10/20/30/40, ponderado R$ 20; mudanças favoráveis e adversas são apresentadas separadamente como ganho ou perda de impairment.




Editou arquivos


A Tarefa 10.4 passou na regressão completa: 305 testes canônicos, 92,53% de cobertura, e 118/7 na suíte legada. Vou publicar POCI. A próxima unidade é 10.5: critérios estatísticos de grupos homogêneos, validação de homogeneidade e rota obrigatória para cálculo individual quando a exposição for relevante.




POCI foi publicado no commit 4472289. Para 10.5, vou separar elegibilidade de agrupamento do cálculo: exposições materiais serão roteadas individualmente; grupos coletivos exigirão dimensões econômicas/contratuais além de score e passarão por tamanho, dispersão de PD/LGD/EAD e concentração. Faixas arbitrárias de score, sozinhas, serão rejeitadas pelo domínio.




Editou arquivos


A Tarefa 10.5 passou nos 7 testes focados. O grupo demonstrativo de 20 hipotecas, definido por produto, colateral, safra e comportamento, passou com CV de PD 0,0040, LGD 0,0017 e EAD 0,0057; maior exposição representa 5,05%. Exposições a partir de R$ 500 mil são desviadas obrigatoriamente ao cálculo individual, e definições baseadas apenas em score falham fechadas.




Editou arquivos


A Tarefa 10.5 passou na regressão completa: 312 testes canônicos, 92,53% de cobertura, e 118/7 legados. Vou publicar o agrupamento. A seguir entra 10.6, que consolidará período, cenário, contrato, cliente, produto e carteira em um ledger imutável, preservando ECL econômico, overlay, piso e valor final separadamente.




O agrupamento foi publicado no commit 6827d80. Na Tarefa 10.6, vou materializar um ledger por execução com linhas contrato–cenário–período, ajustes contratuais separados e hash encadeável. A validação impedirá publicação se os totais ponderados não fecharem com o ECL econômico ou se final ≠ max(econômico + overlay, piso) por contrato.




Editou arquivos


A Tarefa 10.6 passou nos 8 testes focados. O exemplo fecha em todos os níveis: cenário base R$ 40 bruto/R$ 28 ponderado, pessimista R$ 70/R$ 21; contratos R$ 13 + R$ 36 = portfólio econômico R$ 49. Overlays somam R$ 1, pisos R$ 20 e o ECL final contratual agrega R$ 55. O ledger é congelado, determinístico, content-addressed e encadeável por hash.




Editou arquivos


A Tarefa 10.6 passou na regressão completa: 320 testes canônicos, 92,61% de cobertura, e 118/7 legados. Vou publicar o ledger. Depois fecho a Fase 10 com o pacote consolidado de golden cases exigido em 10.7, incluindo Stage 1, Stage 2, Stage 3, rotativo/CCF, garantia, POCI, modificação e multi-cenário.




O ledger foi publicado no commit d6aa104. Para a Tarefa 10.7, vou consolidar evidências já dispersas em um pacote único, com valores manuais congelados em CSV e oito testes independentes. O caso de modificação combinará a mecânica de modificação sem baixa com Stage 2 sobre o cronograma revisado e a EIR original preservada.




Editou arquivos


Os oito golden cases agora passam com valores exatos: Stage 1 R$ 9,05; Stage 2 R$ 12,33; Stage 3 R$ 25; rotativo/CCF R$ 7,50; garantido R$ 30; POCI R$ 20; modificação R$ 268,15; multi-cenário R$ 21,14. Vou acrescentar as duas verificações finais de aceite — identidade entre LGD exibida e usada, e reprodutibilidade — antes da regressão integral da Fase 10.




Editou arquivos


A Fase 10 fechou com 328 testes canônicos, 92,61% de cobertura, e 118 testes legados aprovados/7 ignorados. Os oito golden cases bateram exatamente, a LGD exibida foi reconciliada por período e a repetição multi-cenário foi idêntica. Vou publicar e promover a fase para main, depois iniciar a Fase 11 pela Tarefa 11.1.




A Fase 10 está em main no commit 2b84d7f, e a branch da Fase 11 está publicada. A Tarefa 11.1 exige regra regulatória vigente; vou primeiro cruzar o catálogo local com as fontes oficiais atuais do BCB/CMN, sem transcrever valores de fontes secundárias nem inventar tabelas ausentes.




Contexto compactado automaticamente



Vou validar agora o texto consolidado e os anexos oficiais aplicáveis à provisão mínima por data de referência. A implementação só seguirá depois de fechar essa evidência e o recorte exato da Tarefa 11.1.




Pesquisou na web


A evidência oficial fechou o desenho: o piso é a provisão por perda incorrida do Anexo I da Resolução BCB 352, aplicada individualmente ao valor contábil bruto de ativos inadimplidos e sem substituir a ECL econômica. A metodologia simplificada e seu Anexo II permanecem fora desta tarefa e entram somente na 11.2.




Editou arquivos e pesquisou na web


Os testes direcionados passaram, mas a checagem da tabela revelou um erro de indexação no artefato recém-criado: o Anexo I tem 22 faixas (0–20 meses e “21 ou mais”), não 23. Estou corrigindo isso antes de registrar a evidência no backlog; nenhuma versão incorreta será commitada.




Editou arquivos


A correção foi aplicada e a suíte direcionada agora valida as 22 faixas oficiais, inclusive 20 meses e “21 ou mais”. A matriz registra o piso como implementado, mas mantém o perímetro ECL amplo como parcial — sem antecipar a conclusão das tarefas 11.2–11.5. Vou rodar o gate completo antes do commit.




Editou um arquivo


O gate completo passou: 336 testes canônicos, 92,51% de cobertura, além de 118 testes legados aprovados e 7 skips conhecidos. A Tarefa 11.1 está pronta para commit e push isolados; em seguida começo a verificação de aplicabilidade da metodologia simplificada da 11.2.




Pesquisou na web


A aplicabilidade vigente ficou delimitada: S4 e S5 usam a metodologia simplificada; S4 pode migrar à completa somente com autorização prévia; e há exceções específicas para cooperativas em sistemas com S1–S3 ou com central/confederação autorizada. Vou codificar essa decisão como pré-condição explícita e impedir que o cálculo simplificado aceite uma rota “completa”.




Editou arquivos


A Tarefa 11.2 está funcional nos testes direcionados: roteamento por segmento e exceções, todas as taxas oficiais, composição de provisão e rejeição cruzada entre metodologias. Também corrigi o catálogo: a IN BCB 464 está revogada e não pode permanecer descrita como vigente; a referência operacional atual é a IN BCB 560.




A Tarefa 11.2 foi publicada no commit 04eacc7 após 347 testes canônicos, 92,51% de cobertura e a regressão legada 118/7. Inicio agora a 11.3 pelo contrato de classificação: modelo de negócio, teste SPPI, categoria de mensuração, elegibilidade ao impairment e reclassificação prospectiva.




Editou arquivos e pesquisou na web


A classificação agora produz uma decisão auditável e uma fronteira clara: categoria contábil e elegibilidade ao impairment são campos diferentes. Os testes também impedem reclassificar uma designação irrevogável a FVTPL e validam os efeitos prospectivos materiais; vou fechar o gate completo da 11.3.




A Tarefa 11.3 foi publicada no commit f4296db; o gate ficou em 360 testes canônicos, 92,53% e regressão legada 118/7. Na 11.4 vou reaproveitar os cálculos de modificação já existentes, mas acrescentar a decisão explícita de desreconhecimento e um ledger regulatório de baixa/recuperação, sem duplicar o motor de cash flow.




Editou arquivos


A 11.4 agora separa três momentos que antes estavam parcialmente misturados: decisão de modificação, cálculo contratual e registro de evento realizado. Os testes direcionados passaram para EIR original/nova, baixa parcial/total, insuficiência de allowance e recuperação pós-baixa; falta apenas o gate integral antes do commit.




A Tarefa 11.4 foi publicada em 9a0b9eb com 366 testes canônicos e regressão legada verde. A última tarefa da fase será um pacote de disclosure derivado de saldos e movimentos reconciliados; ele falhará se a ponte opening-to-closing não fechar, em vez de produzir tabelas apenas visualmente plausíveis.




Editou arquivos e pesquisou na web


O pacote da 11.5 fecha a ponte por estágio e inclui um manifesto de fronteiras verificável: capital IRB está fora do escopo e LGD downturn não é aceita como LGD contábil. Os testes direcionados passaram; agora rodo o gate completo que decide a promoção da Fase 11.




As cinco tarefas explícitas da Fase 11 estão publicadas, mas a inspeção de fechamento encontrou uma pendência real na própria matriz: CMN4966-REV-001, BCB352-STAGE-001 e BCB352-ECL-001 ainda estavam atribuídos à Fase 11 sem evidência final. Não vou promover a fase deixando esses requisitos para trás; adicionarei uma tarefa corretiva curta de fechamento regulatório ao backlog.




Editou arquivos


A tarefa corretiva reduziu os blockers regulatórios de 15 para 8; todos os requisitos ainda atribuídos à Fase 11 agora têm código e testes. Os oito restantes pertencem a governança/modelos, disclosures posteriores e Documento 3040. Vou validar e publicar esse fechamento antes de promover a branch para main.




A Fase 11 está fechada no commit a95704c: 373 testes canônicos, 92,57% de cobertura, 118 legados aprovados e 7 skips conhecidos. Vou promovê-la por fast-forward para main e abrir a branch da Fase 12, preservando o histórico linear.




A Fase 11 já está em main e a branch codex/phase-12-doc3040 está publicada. Na Tarefa 12.1 vou primeiro comparar o gerador legado com as instruções oficiais atuais do SCR, identificando campos inventados e defaults silenciosos antes de definir o novo contrato.




Contexto compactado automaticamente



A Fase 12 já está isolada na branch publicada. Agora estou fechando o inventário da Tarefa 12.1: contrato legado, defaults silenciosos e fonte oficial vigente, para que o novo contrato falhe de forma explícita onde hoje o sistema inventa dados.




Pesquisou na web


A fonte oficial vigente mudou em 2026: a IN BCB 733 introduziu alterações com vigência em maio e julho de 2026, e há outra já prevista para novembro. Isso confirma que o contrato precisa ser selecionado pela data-base; não é seguro manter um único conjunto de campos estático nem reaproveitar o XSD do documento 3045.




O desenho da Tarefa 12.1 ficará deliberadamente “incômodo” para quem tenta preencher por atalho: todo valor regulatório presente carregará sua origem, campos condicionais precisarão ser informados explicitamente como valor ou ausência, e o contrato recusará porte, CEP, COSIF, datas e códigos ausentes/incompatíveis. A resolução de domínios por data-base ficará na Tarefa 12.2, mas o formato e a referência oficial de cada domínio já entram no catálogo agora.




Editou arquivos


O contrato canônico já está executável e passou nos testes direcionados: 11 testes cobrem linhagem obrigatória, ausência de defaults escalares, condições PF/PJ, grupos condicionais, datas, totalizadores e atraso. Antes do commit, estou sincronizando a evidência regulatória e deixando explícito que os domínios ainda não são aceitos por simples string — eles só serão liberados quando o registry versionado da Tarefa 12.2 estiver conectado.




Editou arquivos


A evidência documental e a matriz de rastreabilidade agora refletem corretamente um estado parcial do requisito de leiaute: o contrato está implementado, mas o XML ainda não. Os testes regulatórios de contrato e governança passaram (22/22); vou rodar o gate canônico completo antes de criar o commit da Tarefa 12.1.




O gate completo fechou verde: formatação, lint, MyPy, 384 testes canônicos com 91,45% de cobertura e 118 testes legados (7 skips esperados). A Tarefa 12.1 está pronta para o commit e push isolados exigidos pelo backlog.




A Tarefa 12.1 foi publicada no commit 39c91fb. Inicio agora a Tarefa 12.2: vou materializar um manifesto pequeno e verificável para as versões de maio e julho de 2026, registrar hashes dos artefatos oficiais e bloquear tanto datas anteriores ao perímetro suportado quanto novembro de 2026 até que a mudança futura seja incorporada e testada.




Pesquisou na web


A inspeção dos artefatos oficiais revelou um detalhe importante para o registry: a planilha de críticas foi atualizada em 10/07/2026, enquanto o leiaute atual também contém marcações de mudanças futuras. Portanto, o primeiro pacote suportado será estritamente 2026-07 a 2026-10, identificado pelos hashes observados em 14/07; outras datas falharão. Isso evita fingir que o snapshot atual reproduz fielmente maio ou que novembro já foi incorporado.




Editou arquivos


O registry está fechado no período que os hashes realmente sustentam e a matriz agora separa três estados: leiaute parcial, críticas versionadas mas ainda não executadas, e controle de proveniência XSD implementado. Os 28 testes direcionados/governança passaram; vou repetir o gate completo antes do segundo commit da fase.




A Tarefa 12.2 foi publicada no commit 4be5cae; o gate ficou em 390 testes canônicos, 90,96% de cobertura e regressão legada verde. A Tarefa 12.3 agora vai renderizar um XML candidato — ainda não “válido” — e comparar o IPOC fornecido com a composição oficial, sem criar identificadores, vencimentos ou valores contábeis ausentes.




Editou arquivos e pesquisou na web


O gerador candidato já cobre cabeçalho, clientes, operações, vencimentos, garantias, informações adicionais, Sicor, CMN 4.966, agregações e IPOCs conectados. Ele rejeita COSIF no leiaute 2026, recalcula a composição oficial do IPOC e preserva VlrPerda exatamente como entrada — não há mais “metade da ECL”. Os 23 testes Doc3040 passaram; falta apenas registrar a entrega e rodar o gate.




Editou arquivos


A Tarefa 12.3 foi publicada no commit da5b9ac; o gate agora cobre 396 testes canônicos com 91,49% de cobertura. Na Tarefa 12.4, a ausência do XSD 3040 será um bloqueio no relatório — não um passe. Para os domínios, vou usar uma allowlist versionada do perímetro sintético e rejeitar qualquer código fora dela até que a tabela oficial completa seja normalizada.




Para que o fluxo padrão realmente use XSD sem mentir sobre a origem, adotarei duas camadas: um XSD estrutural derivado no próprio projeto e vinculado ao hash do leiaute oficial, mais o bloqueio já existente para qualquer alegação de XSD oficial. O relatório poderá aprovar a pré-validação local derivada, mas continuará declarando que isso não equivale ao validador/homologação do BCB.




Editou arquivos


A pré-validação local agora passa somente quando quatro camadas fecham: XSD estrutural derivado, allowlist de domínios ligada ao hash oficial, regras semânticas locais e reconciliação com controle de carteira/ECL. O relatório inclui regra, severidade, linha, campo e XPath. Ele também emite dois avisos incontornáveis: XSD oficial 3040 indisponível e planilha oficial de críticas ainda não executada integralmente. Os 30 testes Doc3040 passaram.




Editou arquivos


A Tarefa 12.4 foi publicada no commit 789b926; o gate passou com 403 testes canônicos, 91,04% de cobertura e regressão legada verde. A última tarefa da fase criará fixtures imutáveis para um caso localmente pré-validado e falhas distintas de XSD, domínio e semântica, além de fixar a regressão da versão 2026.07.




Editou arquivos


Os golden files estão estáveis e cobrem quatro resultados: um XML localmente pré-validado e rejeições isoladas por XSD, domínio e total semântico. O manifesto fixa hashes e a versão; julho-outubro permanece suportado, junho e novembro são rejeitados. A suíte Doc3040 chegou a 37 testes direcionados.




Editou arquivos


O backlog e os critérios de aceite da Fase 12 agora distinguem claramente pré-validação local de validação oficial. Os 48 testes direcionados e de governança passaram. Vou executar o gate completo, commitar a Tarefa 12.5 e então promover a branch da fase para main.




O gate da Fase 12 fechou em 410 testes canônicos, 91,04% de cobertura e 118 testes legados. Antes da promoção, identifiquei um risco de portabilidade Windows: os hashes golden e do XSD dependem de LF. Vou fixar o eol=lf desses artefatos para que um checkout novo não altere os bytes e invalide a regressão.




Editou um arquivo


A Fase 12 não tem checkboxes pendentes e reduziu o relatório regulatório para 6 blockers; o restante inclui a execução oficial integral das críticas, mantida como limitação explícita. A branch está limpa e publicada. Vou fazer o fast-forward de main, enviar e abrir codex/phase-13-validation para a próxima tarefa.




A Fase 12 está em main no commit 878091c, e a branch codex/phase-13-validation já está publicada. Vou começar a Tarefa 13.1 pela arquitetura de independência: separar evidência de desenvolvimento da decisão de validação, impedir autoaprovação e produzir um relatório reproduzível com decisão aprovada, ressalvada ou rejeitada.




Editou arquivos


Contexto compactado automaticamente



Estou retomando a Tarefa 13.1 exatamente no ponto de verificação: primeiro vou confirmar se o patch de testes e a ordenação determinística foram aplicados integralmente, depois fecho documentação, gates, backlog, changelog, commit e push antes de avançar.




Editou um arquivo


O núcleo passou nos gates locais: 11 testes, Ruff e Mypy sem falhas. A regra ficou realmente independente da ordem de entrada e a decisão não pode ser inserida pelo pipeline de desenvolvimento; agora vou registrar o contrato de validação e alinhar os artefatos de controle da Tarefa 13.1.




Editou arquivos


A Tarefa 13.1 está coerente entre código, política, testes e documentação; os 15 testes direcionados passaram. Vou executar agora o gate completo do repositório — ele é o critério decisivo antes de registrar o commit e publicar a tarefa.




O gate revelou um problema de integração relevante: os testes novos passavam isoladamente, mas scripts/quality.ps1 ainda não incluía tests/validation nem o novo pacote no Mypy. Vou corrigir o próprio gate; sem isso, a validação poderia degradar sem bloquear CI/local quality.




Editou arquivos


O gate completo agora cobre a nova área e passou: 425 testes canônicos, 90,96% de cobertura, mais 118 regressões legadas aprovadas e 7 skips já conhecidos. A Tarefa 13.1 atingiu o aceite; vou consolidá-la em um commit isolado e publicar a branch antes de iniciar o backtesting de PD.




A Tarefa 13.1 foi publicada no commit fb31b76. Na 13.2, vou reaproveitar apenas os dados point-in-time e as métricas já existentes, mas calcular o backtest dentro do pacote independente: previsto versus observado por rating, produto, safra e horizonte, com drift, intervalos e decisão objetiva — sem converter a falha OOT já conhecida em aprovação.




O desenho da 13.2 ficará com uma fronteira de evidência explícita: o modelo apenas fornece probabilidades congeladas; o pacote de validação recebe essas probabilidades e os desfechos maduros, recalcula O/E, intervalos e testes sem treinar ou recalibrar nada. O ano de 2025 continuará marcado como não maturado; a evidência executável será o OOT retrospectivo de 2024, inclusive nos horizontes de 1 e 12 meses.




Editou arquivos


O backtest real foi executado e preservou a conclusão adversa: 233 observações maduras em 2024, 27 defaults em 12 meses, erro absoluto de calibração de 17,82 p.p. e drift de 17,82 p.p.; a política objetiva rejeitou o modelo. O horizonte de 1 mês passou apenas como diagnóstico derivado, e as 182 observações de 2025 continuam sem target maduro — não foram preenchidas nem pontuadas artificialmente.




Editou arquivos


A evidência foi regenerada duas vezes com o mesmo hash de arquivo, e os 27 testes acumulados da área de validação passaram. Também incluí o novo backtest e seu gerador no gate padrão; agora vou rodar a regressão completa antes do commit isolado da 13.2.




O gate completo da 13.2 passou: 437 testes canônicos, 90,94% de cobertura, 118 regressões legadas aprovadas e 7 skips conhecidos. A documentação antiga foi corrigida para distinguir o backtest retrospectivo de 2024 do bloco operacional de 2025 ainda imaturo; vou publicar este incremento isoladamente.




A Tarefa 13.2 foi publicada no commit e104d4c. Vou iniciar a 13.3 preservando a mesma fronteira: previsões LGD congeladas entram como evidência, e o pacote independente reconcilia recuperações previstas/realizadas, coortes abertas/fechadas, cura, write-off e garantia sem reajustar o candidato.




Editou arquivos


A execução independente de LGD confirmou um risco que a média simples escondia: LGD média prevista e realizada são próximas (57,11% vs. 56,89%), mas MAE 35,82%, RMSE 45,20% e recuperação prevista de 164.760 contra 236.224 realizada. A decisão é rejected; sete workouts abertos foram inventariados por coorte, cura, write-off e garantia, sem receber LGD final.




Editou arquivos


A 13.3 está fechada em conteúdo e os 14 testes direcionados passaram; o pacote foi regenerado com hash idêntico. Vou executar o gate completo, e só então registrar commit e push desta tarefa.




O gate da Tarefa 13.3 passou integralmente: 451 testes canônicos, 90,94% de cobertura, 118 regressões legadas aprovadas e 7 skips conhecidos. Vou publicar o commit de LGD e avançar, sem agregar mudanças da próxima tarefa.




A Tarefa 13.3 foi publicada no commit a616fc3. Na 13.4 vou separar duas populações: saldo/EAD de contratos amortizados e drawdown/CCF de rotativos, com cortes objetivos por produto e faixa de utilização; compromissos sem histórico realizado continuarão como limitação, não como observação inventada.




Editou arquivos


O backtest de EAD também preservou as fronteiras corretas: 24 casos amortizados reconciliam exatamente, mas o rotativo tem só 4 observações. Embora o CCF tenha MAE de 3,97 p.p., o EAD previsto médio é 6.280,72 contra 4.494,12 realizado, com MAE relativo de 40,36%; volume e erro de EAD levam a rejected. Off-balance segue excluído por não haver realizado histórico.




Editou arquivos


A 13.4 passou nos 14 testes direcionados e o evidence pack foi regenerado de forma idêntica. Vou rodar o gate completo; depois farei commit/push antes de iniciar a análise de ECL.




O gate completo da 13.4 passou: 465 testes canônicos, 91,00% de cobertura, 118 regressões legadas aprovadas e 7 skips conhecidos. Vou publicar o commit isolado de EAD/CCF e então avançar para o backtesting de ECL.




A Tarefa 13.4 foi publicada no commit 789c576. Para a 13.5, vou primeiro localizar a evidência mensal realmente disponível: ECL inicial, perdas/defaults posteriores e os ledgers de estágio, cenário e overlay. Se a carteira atual não preservar um snapshot histórico completo, o backtest deverá registrar essa lacuna e limitar a atribuição ao que é reprodutível, sem fabricar uma série.




A inspeção confirmou uma lacuna estrutural: o repositório preserva oito ECLs golden pontuais, ledgers de reconciliação e movimentos ilustrativos, mas não uma série que ligue ECL inicial a perdas posteriores por contrato. Vou implementar o backtest e a waterfall completa, porém o evidence pack real da tarefa deverá retornar rejected por zero outcomes maduros e zero snapshots comparáveis; os golden cases não serão rebatizados como perdas realizadas.




Editou arquivos


Editou 163 arquivos+18.931-510Revisar alteraçõesDesfazerRevisar

src/models/lgd/__init__.pysrc/models/lgd/__init__.py+89-7
src/models/lgd/workout.pysrc/models/lgd/workout.py+155-0
tests/models/test_lgd_workout.pytests/models/test_lgd_workout.py+91-0
Mostrar mais 160 arquivos






Você atingiu seu limite de uso. Entre em contato com o proprietário do workspace para obter mais acesso.