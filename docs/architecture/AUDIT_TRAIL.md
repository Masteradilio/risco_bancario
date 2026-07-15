# Trilha de auditoria imutável

## Contrato

A migration `0004_audit_events.sql` cria uma trilha separada dos dados operacionais e dos resultados. Cada evento registra ator e papel, ação, recurso, execução relacionada, estado, timestamp UTC, versões e hashes SHA-256 da entrada e do resultado.

Payloads de negócio e credenciais não são copiados para a trilha. O evento guarda hashes determinísticos e apenas metadados mínimos, reduzindo exposição sem perder a capacidade de reconciliar a evidência com sua fonte autorizada.

## Imutabilidade e encadeamento

Eventos são append-only: triggers impedem `UPDATE` e `DELETE`. O `event_hash` cobre o documento canônico do evento e o hash anterior; `AuditService.verify_chain()` verifica ordem, vínculo e integridade. Uma alteração privilegiada que contorne o trigger quebra a cadeia e é detectada.

O encadeamento atual é serializado pela ordem do banco local. Implantação com múltiplos writers deve usar lock transacional/advisory ou serviço central de auditoria; essa limitação não invalida a imutabilidade testada no modo demonstrativo de processo único.

## Eventos integrados

- login aceito, negado e limitado; logout;
- criação, consumo aceito e consumo rejeitado de confirmação crítica;
- cálculo individual aceito ou rejeitado;
- submissão e conclusão/falha de carteira;
- leitura de evidência e leitura da própria auditoria;
- overrides de estágio e overlays de gestão com justificativa obrigatória;
- exportações e validações regulatórias por contrato de serviço.

A rota `GET /api/v1/audit/events` exige `audit:read`, disponível somente a AUDITOR e ADMIN. A própria leitura gera evento auditável.

## Limites e operação

A trilha não substitui log técnico, métricas ou tracing. Retenção, exportação para storage WORM/SIEM, assinatura externa, sincronização de relógio e políticas institucionais de acesso precisam ser definidas no ambiente de implantação. Erros devolvidos pela API usam códigos estáveis e não armazenam secrets ou stack traces na auditoria de negócio.
