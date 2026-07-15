# Operação e verificação de segurança

## Estado da evidência

Os controles desta tarefa são verificações técnicas automatizadas sobre a plataforma
demonstrativa e dados sintéticos. Eles não substituem pentest independente, revisão
de arquitetura institucional, MFA/IdP, WAF, TLS, cofre de segredos, DLP ou gestão
formal de acessos.

## SAST, dependências e segredos

O gate estático executa Black, Ruff, MyPy e uma passagem SAST dedicada com as regras
Security (`S`) do Ruff sobre todo o diretório `src`. Supressões são locais e trazem
justificativa verificável; SQL dinâmico do repositório é limitado a uma allowlist de
tabelas e identidades internas antes da composição.

No GitHub, `pip-audit` verifica a resolução congelada de Python, `npm audit` verifica
dependências de produção do frontend e Gitleaks verifica a faixa de commits do evento
com o histórico disponível. Todos esses checks falham a CI quando encontram violação
no nível configurado.

Execução local:

```powershell
.\scripts\quality.ps1 --stage static
.\venv\Scripts\python.exe -m pip_audit --local --skip-editable
npm audit --prefix frontend --omit=dev --audit-level=high
```

## Revisão de autenticação e autorização

A API canônica permanece fail-closed: JWT exige segredo externo de pelo menos 32
bytes, algoritmo HS256 fixo, issuer, audience, expiração, sessão persistida e
revogação. Senhas usam política explícita e bcrypt. Não há usuário ou senha padrão.

A matriz RBAC não usa curingas e mantém cálculo, aprovação/exportação, auditoria e
administração separados. Operações críticas são vinculadas a usuário, ação e hash do
payload por confirmação de uso único. Os testes ofensivos cobrem bypass sem token,
JWT `alg=none`, SQL injection no login, acesso de papel indevido, brute force e
métodos HTTP não expostos.

Respostas da API recebem `Cache-Control: no-store`, `X-Content-Type-Options:
nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e uma
`Permissions-Policy` restritiva. HSTS é emitido somente em conexão HTTPS; terminação
TLS continua responsabilidade do ambiente.

## Uploads e exportações

Não existe endpoint de upload ativo na API canônica. Todo endpoint futuro deve usar
`src/security/files.py` antes de persistir ou interpretar conteúdo. O validador:

- limita tamanho antes do parsing;
- exige nome simples, extensão e MIME em allowlist;
- rejeita caminhos, bytes nulos, codificação não UTF-8 e estrutura inválida;
- aceita somente CSV, JSON e XML; XML com DTD ou entidades é bloqueado.

Arquivos exportados são gravados por `SecureExportStore` sob identificador aleatório,
dentro de raiz resolvida no servidor, com criação exclusiva e permissões privadas
`0700/0600`. O nome fornecido nunca controla o diretório. Download por API ainda não
é exposto; quando for criado, deverá exigir `regulatory:export`, confirmação crítica
e evento de auditoria.

## Retenção e exclusão

`config/security/retention.json` versiona a política demonstrativa. A limpeza alcança
somente sessões e confirmações já expiradas, jobs finalizados e exportações geradas.
Usuários, execuções/resultados de cálculo, linhagem e a trilha de auditoria ficam fora
da exclusão automática. Requisitos legais, hold, WORM, anonimização e prazos reais
devem ser aprovados pela instituição antes de dados reais.

Com banco já migrado e variáveis de ambiente explícitas:

```powershell
.\venv\Scripts\python.exe scripts\security_maintenance.py
```

O comando valida o schema, aplica os prazos, registra `RETENTION_PURGE` na trilha
imutável e imprime somente contagens, sem conteúdo ou identificadores pessoais.

## Pentest automatizado básico

`tests/security/test_file_retention_and_pentest.py` executa na CI uma regressão
adversarial de caixa-preta e testes dos controles de arquivo/retenção. Essa suíte é
um smoke test técnico repetível, não um relatório de pentest independente. Antes de
exposição institucional continuam obrigatórios teste externo autenticado, avaliação
de infraestrutura, autorização row-level e remediação/reteste formal.
