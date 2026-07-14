# Glossário oficial do projeto

## Uso e autoridade

Este glossário padroniza a linguagem interna do `risco_bancario`. As definições são operacionais e devem ser refinadas pela matriz de rastreabilidade regulatória. Em caso de conflito, prevalecem a norma oficial vigente, a política institucional aprovada e a documentação versionada do modelo.

## Termos

| Termo | Definição no projeto |
|---|---|
| Allowance / provisão para perdas | Saldo reconhecido para perdas de crédito esperadas no perímetro aplicável. Deve ser apresentado separadamente de overlay, piso e capital regulatório. |
| Ativo problemático / credit-impaired | Ativo que atende à definição versionada de problema de recuperação de crédito. No motor, direciona o tratamento de Stage 3 quando aplicável. |
| Backstop | Critério obrigatório que limita ou sobrepõe uma decisão de modelo, como atraso relevante para staging, sempre parametrizado e rastreável. |
| Backtesting | Comparação posterior entre estimativas e resultados realizados em período não usado no desenvolvimento. |
| Cash shortfall | Diferença entre os fluxos contratuais devidos e os fluxos que se espera receber, descontada conforme a política aplicável. |
| CCF | Credit Conversion Factor; fator que relaciona parcela não utilizada ou compromisso à exposição esperada no default. Não deve ser uma constante global sem evidência. |
| Cenário | Trajetória macroeconômica versionada, com peso, vigência, aprovação e variáveis por período. |
| Config hash | Identificador determinístico da configuração exata usada em uma execução. |
| Contraparte | Pessoa ou entidade em relação à qual a instituição possui exposição; pode agregar múltiplos contratos e integrar grupo econômico. |
| Cura | Retorno de condição de maior risco ou default após critérios e período de observação documentados; não é simples ausência momentânea de atraso. |
| Data card | Documento de origem, população, período, schema, qualidade, limitações e usos permitidos de um dataset. |
| Data de observação | Data na qual as features são consideradas disponíveis para uma previsão; nenhuma informação futura pode ser usada. |
| Default | Evento de inadimplência definido por política versionada, população e produto, com backstops e eventos qualitativos documentados. |
| Desreconhecimento | Remoção contábil de ativo ou passivo quando os critérios aplicáveis são atendidos; é distinto de write-off. |
| Documento 3040 | Documento do SCR tratado pelo produto apenas em fluxo sintético de geração e pré-validação por versão de leiaute. |
| Downturn LGD | Estimativa de LGD sob condições adversas para finalidade específica. Não é usada automaticamente como LGD contábil PIT. |
| EAD | Exposure at Default; exposição esperada no momento de um possível default, projetada por produto e período. |
| ECL | Expected Credit Loss; valor presente ponderado por probabilidades dos déficits de caixa esperados, calculado por período e cenário no motor-alvo. |
| ECL de 12 meses | Parcela das perdas lifetime associada a eventos de default possíveis nos 12 meses seguintes à data de reporte; não é perda de caixa limitada aos próximos 12 meses. |
| ECL lifetime | Perda esperada associada a todos os eventos de default possíveis durante a vida remanescente relevante do instrumento. |
| EIR | Effective Interest Rate; taxa efetiva de juros determinada no reconhecimento inicial e usada conforme a política aplicável para mensuração e desconto. |
| Estágio 1 | Estado no qual se reconhece ECL de 12 meses quando não houve aumento significativo do risco desde o reconhecimento inicial, observadas as exceções aplicáveis. |
| Estágio 2 | Estado no qual se reconhece ECL lifetime por aumento significativo do risco desde o reconhecimento inicial, sem que o ativo esteja necessariamente credit-impaired. |
| Estágio 3 | Estado de ativo com problema de recuperação de crédito, com ECL lifetime calculada pelo tratamento aplicável de cash shortfall e recuperações. |
| Feature leakage | Uso, direto ou indireto, de informação indisponível na data de observação ou derivada do target futuro. |
| Forward-looking | Incorporação de informação razoável e suportável sobre condições futuras em curvas e ECL, com cenários e premissas rastreáveis. |
| FVOCI | Fair Value Through Other Comprehensive Income; mensuração ao valor justo por meio de outros resultados abrangentes, conforme critérios aplicáveis. |
| FVTPL | Fair Value Through Profit or Loss; mensuração ao valor justo por meio do resultado. |
| Garantia / collateral | Direito ou ativo que pode reduzir o déficit de caixa esperado após consideração de valor, haircut, custos, prazo de execução e risco de dupla contagem. |
| Golden case | Caso pequeno com inputs, fórmula e resultado esperado calculado independentemente, usado como referência automatizada. |
| Grupo homogêneo | Conjunto de exposições com características de risco compartilhadas e validação de homogeneidade; não é apenas uma faixa arbitrária de score. |
| Haircut | Redução prudente e documentada aplicada ao valor de garantia ou recuperação. |
| Hazard | Probabilidade condicional de default em um período dado que a exposição sobreviveu sem default até o início desse período. |
| IFRS 9 | Norma de instrumentos financeiros que inclui classificação e mensuração, impairment e hedge accounting. O escopo principal deste projeto é impairment/ECL. |
| LGD | Loss Given Default; proporção da exposição perdida após recuperações líquidas, custos e desconto, conforme a metodologia versionada. |
| Lineage | Encadeamento verificável entre dados de entrada, transformação, modelo, política, configuração, código e resultado. |
| Low-credit-risk exemption | Expediente aplicável somente quando permitido e configurado por política; não é atalho automático para manter Stage 1. |
| Management overlay | Ajuste pós-modelo separado, justificado, aprovado, versionado, temporário e reversível. |
| Model card | Documento de objetivo, população, dados, método, calibração, performance, limitações, aprovação, vigência e monitoramento de um modelo. |
| OOT | Out-of-time; período temporal mantido fora do desenvolvimento para teste final de generalização. |
| PD | Probability of Default; probabilidade de default definida para uma população, horizonte e cenário. |
| PD acumulada | Probabilidade de default até determinado horizonte. |
| PD marginal | Probabilidade incondicional de default em um período específico, consistente com hazard e sobrevivência. |
| PIT | Point-in-time; estimativa sensível às condições atuais e prospectivas do período de reporte. |
| POCI | Purchased or Originated Credit-Impaired; ativo adquirido ou originado já com problema de recuperação, sujeito a tratamento específico e credit-adjusted EIR. |
| Pré-validador | Componente que executa verificações locais de schema e consistência; não é validador oficial nem garante aceitação pelo regulador. |
| Provisão mínima / piso | Requisito local aplicável em camada separada do ECL econômico/contábil, versionado por fonte e data-base. |
| Rating | Categoria derivada de risco ou PD calibrada segundo política documentada; não é escala regulatória universal por mera nomenclatura. |
| Recalibração | Ajuste da correspondência entre estimativa e frequência observada sem necessariamente alterar a estrutura do modelo. |
| Reconciliação | Demonstração de que resultados fecham entre períodos, cenários, contratos, agregações e camadas de ajuste. |
| Redefault | Novo default após cura, identificado e tratado de forma explícita na metodologia. |
| SICR | Significant Increase in Credit Risk; aumento significativo do risco desde o reconhecimento inicial, avaliado com informação quantitativa e qualitativa. |
| SPPI | Solely Payments of Principal and Interest; avaliação das características dos fluxos contratuais usada na classificação e mensuração aplicável. |
| Sobrevivência | Probabilidade de permanecer sem default até determinado horizonte. |
| Stage | Ver Estágio 1, Estágio 2 e Estágio 3. O termo em inglês pode aparecer em schemas e APIs. |
| Taxa ajustada ao crédito | EIR que incorpora perdas de crédito esperadas nos fluxos estimados de um POCI, conforme tratamento aplicável. |
| Teste de regressão | Verificação repetível de que uma mudança não alterou comportamento suportado fora do objetivo declarado. |
| Validação independente simulada | Pipeline separado do desenvolvimento que aplica critérios objetivos e não permite autoaprovação do modelo pelo mesmo processo. |
| Variável latente | Variável interna do gerador sintético que influencia eventos, mas não pode ser entregue como feature ao modelo. |
| Watchlist | Sinal qualitativo de monitoramento que pode contribuir para SICR segundo política versionada. |
| Write-off / baixa | Redução do valor contábil quando não há expectativa razoável de recuperação na extensão baixada; não elimina o registro de recuperações posteriores. |

## Convenções

- Valores monetários de domínio usam `Decimal` e política explícita de arredondamento.
- Probabilidades são armazenadas internamente em escala de 0 a 1; interfaces devem declarar a unidade exibida.
- Datas de reporte, observação, originação, default e execução são distintas e obrigatoriamente identificadas.
- “Sintético”, “demonstrativo”, “homologado”, “validado” e “aprovado” não são sinônimos.
