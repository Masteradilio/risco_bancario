# Demo publicável

A captura em `screenshots/ecl-evidence-workspace.png` foi produzida no frontend
React local contra a API canônica e um banco SQLite efêmero, usando somente o
fixture sintético de `docs/api/examples/ecl_individual.json`.

Nenhuma credencial, dado real ou identificador de cliente institucional está na
imagem. A faixa de advertência, o status dos modelos, os hashes e as limitações
fazem parte da demonstração: não devem ser removidos para fins promocionais.

Para reproduzir, crie um usuário local, envie o fixture pela API, autentique-se
no frontend e consulte o `execution_id` retornado. Veja `docs/api/EXAMPLES.md`.
