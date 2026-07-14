# Stage 3 e default unificado

`src/models/sicr/stage3.py` usa a definição operacional versionada de default
como a única porta de entrada para crédito deteriorado/Stage 3. A saída mantém
os mesmos motivos para `operational_default`, `accounting_credit_impaired` e
`is_stage3`, evitando classificações paralelas.

## Gatilhos próprios

- atraso material a partir de 91 DPD;
- indicadores de unlikeliness to pay da política de default;
- concessão/forbearance combinada com dificuldade financeira, mapeada para
  `distressed_restructuring`.

Concessão isolada não produz Stage 3 automaticamente; ela permanece insumo SICR
até existir dificuldade ou outro indicador de default.

## Arrasto por contraparte

A política `2026.07.1` habilita arrasto somente para produtos avaliados no nível
de contraparte. Produtos configurados no nível de facility não recebem contágio
automático. Evidência de outro contrato defaultado propaga Stage 3, salvo uma
exceção documentada e permitida:

- `independent_facility_risk`;
- `legal_ring_fence`;
- `documented_no_risk_link`.

Exceções desconhecidas, contratos repetidos ou autorreferência falham fechados.
A lista e seu status são hipóteses operacionais pendentes de validação, não uma
presunção normativa universal.

A decisão registra contratos que causaram contágio, exceções aplicadas, motivos,
nível de avaliação, versão, hash e status da política. Nove testes cobrem
backstop, UTP, reestruturação, arrasto, exceções e rastreabilidade.
