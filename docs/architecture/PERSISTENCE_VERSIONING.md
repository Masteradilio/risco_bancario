# Persistência versionada

## Escopo

A Tarefa 14.1 introduz a camada canônica de persistência para entradas e resultados do cálculo de ECL. Ela não substitui ainda as APIs legadas, não cria usuários e não contém dados reais. O banco local é apenas uma infraestrutura demonstrativa para dados sintéticos.

## Seleção do banco

O backend é explícito por `DATABASE_BACKEND`:

- `sqlite` (padrão de desenvolvimento): usa `DATABASE_SQLITE_PATH`, cujo padrão é `var/dbrisco.sqlite3`;
- `postgresql`: exige `DATABASE_URL` completa.

Uma falha do PostgreSQL interrompe a operação. Não existe fallback silencioso para SQLite, pois isso poderia gravar resultados em um destino diferente do aprovado. Arquivos locais `*.db`, `*.sqlite` e `*.sqlite3` não são versionados.

## Migrations e separação

As migrations ficam em `src/infrastructure/database/migrations/<backend>` e seguem o formato `NNNN_nome.sql`. A tabela `schema_migrations` registra versão, SHA-256 e data de aplicação. Uma migration já aplicada cujo conteúdo mudou é rejeitada.

Os nomes deixam explícitas as fronteiras lógicas:

- `operational_*`: contratos, snapshots e observações macroeconômicas;
- `model_registry_*`: modelos e cenários versionados;
- `calculation_*`: execuções revisionadas e resultados por contrato, período e cenário;
- `audit_*`: eventos imutáveis de linhagem.

Essa separação é lógica nesta fase e pode ser promovida a schemas, bancos ou permissões físicas sem alterar os contratos do repositório.

## Exatidão e linhagem

Payloads são serializados em JSON canônico, com chaves ordenadas, e recebem SHA-256. Valores `Decimal` são serializados como texto, sem conversão para ponto flutuante. PostgreSQL usa `NUMERIC` nas colunas monetárias; SQLite armazena a representação decimal exata em `TEXT`.

Cada execução registra data-base e um documento de linhagem que deve identificar, conforme o caso, snapshot, modelos, cenários, política/configuração e commit de código. O hash do documento é parte da identidade técnica da execução.

## Idempotência e reprocessamento

- Repetir uma entrada imutável com identidade e conteúdo iguais reutiliza o registro.
- Reutilizar a mesma identidade com conteúdo diferente é conflito explícito.
- Repetir uma chave de execução com a mesma linhagem reutiliza a execução existente.
- Alterar a linhagem exige `reprocess=True`; isso cria uma nova revisão ligada à anterior.
- Um resultado de ECL repetido com a mesma identidade e conteúdo é idempotente; conteúdo divergente é rejeitado.

Eventos de linhagem não aceitam atualização nem exclusão no banco. A trilha de auditoria funcional completa, com ator, autorização, overlays e exportações, pertence à Tarefa 14.4.

## Limitações atuais

- A migration PostgreSQL é validada estaticamente nesta tarefa; a execução integrada exige uma instância PostgreSQL controlada.
- Não há criptografia em repouso nem política física de backup/restore nesta entrega.
- O repositório recebe mapeamentos validados; a adaptação direta dos modelos de domínio será feita na integração da API/pipeline.
