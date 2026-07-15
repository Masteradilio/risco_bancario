# Threat model da API canônica

## Escopo e estado de evidência

Este documento cobre a API local em `src/interfaces/api`, sua persistência e o motor canônico de ECL. A implementação é demonstrativa, usa dados sintéticos e não foi submetida a pentest, homologação institucional ou certificação do BCB. O backend legado e seus mocks não integram a fronteira confiável.

## Ativos e fronteiras

Ativos: credenciais, tokens, contratos sintéticos, curvas PD/LGD/EAD, cenários, configurações, resultados ECL, hashes de linhagem e evidências. As fronteiras são cliente HTTP → API autenticada → banco explicitamente selecionado → motor canônico/configurações locais versionadas.

TLS, WAF, gestão corporativa de identidades, cofre de segredos e criptografia de disco pertencem ao ambiente de implantação e não são simulados pelo código. PostgreSQL não possui fallback para SQLite. NTLM/SSO não está implementado nem é alegado.

## STRIDE e controles implementados

| Categoria | Ameaça principal | Controle verificável | Risco residual |
|---|---|---|---|
| Spoofing | roubo/falsificação de identidade | bcrypt, JWT HS256 com segredo externo ≥32 bytes, issuer/audience, `exp`/`iat`/`sub`, `jti` e sessão persistida revogável | HS256 exige rotação e distribuição segura; MFA/IdP não implementados |
| Tampering | alterar input, cenário, resultado ou operação confirmada | schemas `extra=forbid`, hashes SHA-256, migrations checksummed, resultados imutáveis por identidade e confirmação ligada a usuário/ação/hash do payload | banco/host comprometido permanece fora do modelo local |
| Repudiation | negar execução ou operação crítica | sessão identificada, confirmação de uso único e trilha append-only encadeada por hash para autenticação, cálculo, lote, evidência, overrides, overlays, exportação e validação | retenção WORM/SIEM e assinatura externa dependem do deployment |
| Information disclosure | auditor ou analista acessar função indevida | permissões explícitas sem curinga; resposta de erro de lote usa código não sensível | TLS e mascaramento institucional dependem do deployment |
| Denial of service | brute force ou lote repetido | rate limit por usuário/permissão e por login; lote limitado a 10.000 itens e processado como job | limiter é em processo e não coordena múltiplos workers |
| Elevation of privilege | papel acumular cálculo, aprovação, exportação e auditoria | matriz separa ANALYST, MANAGER, AUDITOR e ADMIN; ADMIN não ganha permissões quantitativas implicitamente | ciclo formal de concessão/revisão de acesso depende da instituição |

## Matriz de segregação

| Capacidade | ANALYST | MANAGER | AUDITOR | ADMIN |
|---|:---:|:---:|:---:|:---:|
| cálculo individual | sim | sim | não | não |
| cálculo de carteira | não | sim | não | não |
| aprovação de cenário | não | sim | não | não |
| exportação regulatória | não | sim | não | não |
| leitura de resultados | sim | sim | sim | não |
| leitura de auditoria | não | não | sim | sim |
| gestão de usuários | não | não | não | sim |

As permissões de aprovação e exportação já estão separadas no contrato RBAC; endpoints correspondentes devem exigir confirmação crítica quando forem expostos. O cálculo de carteira já exige confirmação de cinco minutos, vinculada ao SHA-256 canônico do pedido e consumida uma única vez.

## Operação segura

- Não existem usuários ou senhas default. O primeiro usuário local é criado interativamente por `scripts/bootstrap_api_user.py`.
- `JWT_SECRET` não possui valor padrão e nunca deve entrar no Git. `.env.example` mantém o campo vazio.
- Logout revoga a sessão persistida; desativação/troca de `token_version` invalida tokens emitidos.
- Respostas 401/403 não revelam se usuário, sessão ou permissão específica existem.
- A API é iniciada com factory para que configuração incompleta falhe antes de aceitar tráfego.

## Critérios antes de exposição institucional

Adotar IdP corporativo com MFA, chaves assimétricas/rotação, cofre de segredos, TLS mútuo quando aplicável, rate limiter distribuído, fila durável, backup/restore testado, revisão periódica de acessos, SAST/DAST/SCA, pentest independente e observabilidade protegida. Esses itens não são apresentados como implementados nesta fase.
