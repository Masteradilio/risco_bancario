# Esquema Usuarios - Sistema de Gestão de Acesso RBAC

Este diretório contém os scripts DDL para o esquema de gerenciamento de usuários e controle de acesso baseado em funções (RBAC).

## Integração com Windows AD

O sistema utiliza autenticação integrada com Windows Active Directory (NTLM/SSO), delegando a política de senhas ao AD corporativo (60 dias para troca).

## Tabelas

| Tabela | Descrição |
|--------|-----------|
| `usuarios` | Dados do usuário (sincronizados com AD) |
| `usuarios_sessoes` | Sessões ativas (timeout 30min) |
| `auditoria_atividades` | Log de ações de usuários |
| `sistema_erros` | Log de erros (visível apenas Admin) |
| `permissoes_perfil` | Mapeamento de permissões por perfil |

## Perfis de Acesso

| Perfil | Descrição | Permissões Principais |
|--------|-----------|----------------------|
| **ANALISTA** | Operações diárias | Classificação, Cálculo ECL |
| **GESTOR** | Supervisão | Analista + Exportações BACEN + Analytics |
| **AUDITOR** | Conformidade | Leitura completa + Logs + Relatórios |
| **ADMIN** | TI | Acesso total + CRUD usuários + Erros sistema |

## Auditores Externos

Auditores do BACEN são cadastrados como `AUDITOR` com:
- `is_externo = TRUE`
- `data_expiracao = CURRENT_DATE + 30 dias`

## Deploy

```sql
SOURCE create_tables.sql;
```
