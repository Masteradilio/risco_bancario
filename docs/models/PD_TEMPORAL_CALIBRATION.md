# Separação temporal e calibração de PD

## Protocolo congelado

O dataset `0.2.0` usa cortes por data e preserva a safra de originação como
metadado. Treino termina em 2018; validação usa 2020; calibração usa 2022; OOT
usa 2024. Os anos 2019, 2021 e 2023 são embargos de doze meses e não entram nos
datasets de modelagem. O backtesting futuro usa 2025 e permanece sem target até
que a janela de doze meses amadureça.

O baseline logístico é ajustado apenas em treino. Platt (`sigmoid`) e isotonic
são comparados dentro da validação: o primeiro semestre ajusta calibradores
temporários e o segundo semestre os avalia. O método vencedor é então ajustado
do zero somente em `calibration`. Beta calibration não foi adicionada porque os
dois métodos predefinidos já permitem a decisão nesta amostra pequena.

## Seleção em validação

| Método | n | Eventos | PD média | Taxa | Erro global | Brier | Log loss | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Isotonic | 86 | 18 | 0,1831 | 0,2093 | 0,0262 | 0,1464 | 1,5742 | 0,7022 |
| Platt/sigmoid | 86 | 18 | 0,1754 | 0,2093 | 0,0339 | 0,1622 | 0,4770 | 0,6838 |

O critério congelado prioriza Brier e, em empate, erro de calibração global;
portanto isotonic foi selecionado sem consultar OOT.

## Auditoria OOT e decisão

Na primeira avaliação OOT deste baseline calibrado, as 233 linhas contêm 27
eventos. A taxa observada é 0,1159, contra PD média 0,2941; Brier 0,1342, log
loss 0,4498, ROC AUC 0,5000 e AP 0,1159. A transformação isotonic colapsou para
uma previsão constante sob mudança temporal. Esse resultado é um blocker, não
foi usado para trocar o método depois do teste e mantém status
`synthetic_validation_not_approved`.

Há 14 cortes OOT por rating, produto e ano de safra. O maior erro absoluto
ocorre em `mortgage`: 31 linhas, 20 eventos, taxa 0,6452 e PD média 0,2941.
Produtos sem evento e ratings B1/B2 também recebem aproximadamente 0,2941,
confirmando instabilidade de segmentação. Cortes pequenos são diagnósticos, não
estimativas aptas a uso institucional.

Cinco testes cobrem embargo e nulidade futura, seleção sem OOT, avaliação final
única, cortes de calibração e preservação da safra fora da matriz de features.
