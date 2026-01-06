# Documentação Técnica de Perda 4966 - BIP

> **Documento convertido automaticamente de PDF para Markdown**  
> **Arquivo original:** `Documentação Técnica de Perda 4966 - BIP.pdf`  
> **Data de conversão:** 25/07/2025 10:50:37

---

<!-- Página 1 -->









## DOCUMENTAÇÃO TÉCNICA DE CÁLCULO DE
## PROVISÃO PARA PERDA  ESPERADA ASSOCIADAS
AO RISCO DE CRÉDITO











BanPará












27/11/2024

<!-- Página 2 -->


2

## DOCUMENTAÇÃO TÉCNICA DE PERDA
## BANPARÁ
## Segmento: Parcelados e Rotativos   Data: 27/11/2024
## Desenvolvido por:  Marcos Lucas e Beatriz Galino
Revisado por:  Gustavo Secco












<!-- Página 3 -->


3

## S U M Á R I O
1 INTRODUÇÃO  ................................ ................................ ................................ ..............  4
1.1 Introdução do projeto  ................................ ................................ ................................ .. 4
1.2 Características da carteira  ................................ ................................ ............................  6
2 PREMISSAS GERAIS  ................................ ................................ ................................ ... 7
2.1 Write Off (WO)  ................................ ................................ ................................ ..........  7
2.2 Tempo remanescente de contratos de limite  ................................ ...............................  8
2.3 Definição de Reestruturação  ................................ ................................ ......................  9
2.4 Critérios para migração entre estágios – Problema de recuperação de Crédito  ........  11
2.5 Critérios para migração entre estágios – Aumento do risco de crédito  ....................  12
2.6 Cura – Diminuição do risco de crédito  ................................ ................................ ...... 16
3 DESENVOLVIMENTO DE MODELOS  ................................ ................................ ... 19
3.1 Definição de Conceitos  ................................ ................................ .............................  19
3.2 Modelo de PD Concessão  ................................ ................................ .........................  21
3.3 Modelo de score ( behaviour ) ................................ ................................ ....................  27
3.4 Grupos homogêneos de risco  ................................ ................................ ....................  32
3.5 PD Forward  Looking  ................................ ................................ ................................ . 35
3.6 Extrapolação PD 12 para PD vida  ................................ ................................ ...........  435
3.7 Loss Given Default (LGD)  ................................ ................................ ........................  37
3.8 LGD Forward Looking ................................ ................................ ..............................  53
3.9 Exposure At Default (EAD)  ................................ ................................ ......................  61
3.10  Perda Esperada  ................................ ................................ ................................ ..........  63
4 TÍTULOS E VALORES MOBILIÁRIOS  .... ERRO! INDICADOR NÃO DEFINIDO.
5. Anexos  ................................ ................................ ................................ ..........................  70





<!-- Página 4 -->


4

## 1 INTRODUÇÃO
Esta documentação refere -se a metodologia de construção, definição  e cálculo de provisão para
perdas esperadas associadas ao risco de crédito e reporte contábil do BanPará que entra em
conformidade com a norma do Banco Central do Brasil a partir do detalhamento estipulado na Resolução
4966.
Além de algumas definições qualitativas de premissas, foram desenvolvidas análises estatísticas
a partir de  bases históricas. Todas as análises  de modelagem  e o cálculo da Perda Esperada  foram
desenvolvidas em R.
## 1.1 Introdução do projeto
Dentre outros aspectos , a resolução 4966  trata da metodologia completa para  cálculo do
provisionamento de perdas esperadas devido ao risco de crédito dos ativos financeiros de instituições
que tem operações no Brasil . Vale ressaltar que o risco de crédito pode incluir não somente operações
de crédito da instituição, mas também outros ativos financeiros que tenham risco de crédito associados,
como operações de compromissos de crédito, títulos públicos, privados etc.
Para realizar o cálculo a instituição deve definir uma série de regras, premissas e estudos para
compor a conta final que leva em consideração: a exposição base que está sujeita ao risco de crédito, a
probabilidade dos contratos se tornarem um ativo proble ma ou com problema de recuperação, e
probabilidades de recuperação de contratos com problema de recuperação. Em suma, cada ativo
financeiro ( operação ) deve ter um valor calculado individualmente, sendo que a estimativa pode ser feita
para apenas 12 meses o u para a vida toda (prazo remanescente) d a operação , dependendo do estágio que
aquele ativo estiver naquela data base (data da carteira). Para isso a norma exige a construção de modelos
estatísticos com os mesmos parâmetros de risco considerados em Basileia II, que são a Probabilidade
de inadimplência (PD – Probability of Default ), o percentual de Perda dada a inadimplência (LGD –
Loss Given Default ) e a Exposição na data da inadimplência (EAD – Exposure At Default ). Para a
resolução 4966, isso não é difere nte, alterando apenas as nomenclaturas desses modelos de forma a
abrasileirá -las.
Todas as operações ativas da carteira que são considerados escopo de provisão de risco de
crédito devem constar como pertencentes a um dos 3 estágios possíveis, lembrando que operaçõe s ativ as
são aquel as não caracterizados como em prejuízo  (cada instituição define o ativo em prejuízo através de
estudos da sua carteira, sendo que o Banpará considerou contratos com atraso maior que 360 dias de
atraso , conforme definido no item 2.ii.).

<!-- Página 5 -->


5

## Segue a definição para alocação em estágios para a carteira ativa:
Estágio 1 : Operaçõe s que não apresentam aumento significativo relativo ao risco de crédito com
relação a data inicial da operação. Neste caso a perda esperada é baseada no cálculo para uma janela
futura d a vida (PD para o prazo remanescente d a operação ) limitado a 12 meses (PD 12 meses);
Estágio 2 : Operaçõe s que apresentam aumento significativo relativo ao risco de crédito com
relação a data inicial da operação. Neste caso a perda esperada é baseada no cálculo para uma janela
futura da vida (PD para o prazo remanescente d a operação , devendo compor no mínimo a PD12 meses );
Estágio 3 : Operaçõe s com evidências de perdas  ou com problema de recuperação de crédito.
Neste caso a perda esperada é baseada no cálculo para uma janela futura da vida, porém a PD neste caso
é 100% uma vez que o estágio 3 é a própria inadimplência.  Essa caracterização recebe a mesma definição
instituída na resolução 4557.
O conceito de risco de crédito d a operação  deve ser baseado na probabilidade de default  para
sua vida toda .
Originalmente um a operação começa a ser contabilizad a em estágio 1 e, posteriormente, a cada
data base, deve -se avaliar se este ativo apresentou aumento significativo no risco de crédito desde o
reconhecimento inicial; em caso positivo, est a operaçã o deve passar a ser considerad a em estágio 2, ou
ainda se o ativo, além de apresentar aumento significativo no risco de crédito, apresentar evidência
objetiva de recuperação de crédito , será alocado em estágio 3. Por fim, se a operação , além de apresentar
a evidê ncia de recuperação de crédito , tiver estimativas insignificantes de recuperação, est a deve ser
baixad a para prejuíz o.
As definições de aumento significativo e evidência de ativo problemático , são baseadas não
apenas em aspectos qualitativos e prospectivos (projeções de modelos de probabilidade de default ), mas
também no atraso efetivo do ativo financeiro.
Em relação à avaliação do atraso, a norma prevê uma premissa refutável de 30 dias de atraso
para aumento significativo e 90 dias de atraso para evidência de default . No caso de  default, ainda deve
ser considerado todos os conceitos estipulados pela resolução 4557 para considerar um ativo como
problemático, sendo assim, será alavancado principalmente devido ao cliente declarar recuperação
judicial, houver algum contrato na instit uição determinado como reestruturação ou até se outros
contratos daquele cliente  já for considerado com problema de recuperação de crédito (arrasto de
contratos d a mesma contraparte ).
Já com relação aos aspectos prospectivos , a norma prevê que seja feita um a consideração
estatística nos patamares de risco de crédito (tanto na PD quanto LGD) devido a alteração

<!-- Página 6 -->


6

macroeconômicas atualizadas recorrentemente. Para isso, deve ser realizados estudos que evidenciem
aumentos ou reduções correlacionadas com os impactos adversos externos a instituição.
Outro aspecto normativo é a necessidade de consideração do aumento de risco do contrato desde
o seu reconhecimento inicial. Essa avaliação deve ser realizada a partir de estudos que mostrem um
efetivo aumento de risco quando um contrato tem uma variação co nsiderável de risco de crédito ou PD
em comparação com o seu risco de concessão ou inicialmente estimado na vida do contrato. Além da
avaliação do aumento do risco refletivo na mudança do ativo para estágios maiores (estágio 2 e estágio
3), existe a possib ilidade desses ativos apresentarem sinais de diminuição do risco (cura), sendo que esta
melhora deve ser refletida na volta do ativo para estágios menores (estágio 1 e estágio 2).
Ainda, apesar de o estágio alocado e as estimativas de perdas deverem ser feitas para cada ativo
financeiro individualmente, a norma prevê a possibilidade de avaliação em bases coletivas, contanto que
estes agrupamentos de ativos representem grupos homogên eos de risco, o que deve ser validado
periodicamente.
Devido ao fato de as métricas de alocação em estágios, a definição de inadimplência, a baixa a
prejuízo e os agrupamentos para avaliação em bases coletivas estarem abertas, é necessária uma etapa
antecedente à modelagem para a definição dessas premissas.
## 1.2 Características da carteira
O escopo da 4966 prevê o cálculo de provisão de perdas esperadas de todos os ativos financeiros
que causam algum potencial risco de crédito para a instituição. Com isso , após realizadas análises  das
diferenças de riscos, foram divididos  os ativos do BanPará entre modalidade de crédito rotativos,
parcelados  e consignado  para a amostra para o ano de 2022 :

## Tabel a 01 - Inadimplência por produto
## Produtos Total de contratos Total de Default Risco Médio (%)
## Consignado 588.051                     23.047                    3,92
## Parcelados 1.243.546                  64.897                    5,22
Rotativos 342.718                     53.999                    15,76

<!-- Página 7 -->


7

## 2 PREMISSAS GERAIS
## 2.1 Write Off (WO )
A norma 4966 determina que se faça um estudo estatístico para ter a definição do Prejuízo e,
para isso, se observa o período em que ocorre estabilização da recuperação e, com isso, o momento em
que contratos serão baixados como prejuízo. A figura abaixo  traz a média das  rolagens calculadas de
janeiro de 20 22 a dezembro  de 2022. No caso de parcelados , nota -se que a  após 150 dias  de atraso a
rolagens tem uma tendência de aproximação de 100% de saldo  e, na faixa dos 360 dias o percentu al
faixa a faixa se aproxima na média entre 95% e 100% . Isso indica, que após esse período, não há mais
recuperações e esse pode limiar pode ser considerado prejuízo para a grande maioria da carteira d o
Banpará . O mesmo acontece para Rota tivos .


Gráfico 1 – Análise de rolagem  em 510 dias de Atraso – Parcelados

## 3%29%93%
## 76%87%101%
## 86%100%
## 90%102%
## 95%92%106%
## 87%98%95%99%
## 0%20%40%60%80%100%120%
30 60 90 120 150 180 210 240 270 300 330 360 390 420 450 480 510Parcelados

<!-- Página 8 -->


8


Gráfico 2 – Análise de rolagem em 420 dias de Atraso  – Rotativos

## 2.2 Tempo remanescente d e contrato s de limite
A Resolução CMN n° 4.966 determina que a avaliação de risco de crédito deva ser estipulada
para todo o prazo remanescente do contrato. Mais especificamente, para contratos em estágio 2, esse
conceito será utilizado para calcular a Probabilidade de Default durante toda a vida do ativo.
No caso de contratos parcelados com prazos de vencimento pré -definidos, deve -se considerar a
própria diferença da data de referência e a data de vencimento do contrato. Já para contratos com créditos
a liberar, limites de crédito concedidos e rotativos, de ve-se estipular a partir de estudo da carteira. A
definição aqui, foi baseada na observação de estabilização da quantidade de contratos em estágio 2 a
partir de um mês de referência M 0. O tempo médio desses contratos no tempo em estágio 2 é o tempo
em que deve ser calculado o risco para o tempo de vida desses contratos.  O período de desenvolvimento
do estudo foi de janeiro de 2022 até dezembro  de 2022.
Como mostra o gráfico a seguir, o tempo de sobrevivência dos contratos rotativos em estágio  2
tendem a ficar muito baixo  após os 1 2 meses , uma vez que o percentual de contratos em estágio 2  após
12 meses fica abaixo de 1%.
## 9%11%71%84%98%101%
## 93%101%97% 98%101%98%113%
## 89%
## 0%20%40%60%80%100%120%
30 60 90 120 150 180 210 240 270 300 330 360 390 420Rotativos

<!-- Página 9 -->


9


## Gráfico  03 – Tempo de sobrevivência para rotativos
## 2.3 Definição de Reestruturação
De acordo com a norma, a instituição deve definir o conceito de reestruturação, que seriam
aqueles contratos reformulados ou criados a partir de outros contratos que possuem alteração ou
reformulação contratual devido a um aumento de risco de crédito ou problema de recuperação de crédito.
A reestruturação, diferente da renegociação, será caracterizada como tal quando es sa houver uma
reformulação que implique em uma concessão significativa de risco. Entende -se por concessão significa
de risco, tudo aquilo qu e implique em uma redução no patamar de saldo contábil ao risco de crédito,
tanto no momento quanto comparado com o valor do dinheiro no tempo.
Foi utilizado para marcação de reestruturação, um a base de contratos que fizeram renegociação
de um contrato cuja contraparte apresenta evidente problema de recuperação de crédito e por isso teve
seu contrato original quitado e nascimento de um novo.
Para renegociações identificadas pelo BanPará como  confissão de dívida e para aquelas
caracterizadas como renegociações de PJ, foram consideradas diversas características que as qualificam
como reestruturações.  A primeira delas foi pautada em estudo estatístico em se observou que
renegociações realizadas em contratos com mais de 30 dias de atraso possuem probabilidade alta de se
tornar ativo problemático nos próximos meses. De forma mais objetiv a foi observada a taxa de contratos
que se tornam inadimplentes  nos próximos 12 meses  da carteira do Banpará no período de 2020 e 2021é
de aproximadamente 3%, enquanto os contratos renegociados de contrato original com mais de 30 dias
possuem taxa  de 21% no momento de nascimento dessa renegociação, no mesmo período.   0,0%5,0%10,0%15,0%20,0%25,0%30,0%
1 2 3 4 5 6 7 8 910 11 12 13 14 15 16 17 18 19 20 21 22 23 24

<!-- Página 10 -->


10

Além desse estudo, foi considerado outros fatores para considerar renegociações como
problemas de recuperação, ou seja, reestruturação. Esses fatores mostraram evidentes problemas de risco
de crédito dentro da avaliação qualitativa do Banpará, entretanto, devido à falta de informaçã o de
marcação dos contratos renegociados nas bases de dados histórica, e principalmente de dados de
marcação dos contratos originais dos mesmos não foi possível confirmar as decisões qualitativas de
## forma analítica/histórica. Seg ue o resumo das regras:
• Para renegociações caracterizados pelo banpará como confissão de dívida e renegociações de
## PJ nós apoiamos a decisão de que devem ser considerados reestruturações:
Contratos cujo contrato original possuíam atraso superior 30 dias OU;
Contratos cujo o contrato original eram uma confissão de dívida OU;
Contratos cujo o contrato original eram uma renegociação de PJ OU;
Contratos cujo o contrato original eram um parcelamento de fatura de cheque especial OU;
Contratos cujo o contrato original eram um parcelamento de fatura de cartão de crédito OU;
Contratos cujo o contrato original eram uma repactuação de banparacard.
• Para renegociações caracterizados pelo banpará como parcelamento de fatura de cartão de
## crédito em atraso devem ser considerados reestruturações:
Contratos cujo contrato original (fatura do cartão de crédito) possuíam atraso superior a 90
dias;
• Para renegociações caracterizados pelo banpará como repactuações de banparacard e devem
## ser considerados reestruturações:
Contratos cujo contrato original possuíam atraso superior a 90 dias;
É importante destacar que o estudo embasou a definição da regra que será marcada na
implantação da s bases de dados e que serão consumidas pel o cálculo de perda esperada. Porém, para
fins de modelagem de dados históricos, os contr atos reestruturados foram marca dos da melhor forma
possível, visão minimizar os impac tos dos pro blemas operacionais ocasionados em decorr ência das
ausências dessas marcações.  Para tal, foi considerado contratos novos que possuíam até 50%, para mais
ou menos, da soma do saldo contá bil dos contratos que deixaram de existir no mês posterior. A fim de
evitar um comportamento inflacionário quanto ao risco de default  ocasionado pela marcação da
reestruturação foram considerados contratos reestruturados que tivessem no mínimo contratos originais
com 30 dias de atraso.


<!-- Página 11 -->


11

## 2.4 Critérios para migração entre estágios – Problema de
## recuperação de Crédito
De acordo com a norma, estágio 3 devem ser todos os contratos que têm evidência  de problema
de recuperação de crédito. A norma evidencia algumas regras objetivas para definição de ativo
problemático  tais como atrasos de pagamento do contrato a mais  90 dias em atraso, contratos
caracterizados como reestruturados na instituição , clientes em recuperação judicial  e/ou tutela . A
reestruturação foi pautada no estudo do tópico supracitado e as outras decisões quali. e quantitativas
estão explicitadas na política de definição de ativo problemático do Banpará.
Para a marcação dos contratos que possuíam essas características  no histórico utilizado na
modelagem,  foram utilizadas  as bases , recuperação  judicial , marcação de reestruturação  e a variável de
atraso . Para tutelas observadas no histórico  assumiu -se que será considerado como ativo problemático
apenas as que possuem atrasos superiores a 30 dias .
Além disso, pode ser considerado o arrasto para contratos marcados como  ativo problemático.
O arrasto indica que se um contrato for caracterizado como ativo problemático todos os contratos da
mesma contraparte devem receber a  mesma marcação. Todavia, de acordo com as diretrizes
estabelecidas na Resolução CMN n° 4.966 nos artigos 42 e 43, o arrasto não precisará ser aplicado para
## os contratos que possuírem as seguintes características:
• Que pertençam ao mesmo grupo homogêneo de risco;
• Que sejam definidos na política de crédito e nos procedimentos de gestão de crédito da
instituição como operações de varejo;
• Cujo gerenciamento seja realizado de forma massificada;
Em vista dos critérios acima  não foi necessário aplicar o arrasto para os contratos analisados
uma vez que os contratos são alocados por grupos semelhantes de risco e por características de produtos;
são caracterizados como operações de varejo e são gerenciados de forma massificada. O gerenciamento
massificado é compreendido como uma gestão não individualizada  dos contratos existentes . Dado um
rating  atribuído no modelo de concessão todos os contratos que tiverem essa mesma classificação serão
tratados de forma padronizada  pela instituição . Dessa forma, a disponibilização de  pacotes de serviços
bancários, cartões de crédito com taxas e limites pré -definidos  e empréstimos serão aplicados de uma
forma padrão  as contrapartes que tiverem a mesma classificação inicial.  As informações sobre gestão
massificada podem ser verificadas nas políticas de crédito do Banpará .



<!-- Página 12 -->


12

## 2.5 Critérios para migração  entre estágios  – Aumento do risco de
## crédito
Segundo a norma, os ativos que devem ser considerados como estágio 2 são aqueles com
aumento significativo do risco de crédito desde o reconhecimento inicial,  tendo como premissa refutável
o atraso em 30 dias  (limitado a 60 dias ).
Além das premissas refutáveis baseadas nos dias em atraso, a norma prevê que o aumento
significativo do risco de crédito (Estágio 2) deve ser detectado com antecedência mesmo antes do atraso,
através da análise do risco de crédito. Dessa forma os grupos homogêneos de risco (gerados pelo modelo
de PD) avaliados no momento da análise da carteira e comparados com o grupo de risc o no momento
da concessão podem causar alocação de contratos em estágio 2, a depender dos triggers definidos para
tal.
Para a aplicação da norma supracitada, é realizada uma análise  da quantidade de contratos  em
default  em relação a quantidade total de contratos para as respectivas duplas de PD concessão e PD.
Caso exista um aumento  significativo, normalmente  em torno de 200%, do risc o dos contratos que
estavam na PD inicial  e foram para a PD atual com um risco significativamente maior , ou seja, houve
um aumento factual do risco do contrato,  ele será alocado como estágio  2 em decorrência do aumento
do risco relativo .
Para avaliação das premissas refutáveis citadas,  foram desenvolvidos estudos de rolagem para
analisar se as premissas refutáveis de atraso fazem sentido na carteira d o BanPará . Depois avaliamos as
rolagens de cada faixa de atraso para default  e caso o percentual fosse  significativo ( a partir de  50%)
concluímos que esta faixa de atraso deveria  ser estabelecida como aumento significativo do risco de
crédito  (Estágio 2) . Foram considerados os contratos sem mau na origem e com no mínimo 12 meses de
existência do contrato.  Abaixo seguem os resumos  calculados de Jan/22 a Dez/22:


## Tabela 02 – Rolagem de default para  rotativos
## FAIXA ATRASO BAD RATING
## 0 14,32%
## 1 36,39%
## 15 56,26%
## 30 76,03%
## 60 87,76%Rotativos
ESTÁGIO 2ESTÁGIO 1

<!-- Página 13 -->


13

• Legenda:  em vermelho foram destacados os públicos de contratos que tiveram um aumento
percentual elevado de risco que justificam caracterização desses contratos como evidência de
aumento significativo de risco desde a sua originação.
• Bad Rate: é a mesma regra do ativo problemático em 12 meses. O "bad rat e" é um indicador que
determina o nível de risco e as potenciais perdas financeiras que podem ocorrer, influenciando
decisões de investimento e gestão de risco, de forma direta é a proporção de clientes maus.



Tabela 03 – Rolagem de default para parcelados


Tabela 04 – Rolagem de default para consignado

Vale destacar que a definição de aumento significativo de risco desde o reconhecimento inicial
do contrato adicionado na regra de alocação de estágio 2 , seguiu a partir das seguintes regras em  que
define patamares relativos ou absolutos de comparação da PD12 meses behavior  atualizada na base de
cálculo v ersus a PD 12 meses de concessão dos contratos.  Segue a baixo a  tabela resumo  para rotativos
## e parcelados :
## FAIXA ATRASO BAD RATING
## 0 4,64%
## 1 10,54%
## 15 29,73%
## 30 64,83%
## 60 91,47%Parcelados
## ESTÁGIO 1
## ESTÁGIO 2
## FAIXA ATRASO BAD RATING
## 0 4,01%
## 1 17,66%
## 15 53,41%
## 30 64,57%
## 60 82,79%ESTÁGIO 1
ESTÁGIO 2Consignado

<!-- Página 14 -->


14

## Parcelados
Para a análise  do aumento de risco da PD relativa para parcelados foi considerado um aumento
percentual acima de 200%  do risco inicial para o risco  behavior  do contrato . Para esse público foi
considerado estágio 2  os contratos  que iniciaram com a PD concessão  nos três melhores grupos, de
1,86% até 5,48% e migraram para os dois piores grupos da PD 1 2 entre  11,12% até 29,57%.

Tabela 05 - Definição de aumento significativo desde o reconheicmento inicial para alocação em
Estágio 2 para Percelados


• Legenda:  em vermelho foram destacados os públicos de contratos que tiveram um aumento
percentual elevado de risco que justificam caracterização desses contratos como evidência de
aumento significativo de risco desde a sua originação.

Esse estudo contém uma matriz de GH (Grupos Homogêneos de Risco) de PD concessão ou PD Inicial
e a PD Behavior ou PD atual. A comparação é realizada comparando o patamar de aumento da BadRate
daquele cluster  (célula da matriz) com a sua respectiva PD inicial. Se o aumento se apresentar
significativo em relação aos demais (pelo menos acima de 1 90% de aumento), propõe -se a consideração
desse cluster  como aumento significativo de risco desde o reconhecimento inicial sendo esses contratos
marcados como estágio 2.


Consignado

<!-- Página 15 -->


15

Para a análise do aumento de risco da PD relativa para consignado  foi considerado um aumento
percentual acima de 200% do risco inicial para o risco behavior  do contrato . Para esse público foi
considerado estágio 2 os contratos que iniciaram com a PD concessão nos dois melhores grupos, de
1,86% e 2,70% e migraram para os dois piores grupos da PD 12 entre 11, 05% até 18,02%.

Tabela 06 - Definição de aumento significativo desde o reconheicmento inicial para alocação em
Estágio 2 para Consignado

## Rotativos
Para rotativos foi considerado um aumento percentual acima de 200% e PD 12 média acima de
45%. Para esse público foi considerado estágio 2 os contratos  que iniciaram com a PD concessão nos
dois melhores grupos, de 1,64% e 9,81% e migraram para os dois piores grupos da PD 12 e para
contratos que nasceram com PD 12 acima de 45%.

Tabela 07 - Definição de aumento significativo desde o reconheicmento inicial para alocação em
## Estágio 2 para Rotativos
## Outras marcações qualitativas para definição de estágio 2:
o Parcelamento de fatura cartão que não sejam caráter de reestruturação OU;

<!-- Página 16 -->


16

o Parcelamento de fatura de cheque especial que não sejam caráter de reestruturação OU;
o Repactuações de Banpa racard que não sejam caráter de reestruturação OU;
o Confissão de Dívida que não sejam caráter de reestruturação OU;
o Renegociações de PJ que não sejam caráter de reestruturação;


## 2.6 Cura  – Diminuição do risco de crédito
O conceito de cura é utilizado para reduzir o estágio de contratos que já tenham tido algum
aumento no risco  (Estágio 2 ou Estágio 3 ). Esta cura é definid a como o período considerado para que
uma operação comprove que efetivamente teve uma diminuição no nível de risco de crédito, garantindo
que os patamares de risco são os aceitáveis para estágios menores .
Aqui, foram feitos dois estudos, um de cura para o Estágio 1 e outro de cura para o Estágio 2.
O objetivo deste estudo foi o de avaliar qual o número de meses consecutivos em pagamento (sem
ocorrência de atraso) em que se ating iu uma média de PD geral menor do que a média do estágio para
o qual se desejava voltar, e então este momento foi definido como o da cura . Em cada tabela temos a
taxa de inadimplência nos meses consecutivos de pagamento bem como a taxa média de inadimplência
do estágio para o qual o c ontrato migra em caso de cura . Para o público de consignado não foi
desenvolvido um estudo de cura uma vez que essa carteira apresenta um comportamento muito
específico  quanto a risco e a duração dos contratos  apresentando uma baixa perspectiva de mudanças de
estágio  para um contrato . Além de estar atrelado a salários, benefícios ou recebimento muito estáveis ao
longo do tempo para o cliente. Dessa forma, a análise  de migração  de estágio para  esses casos não
refletirá o real comportamento dessa carteira.
## Parcelados
• Cura para Estágio 2

Tabela 08 – Cura para estágio 2 para P arcelados

## Mês/Ano M0 M1 M2 M3 M4 M5
## Estágio 2 1 1 1 1 1
% Inadimplência em 12 meses 100,0% 8,5% 6,4% 5,7% 4,5% 3,9%Estudo de Cura do Estágio 2 para Estágio 1
Inadimplência Média em 12 meses para o Estágio 1 - 4,3%

<!-- Página 17 -->


17

• Cura para Estágio 3

## Tabela 09 – Cura para estágio 3 para Parcelados
Para o mês 9  de cura em parcelados , não foram encontrados contratos necessários para a realização do
estudo  para os meses subsequentes. Dessa forma, considerou -se a cura tendo em visa essa janela de 9 .

## Rotativos
• Cura para Estágio 2

## Tabela 10 – Cura para estágio 2 para Rotativos
• Cura para Estágio 3

Tabela 11 – Cura para estágio 3 para Rotativos

O valor da inadimplência média (PD) para o Estágio 1 no período de estudo foi de 4,3% para
parcelados  e 13,3% para rotativos . Já o valor da inadimplência média (PD) para o Estágio 2 no período
de estudo foi de 16,8% para parcelados  e 28,8% para Rotativos . Para o Estágio 3 de 100%, uma vez que
esta é a própria definição de inadimplência.
Para melhor entendimento, vamos detalhar a análise de cura do segmento Rotativos , e os demais
seguiram a mesma linha. Avaliando os valores de risco de default  no estudo de  cura para estágio 2,
observamos que os contratos que estavam em estágio 3 e pagaram 7 parcelas em dia  (ficaram em dia
durante 7 meses)  apresentaram uma PD menor do que a média do estágio 2 com o valor de  20,0%, sendo
## Mês/Ano M0 M1 M2 M3 M4 M5 M6 M7 M8 M9
## Estágio 3 2 2 2 2 2 2 2 2 2
% Inadimplência em 12 meses 100,0% 48,2% 53,3% 50,0% 40,6% 34,8% 31,3% 25,0% 25,0% --Estudo de Cura do Estágio 3 para Estágio 2
## Inadimplência Média em 12 meses para o Estágio 2 - 16,8%
## Mês/Ano M0 M1 M2
## Estágio 2 1 1
% Inadimplência em 12 meses 100% 15% 10,1%Estudo de Cura do Estágio 2 para Estágio 1
## Inadimplência Média em 12 meses para o Estágio 1 - 13,3%
## Mês/Ano M0 M1 M2 M3 M4 M5 M6 M7
## Estágio 3 2 2 2 2 2 2 2
% Inadimplência em 12 meses 100% 36,2% 40,4% 40,0% 42,3% 33,3% 37,5% 20,0%Estudo de Cura do Estágio 3 para Estágio 2
Inadimplência Média em 12 meses para o Estágio 2 - 28,8%

<!-- Página 18 -->


18

este o momento ideal da cura de um contrato em estágio 3 para o estágio 2 ou 1 neste segmento . Para a
cura do estágio  2 o comportamento descrito acima é observado no mês 2 que possuem contratos com
um ri sco inferior ao risco dos contratos em estágio  1 em M0.
## As regras de cura ficaram da seguinte forma:
• Cura de estágio 2 para 1: fica-se definido  5 meses para parcelados  e 2 meses para cura de
Rotativos .
• Cura  de estágio 3 para 2  ou 1: fica-se definido 9 meses para parcelados  e 7 meses para cura
de Rotativos .

Essa abordagem leva em considerações todo o tipo de contrato migrado para estágio 2 ou 3, ou
seja, as reestruturações também terão  cura caso elas venham a pagar recorrentemente dentro do
período estipulado no estudo.

<!-- Página 19 -->


19

## 3 Desenvolvimento De Modelos
## 3.1 Definição de Conceitos
A Perda Esperada é composta pelas componentes de risco conforme acordo de basileia:
𝑃𝐸=𝑃𝐷(𝑃𝑟𝑜𝑏𝑎𝑏𝑖𝑙𝑖𝑡𝑦  𝑜𝑓 𝐷𝑒𝑓𝑎𝑢𝑙𝑡 )∗𝐸𝐴𝐷 (𝐸𝑥𝑝𝑜𝑠𝑢𝑟𝑒  𝐴𝑡 𝐷𝑒𝑓𝑎𝑢𝑙𝑡 )∗𝐿𝐺𝐷 (𝐿𝑜𝑠𝑠  𝐺𝑖𝑣𝑒𝑛  𝐷𝑒𝑓𝑎𝑢𝑙𝑡 )
A PD é a probabilidade futura de um ativo entrar em inadimplemento em uma janela de tempo
determinada, o EAD é o valor da exposição deste ativo na data deste inadimplemento, e o parâmetro
LGD é o percentual que se espera perder deste valor. A combinação de stes parâmetros pode ser utilizada
como uma expectativa das perdas de um determinado ativo (ou Perda Esperada).
Para a PD temos as etapas da marcação da variável resposta na base, modelagem do escore, a
criação dos grupos homogêneos e o ajuste cíclico futuro denominado Forward Looking . Para a marcação
da PD  foi considerado o default  do contrato dentro do período de 12 meses a frente do período atual ,
isto é, caso o contrato marcação de ativo problemático (estágio 3)  em um período de 12 meses  ele será
considerado o nosso target do modelo (default em 12 meses) . Já no LGD temos também um modelo de
score/ordenação, uma d efinição de grupos homogêneos e a determinação de um valor de LGD fixo para
cada grupo , além do ajuste cíclico futuro denominado Forward Looking .
A seguir observaremos cinco  seções associadas somente ao modelo de PD. Isso se deve ao nível
de complexidade atribuído a este tipo de modelagem. Em linhas gerais, n um primeiro momento é
necessário  o desenvolvimento de um modelo de score  (ordenação de risco) na originação do contrato,
chamado modelo de concessão para posterior comparação com a data base e definição do aumento
significativo de risco. No segundo passo,  o desenvolvimento de um modelo de score  na data base  que
posteriormente deve ser trabalhado para gerar agrupamentos de risco denominados Grupos Homogêneos
de Risco. Em seguida estes grupos definidos em uma visão não cíclica devem ser ajustados de acordo
com fatores macroeconômicos e/ou de política de crédito, este modelo de ajuste é denominado Forward
Looking . Além disso,  devemos ter um cálculo de PD 12 meses para contratos, e um cálculo de PD para
a vida para contratos. Dessa forma, como os modelos de score , grupos homogêneos e Forward Looking
foram desenvolvidos para PD 12, foi necessário criar uma curva de extrapolação pa ra o modelo de PD 12
levando a valores de PD vida.
A base de dados para o estudo estatístico deve permitir o acompanhamento temporal de cada
operação, uma vez que dependemos da observação de recuperações de um contrato em uma janela de
tempo. Dessa forma, a sua construção depende da compilação de diferente s datas -bases. Introduzimos
aqui o conceito de ponto de observação, que nada mais é do que a definição de uma data de referência

<!-- Página 20 -->


20

a partir da qual será feito o acompanhamento de operações por um tempo determinado. O estudo requer
que exista o máximo de histórico  / pontos de observação. O tempo de acompanhamento das operações
(futuro à data de referência) será referido como janela de performance  (ou visão ever no caso da PD) : é
neste  período  que se avalia, por exemplo, se a operação se tornou inadimplente ou não.
Supondo que a data mais recente de informação disponível em sistemas é Agosto  de 20 22 e
supondo que a janela de performance definida é de 12 meses, o ponto de observação mais recente
acompanhável nesta janela é Agosto  de 20 21 (veja que sempre perde -se um ano na apuração dos dados)
e o mais antigo será a data base mais antiga disponível para o estudo .
Vale ressaltar que quanto maior a janela de observação definida, maior será a quantidade de
meses que se volta no tempo com relação a data da última observação disponível, data de “hoje”.
Na Figura  podemos ver o que foi descrito acima , sendo o “hoje” do exemplo a data de dez/17,
PO a data de referência, e P1 a P12 os momentos “futuros” a data de referência em que se observa  a
informação de interesse . Portanto , através do cálculo  da janela  dos 12 meses futuros  (PD 12 meses) ,
obtém -se a perda esperada (PE) .

Figura 01 - Janela de observação.
Os modelos utilizados aqui foram , PD concessão  e PD Behavior  construído  ambos  a partir de
uma Regressão Logística, alimentada com variáveis cedidas pel o BanPará .


## jan/15
## fev/15
## mar/15
## abr/15
## mai/15
## jun/15
## jul/15
## ago/15
## set/15
## out/15
## nov/15
## dez/15
## jan/16
## fev/16
## mar/16
## abr/16
## mai/16
## jun/16
## jul/16
## ago/16
## set/16
## out/16
## nov/16
## dez/16
## jan/17
## fev/17
## mar/17
## abr/17
## mai/17
## jun/17
## jul/17
## ago/17
## set/17
## out/17
## nov/17
## dez/17
## jan/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## fev/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## mar/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## abr/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## mai/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## jun/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## jul/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## ago/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## set/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## out/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## nov/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## dez/15 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## jan/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## fev/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## mar/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## abr/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## mai/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## jun/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## jul/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## ago/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## set/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## out/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
## nov/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12
dez/16 PO P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12

<!-- Página 21 -->


21

## 3.2  Modelo de PD Concessão
## Dados
Para construir o modelo de PD Concessão, foi introduzido a marcação de performance de default
juntamente da marcação do score  dos contratos concedidos entre o período de janeiro  de 202 2 até
dezembro  de 202 2 para o desenvolvimento de parcelados , consig nado e rotativos.  É de vital importância
destacar que o público -alvo para a PD Concessão abrange apenas os contratos que possuem no máximo
três meses de vida desde a data de contratação até seu respectivo mês de referência.
A fim de mitigar o efeito do ciclo econômico na média da inadimplência (visão  Through The
Cycle  – TTC), considerou -se o máximo de bases possível, dentro do intervalo citado, no
desenvolvimento da PD Concessão.
## Metodologia
Para o cálculo da estimativa da probabilidade de default  de um cliente na concessão, foi utilizada
a métrica de modelagem estatística com janela de 12 meses. Para a realização deste estudo, foi realizado
a verificação se o modelo de score  segmenta bem o risco e ordena em grupos homogêneos ao longo do
tempo. Com essa abordagem, conseguimos inferir que o modelo de score concessão possui correlação
de risco de crédito nos moldes dos conceitos da norma 4966.
Sabe -se que na definição de premissa de  default , um cliente é considerado em  default  caso o
número de dias de atraso dele seja igual ou superior a 90 dias. Esta marcação foi feita na visão  ever para
a modelagem de PD – ou seja, basta chegar em 90 dias em algum momento da janela de observação
para ser considerado  default .
Para o cálculo da PD estimada 12 meses, foi utilizado o modelo estatístico de Regressão
Logística, uma vez que tal modelo se aplica de forma satisfatória para explicitar a ocorrência de
fenômenos de natureza binária, ou seja, 1 (caso  default ) e 0 (caso não  default ).
O modelo tem como finalidade o cálculo da probabilidade de ocorrência do evento de  default ,
dado algumas informações sobre a característica do cliente. Abaixo descreve -se o modelo utilizado:
Função logística:   assumindo valores entre 0 e 1, para qualquer Z entre - ∞ e +
## ∞ onde  , em que   é a covariável (característica do contrato) e  𝑝 é a
probabilidade de  default .


<!-- Página 22 -->


22


Figura  02 – Função  logit.


O termo   representa a chance ( odds ) de ocorrência do  default  e a função   é a
probabilidade de o cliente entrar em  default  dado a característica das variáveis explicativas. Para a
estimação dos parâmetros do modelo de regressão logística  , foi utilizado a função de máximo
verossimilhança.
Para a construção dos Scores  usados nas quebras dos GH é aplicado uma transformação no
resultado da regressão linear  (predict)  da seguinte forma: (1 – predict) * 1000. Dessa forma, teremos no
resultado  um score  de 0 – 1000 para cada operação.
Para a modelagem foram analisadas diversas variáveis , de todas, foram selecionadas as
variáveis significativas na probabilidade de  default :

## •       Parcelados :
→ Tempo do relacionamento do cliente em meses ;
→ Existência de renegociação do cliente ;
→ Existência de cheque especial do cliente;
→ Existência de atraso do cliente;
→ Razão entre o saldo em atraso pelo saldo utilizado do cliente .

## •       Rotativos :
→ Porte do cliente;
→ Tempo de relacionamento do cliente em meses ;
→ Existência de atraso maior do que 30 dias do cliente;
→ Existência de cheque especial do cliente ;
→ Razão entre o saldo em atraso pelo saldo utilizado do cliente.

<!-- Página 23 -->


23


A partir do  score  calculado pelo modelo de regressão logística, ordena -se a base de dados por
este score  e, gradativamente, são criadas quebras, objetivando construir faixas de mesmo tamanho a fim
de agrupá -las e gerar os Grupos Homogêneos de risco (GH) para os dois segmentos ( parcelados  e
rotativos ). Sendo assim, uma primeira versão de agrupamento é gerada, porém não definitiva, uma vez
que são reagrupados com diferentes pontos de corte de forma que dentro de cada GH a PD na concessão
fosse muito parecida (homogênea) e entre os GHs a média de PD fos se distante (heterogênea). Após
esta análise e definidos os pontos de corte, chegou -se em 5 grupos para parcelados  e 4 grupos para
rotativos .

## Resultados
Dentro dos modelos utilizou -se o WOE ( Weight of Evidence ) calculado como o “ ln” da razão
entre percentual de não  default  e percentual de  default  em cada faixa de risco, como representado
abaixo:

Este WOE possui um valor específico que demonstra o nível de risco de  default  para cada
categoria da variável, permitindo a inclusão dessas variáveis de forma quantitativa no modelo. O efeito
final da categoria é dado pelo parâmetro estimado multiplicado pelo valor do WOE.

Se o efeito é negativo, significa que a categoria em questão influencia negativamente na PD, ou
seja, estar nesta categoria diminui a probabilidade de  default  do cliente. Analogamente, ter um efeito
positivo aumenta a probabilidade de  default .
Escolhemos as variáveis que mais impactam na PD na concessão e que são estatisticamente
significativas a 5% de significância, ficando os modelos finais de Parcelado e Rotativos ,
respectivamente, como:


<!-- Página 24 -->


24


Tabela 12 - Lista de variáveis e efeitos na PD concessão para Parcelados


Tabela 13 - Categorização das variáveis e efeitos na PD concessão para Rotativos
## Validação
A validação dos modelos foi feita por meio de diferentes métricas e indicadores, sendo eles o
KS, GINI  e ROC. O teste de KS (estatística de  Kolmogorov Smirnov ) é bastante utilizado como
verificação da qualidade do ajuste e tem por base a análise da proximidade entre duas funções de
distribuição, neste caso, a dos clientes  default  e a dos clientes não  default . O cálculo do KS é a diferença
máxima entre as duas funções de distribuição, por isso, quanto maior, mais distantes as funções e,
portanto, melhor o modelo construído, pois discrimina de forma mais evidente as duas populações
(default  e não  default ).
Já o GINI é uma métrica que também avalia a capacidade de discriminação de um modelo de
classificação binária. Ele é calculado como duas vezes a área sob a curva ROC (Característica de
Operação do Receptor) menos um (2*AUC -1). O GINI varia de 0 (sem discri minação) a 1
(discriminação perfeita). Quanto maior o valor de GINI, melhor a capacidade do modelo de classificação
em separar as classes.
Em relação ao ROC, entende -se como um gráfico que mostra a relação entre a taxa de
verdadeiros positivos (sensibilidade) e a taxa de falsos positivos (1 - especificidade) para diferentes
pontos de corte. A área sob a curva ROC (AUC) é frequentemente usada como métrica de desempenho.
Quanto maior a AUC, melhor o modelo. A curva ROC é útil para escolher o ponto de corte ideal que
equilibra sensibilidade e especificidade de acordo com os requisitos do problema.
## ID Variável Descrição Efeito Beta P-valor Peso
1 cliente_tempo_relac_meses Tempo de relacinaomento do cliente em meses - 0,00440 <2e-16 14,95%
2 flag_renegociacao_cliente Existência de renegociação do cliente + 0,51845 <2e-16 3,85%
3 flag_cheque_especial_cliente Existência de cheque especial do cliente + 0,37491 <2e-16 3,93%
4 percentual_contrato_pago_clienteUm menos a Razão entre o saldo utilizado pelo valor do
## contrato do cliente- 1,25874 <2e-16 5,11%
## 5 flag_atraso_cliente Existência de atraso do cliente + 1,39995 <2e-16 23,10%
6 saldo_atraso_div_saldo_total_cliente Razão entre o saldo em atraso pelo saldo utilizado do cliente + 1,19651 <2e-16 4,68%
## 7 Intercept Constante - 2,70184 <2e-16 44,38%
## ID Variável Descrição Efeito Beta P-valor Peso
## 1 porte.do.cliente Porte do cliente - 0,12297 0,000085 7,45%
2 cliente_tempo_relac_meses Tempo de relacionamento do cliente em meses - 0,00505  < 2e-16 17,89%
3 flag_atraso_maior30_cliente Existência de atraso maior do que 30 dias do cliente + 0,88605 0,000000 12,86%
4 flag_cheque_especial_cliente Existência de cheque especial do cliente + 1,15667  < 2e-16 24,32%
5 saldo_atraso_div_saldo_total_cliente Razão entre o saldo em atraso pelo saldo utilizado do cliente + 1,38006 0,000024 8,01%
6 Intercept Constante - 2,19478  < 2e-16 29,47%

<!-- Página 25 -->


25


3.2.1.1  Parcelados

Tabela  14 - Métricas  do modelo  de Parcelados

Os valores apresentados acima para as métricas do modelo de Parcelados  da PD Concessão
estão dentro do esperado, uma vez que um valor de KS de 42% e 32% é bastante bom e indica que o
modelo tem uma capacidade sólida de discriminação entre as classes positivas e negativas. Já para o
GINI um valor de 51% e 43% é considerado muito bom. Em relação ao AUC , uma pontuação de 0, 75 e
0,71 é alta e indica um bom desempenho do modelo. Sendo assim, os resultados que o modelo de
Parcelados  apresentou sugerem um desempenho sólido e capaz de separar bem as classes.


Gráfico  04 - GHs  da PD concessão  para  Parcelados


O agrupamento da PD Concessão para Parcelados  foi realizado com faixas de ratings  próximas
## ETAPA KS GINI AUC
## Desenvolvimento 42% 51% 75%
Validação 35% 43% 71%MODELO CONCESSÃO PARCELADO

<!-- Página 26 -->


26

e risco semelhante. Então, chegou -se a um total de 5 grupos em uma ordenação de risco clara com
homogeneidade de risco ao longo dos meses para um mesmo grupo e heterogeneidade entre o mês a
mês de cada grupo.

3.2.1.2  Rotativos


Tabela  15 - Métricas  do modelo  de Concessão  Rotativos

As métricas observadas para o modelo de Rotativos  da PD Concessão estão em linha com as
expectativas. Para o indicador KS, obtendo valores de 0, 43 e 0,51, podemos considerar que o modelo
exibe uma habilidade esperada  em distinguir entre as categorias positivas e negativas. No caso do GINI,
apresentando valores de 0, 54 e 0,54, pode -se afirmar que o desempenho é significativamente
satisfatório. No que diz respeito à métrica AUC , registrando pontuações de 0, 77 e 0,77, demonstra um
desempenho notável do modelo. Quanto mais próxima de 1 essa pontuação se encontra, melhor é a
capacidade do modelo em classificar de forma precisa as instâncias . Portanto, as métricas avaliadas para
o modelo de Pontuação de Risco sugerem um desempenho satisfatório  na diferenciação das categorias.

## Etapa KS GINI AUC
## Desenvolvimento 43% 54% 77%
Validação 51% 54% 77%MODELO CONCESSÃO ROTATIVO

<!-- Página 27 -->


27


Gráfico  05 - GHs  da PD concessão  para  Rotativos


O agrupamento da PD Concessão para Rotativos  foi conduzido com base em intervalos de
classificação próximos e níveis de risco comparáveis. Isso resultou na identificação de um total de três
grupos, organizados de forma a refletir distintos níveis de risco.
Em resumo,

Tabela 16 – Concessão por GHs para Parcelados

## Tabela 17 – Concessão por GHs para Rotativos
## 3.3 Modelo de score  (behaviour )
## GH PD ScoreMin ScoreMax
## 1 14,48% 0,00 870,77
## 2 9,91% 870,77 937,14
## 3 5,48% 937,14 949,99
## 4 2,70% 949,99 967,04
## 5 1,86% 967,04 1000,00
## GH PD ScoreMin ScoreMax
## 1 38,14% 0,00 834,91
## 2 24,96% 834,91 938,31
## 3 9,81% 938,31 980,57
4 1,64% 980,57 1000,00

<!-- Página 28 -->


28

## Dados
Para o desenvolvimento da modelagem de score  foram utilizadas bases de dados de janeiro  de
2022 até setembro  de 2022 para o desenvolvimento de Parcelados, Consig nado e Rotativos . Já para o
período de validação  foi usado o  intervalo de outubro  de 202 2 até dezembro de 202 2. Consideramos o
máximo de data bases possíveis no desenvolvimento para minimizar o efeito do ciclo econômico na
média da inadimplência (visão Through The Cycle  – TTC).
## Premissas
Os modelos de score  para PD foram segmentados em Rotativo s, Parcelado  e Consignado . Os
segmentos de pessoa física e pessoa jurídica não apresentaram diferenças significativas em relação ao
comportamento da  PD o que possibilitou a  junção desses dois públicos . Além disso, a quantidade de
contratos existentes para o público  de PF apresentou pouc a volumetria que justificasse sua separação .
## Metodologia
Para a modelagem foram analisadas diversas variáveis  (𝑋𝑖), todas elas disponibilizadas pel o
Banpará . Além dos dados na visão de contratos  foram disponibilizadas i nformações cadastrais na visão
cliente . As bases foram utilizadas com o propósito  de aplicar o melhor tipo de visão para as variáveis
em cada um dos modelos, Rotativos  e Parcelados , trazendo consigo às variáveis combinadas, históricas
e de tendência .
Outro processo muito importante é o de criar bins para variáveis categóricas , ou seja, para dados
qualitativos, quando há um código, texto ou qualquer outra informação que  não sejam números
contínuos . Essa “binarização” permite que se abstraia os valores internos da variável em questão para
que através de uma relação de relevância entre variável explicativa e variável resposta faça a melhor
classificação dos valores, abstraindo dezenas ou centenas de informações em poucas classes.
Frente a uma quantidade grande de variáveis a serem aplicadas ao modelo foram feitas seleções
de variáveis seguindo as principais recomendações, análises  e práticas de mercado de modelagem
estatística de onde definimos  as melhores variáveis a serem testadas e posteriormente aplicadas ao
código final .
Para compreender se os resultados do modelo estavam atendendo e fazendo sentido, iniciamos
pela base de treino e olhamos para a Curva ROC e os coeficientes de ROC e Gini, a partiu disso, olhamos
para os betas  e os P-value s das variáveis que rodaram  para entender a relevância de cada variável, se
todas elas ajudavam a explicar o modelo . Também consideramos o VIF (Variance Inflation Factor), que

<!-- Página 29 -->


29

é uma medida para detectar multicolinearidade entre as variáveis independentes  (ou variáveis
explicativas) . A multicolinearidade pode afetar a estabilidade das estimativas dos coeficientes e,
portanto, é importante identificar  se orientar por essa métrica . Replicamos para a base de
desenvolvimento (ou teste)  o processo de olhar para a Curva ROC e os coeficientes de ROC e Gini , isso
dá a noção comparativa entre os coefi cientes entre treino e teste , assim podemos determinar se o modelo
está generalizando bem para novos dados , além de identificar possíveis problemas de overfitting  ou
underfitting . Esses tipos de análise garantem  robustez do modelo  para explicar novos conjuntos de
dados. Por fim, olhou -se o KS das bases de treino e desenvolvimento , essa métrica entrega a noção da
capacidade que os modelos têm de diferenciar as duas classes (0 ou 1, não -inadimplente  ou
inadimplente).
Depois de garantir que o modelo está funcionando bem, chegamos ao fim para calcular o score ,
esse c álculo é baseado na probabilidade que um contrato em um mês tem de se tornar inadimplente.
Esse score  será utilizado para criar os Grupos Homogêneos (GHs).
## Resultados
Em vista disso, segue abaixo o detalhamento de cada modelo desenvolvido  com as variaveis
utilizadas,  descrição , betas e P -Valor.


## Tabela 18 - Desc rição das variáveis e efeitos na PD para Parcelados
## ID Variável Descrição Efeito Beta P-Valor Peso
1 fx_atraso_3040_num_v2_tend_0/1 Tendência da faixa de atraso no último mês +0,09276 <2e-16 5,03%
2 percentual_contrato_pago_points_manualClassificação de um menos a razão entre o saldo utilizado pelo valor original do contrato
## Faixa 1: <  45%
## Faixa 2: 45% - 90%
## Faixa 3: >= 90%-0,77770 <2e-16 10,40%
3 saldo_atraso_div_saldo_total_cliente Razão entre o saldo em atraso pelo saldo total do cliente +0,90910 <2e-16 4,79%
## 4 flag_atraso_cliente Existência de atraso do cliente +1,60300 <2e-16 32,76%
5 flag_atraso_1_361_sum_last_1_meses      Soma da existência de atraso do cliente nos últimos 361 dias observados no último mês +0,46240 <2e-16 11,75%
6 cliente_tempo_relac_meses Tempo de relacionamento do cliente em meses -0,00243 <2e-16 10,18%
7 Intercept Constante -2,44600 <2e-16 25,09%

<!-- Página 30 -->


30


Tabela 19 - Descrição  das variáveis e efeitos na PD para Consignado

## Tabela 20 - Descrição  das variáveis e efeitos na PD  para  Rotativos
Dentro das variaveis usadas no modelo c abe ressaltar a construção de algumas delas  para melhor
entendimento.  Para a variável “percentual_contrato_pago_points_manual ” é realizado primeiro o seu
cálculo  de 1- (saldo utilizado/valor original do contrato) e depois os valores desse cálculo  são divididos
em faixas. As faixas são de 1 a 3 , conforme mostrado nas tabelas acima , e são esses valores de 1 a 3 que
entra m no modelo para serem multiplicados pelo beta.  Outra variável a destacar são as variaveis de
tendencia, como a “fx_atraso_3040_num_v2_tend_0/1 ”. Essa é uma variável de tendência, ou seja,
primeiro é construída a variável “fx_atraso_3040_num_v2 ”, sua construção em detalhes está presente
no anexo . Após isso, são construídas defasagens dessa variável (lags), nesse caso é construído uma
variável de “fx_atraso_3040_num_v2_lag_1 ” que se refere ao valor da “fx_atraso_3040_num_v2 ” do
mês anterior em relação ao  atual. Na sequência , a variável “fx_atraso_3040_num_v2 ”, que se refere ao
período atual, é dividida pela variável “fx_atraso_3040_num_v2_lag_1 ” que, por consequência, terá
uma variação de 0 a 1 que será a tendência de faixa de atraso do mês atual em relação ao anterior , assim
são construídas as variaveis de tendência.
## Métricas
## ID Variável Descrição Efeito Beta P-Valor Peso
1 cliente_tempo_relac_meses Tempo de relacionamento do cliente em meses -0,00173 <2e-16 7,27%
2 ocupacao_categ Tipo de ocupação com duas categorias  pensionista e outros -0,23388 0,00130 1,54%
3 saldo_atraso_div_saldo_total_cliente Razão entre o saldo em atraso pelo saldo total do cliente +2,48952 <2e-16 8,54%
4 flag_atraso_cliente Existência de atraso do cliente acima de 5 dias +1,76909 <2e-16 35,39%
5 fx_atraso_3040_num_v2_tend_0/1 Tendência da faixa de atraso no último mês +0,21787 <2e-16 10,93%
6 percentual_contrato_pago_points_manualClassificação de um menos a razão entre o saldo utilizado pelo valor original do contrato
## Faixa 1: <  45%
## Faixa 2: 45% - 90%
## Faixa 3: >= 90%-0,34704 <2e-16 4,45%
## 7 Intercept Constante -3,28595 <2e-16 31,88%
## ID Variável Descrição Efeito Beta P-Valor Peso
1 IU_min_last_1_meses Mínimo da razão entre o saldo utilizado pelo saldo total no último mês +0,92880 <2e-16 11,84%
2 saldo_atraso_div_saldo_total_cliente Razão entre o saldo em atraso pelo saldo total do cliente +1,68400 <2e-16 7,39%
3 fx_atraso_sum_last_1_meses Soma das faixas de atraso observadas no último mês +0,03260 <2e-16 13,39%
4 saldo_div_limite_min_last_6_meses Menor razão entre o saldo utilizado pelo saldo limite observado nos últimos seis meses +0,00001 0,02960 0,67%
5percentual_contrato_pago_max_last_3_mesesMáximo percentual de contrato pago (um menos a razão do saldo utilizado pelo valor original
## do contrato) observado nos últimos três meses-3,05900 <2e-16 13,98%
6 flag_atraso_1_361_max_last_3_mesesMáximo da existência de atraso do cliente nos últimos 361 dias observados nos últimos três
## meses+1,14000 <2e-16 15,86%
7 Intercept Constante -2,30700 <2e-16 36,88%

<!-- Página 31 -->


31

Os valores apresentados abaixo  para as métricas do modelo de Parcelados  da PD 12 estão dentro
do esperado, uma vez que um valor de KS de 0, 45 para treino  e 0,37 para validação  é bastante bom e
indica que o modelo tem uma capacidade sólida de discriminação entre as classes positivas e negativas.
Já para o GINI um valor de 0, 55 e 0,59 é considerado muito bom. Em relação ao AUC , uma pontuação
de 0, 77 e 0,74 é alta e indica um bom desempenho do modelo. Sendo assim, os resultados que o modelo
de Parcelados  apresentou sugerem um desempenho sólido e capaz de separar bem as classes.


Tabela 21 – Métricas de qualidade para Parcelados

As métricas observadas para o modelo de Consignado  da PD 12 estão em linha com as
expectativas. Para o indicador KS, obtendo valores de 0, 44 e 0,32, podemos considerar que o modelo
exibe uma habilidade esperada em distinguir entre as categorias positivas e negativas. No caso do GINI,
apresentando valores de 0,4 9 e 0,38, pode -se afirmar que o desempenho é significativamente
satisfatório. No que diz respeito à métrica AUC, registrando pontuações de 0,7 4 e 0,69, demonstra um
desempenho notável do modelo.

Tabela 22 – Métricas de qualidade para Consignado

As métricas observadas para o modelo de Rotativos da PD 12 estão em linha com as
expectativas. Para o indicador KS, obtendo valores de 0, 44 e 0,39, podemos considerar que o modelo
exibe uma habilidade esperada em distinguir entre as categorias positivas e negativas. No caso do GINI,
## ETAPA KS GINI AUC
## Desenvolvimento 45% 55% 77%
## Validação 37% 49% 74%MODELO BHV PARCELADO
## ETAPA KS GINI AUC
## Desenvolvimento 44% 49% 74%
Validação 32% 38% 69%MODELO BHV CONSIGNADO

<!-- Página 32 -->


32

apresentando valores de 0, 59 e 0,47, pode -se afirmar que o desempenho é significativamente
satisfatório. No que diz respeito à métrica AUC, registrando pontuações de 0,7 8 e 0,73, demonstra um
desempenho notável do modelo.


Tabela  23 – Métricas de qualidade para  Rotativos

## 3.4 Grupos homogêneos de risco
## Dados
Para o cálculo da PD e definição de grupos homogêneos foi utilizada a mesma base de dados
que confere a adequação do para os novo s patamares de default no novo conceito 4966.
## Metodologia
Com o score marcado para o p úblico de desenvolvimento e validação do modelo marcamos o
default em 12 meses no conceito da 4966 e foi verificado se os antigos agrupamentos ainda
representam uma ordenação de  risco consistente e homogênea ao longo do tempo para os quatro
segmentos.  Caso necessário, ainda se optou  por reagrupar os GHs afim de ordenar o risco e buscar
heterogeneidade entre os grupos.
## Resultados
Após a análise e definidos os pontos de corte, cheg ou-se nas seguintes conclusões:
• Parcelados :    4 GHs definidos;
• Consignado :  4 GHs definidos;
• Rotativos :      4 GHs definidos .

## ETAPA KS GINI AUC
## Desenvolvimento 44% 56% 78%
Validação 39% 47% 73%MODELO BHV ROTATIVO

<!-- Página 33 -->


33

3.4.1.1  Parcelados

Gráfico 06 - PD para Parcelados  por GH

3.4.1.2  Consignado


Gráfico 07 - PD para Consignado  por GH


3.4.1.3  Rotativos

<!-- Página 34 -->


34


## Gráfico 08 – PD para  Rotativos  por GH
Em resumo:

Tabela 24 – PD 12 meses por GHs para Parcelados

Tabela 25 – PD 12 meses por GHs para Consignado


## GH PD ScoreMin ScoreMax
## 1 29,57% 0,00 818,58
## 2 11,12% 818,58 949,12
## 3 2,76% 949,12 987,76
## 4 0,59% 987,76 1000,00
## GH PD ScoreMin ScoreMax
## 1 18,02% 0,00 855,20
## 2 11,05% 855,21 897,16
## 3 4,09% 897,16 975,31
## 4 1,77% 975,31 1000,00
## GH PD ScoreMin ScoreMax
## 1 83,45% 0,00 267,30
## 2 39,49% 267,30 798,77
## 3 15,76% 798,77 862,46
4 8,83% 862,46 1000,00

<!-- Página 35 -->


35

## Tabela 26 – PD 12 meses por GHs  para Rotativos
## 3.5 PD Forward  Looking
## Dados
Para a construção do modelo de Forward Looking , utilizou -se bases de dados que datam de
janeiro  de 202 2 até dezembro  de 20 22. Devidos aos motivos já explicitados anteriormente, o público de
consignado  segue moldes muito restritos de contrato, vinculados a salários/benefícios/recebimentos
muito estáveis do cliente o que reduz expressivamente a correlação de risco de crédito dessas operações
com cenário macroeconômico. Dessa forma, não foi desenvolvido o  modelo de Forward Looking  para
o mesmo.  No que diz respeito as informações macroeconômicas utilizadas , foram recolhidas séries
históricas do site do BACEN. Segue abaixo as variáveis macroeconômicas consideradas :
Índice Nacional de Preços ao Consumidor (INPC);
• Índice de Preços ao Consumidor Amplo (IPCA);
• Valor do dólar na compra;
• Valor do dólar na venda;
• Taxa Selic;
• Produto Interno Bruto (PIB);
• Endividamento das famílias brasileiras com o SFN;
• Inadimplência da carteira de crédito (Total, PF e PJ);
• Taxa de desocupação – PNADC.

## Histórico
Foram utilizados dados em painel, agrupamento por Grupo Homogêneo (GH) de risco e datas
bases, e transformou -se a taxa média de inadimplência a fim de garantir que variassem de −∞ a ∞. A
metodologia de modelagem foi a Regressão Linear Múltipla para dados em painel, considerando efeito
fixo dos GHs, ou seja, garantindo patamares distintos de PD para cada grupo de risco via criação de
dummies .
Para a construção do Forward Looking  foi considerado o período da base de dados com
marcação da PD de janeiro  de 202 2 até dezembro  de 202 2. Esse período foi escolhido por apresentar
uma mais estabilidade quanto ao comportamento da PD no tempo.

<!-- Página 36 -->


36

Como havia informações da série de PD desde janeiro  de 202 2, todas as séries macroeconômicas
foram recolhidas desde janeiro de 20 21, para que fosse possível criar lags (defasagens) de até 12 meses.
## Metodologia
Os modelos vistos até aqui baseiam -se na utilização de dados históricos e toda variável relevante
na predição do risco deve ser incluída no modelo. O maior problema desses modelos é o tipo de variável
utilizada: os modelos são construídos baseados no histó rico do cliente, portanto esses modelos não
conseguem captar mudanças no cenário econômico futuro. Em outras palavras, os modelos não são
sensibilizados quando acontece alguma mudança na previsão econômica Forward Looking .
Uma forma de corrigir essa deficiência dos modelos é incluir variáveis cíclicas; por exemplo,
variáveis macroeconômicas como taxa de desemprego, inflação, endividamento, taxa de Selic, entre
outras. Também podem ser utilizadas algumas variáveis de política  de crédito, como taxa de juros
concedido e número médio de parcelas.
A norma 4966 determina que todos os modelos tenham inclusão de variáveis preditivas de
fatores macroeconômicos para proporcionar uma visão do risco à exposição dos fatores exógenos,
preparar e antecipar as instituições na avaliação de impactos em eventos e xtremos (cenários sob
estresses). Em outras palavras, as variáveis Forward Looking  funcionam como uma calibragem dos
modelos sob efeitos macroeconômicos ou política de crédito.  Nesse modelo também é adicionado a
variável WOE_score, que é log ( percentual  de contratos bons (em dia ) / percentual  de contratos em ativo
problemático)  por GH  e para estimar o impacto dessa valor sobre a PD é utilizado WOE_Score_medio ,
que é a média da PD para o período desenvolvido . Ela é usada para suavizar os efeitos de impactos no
resultado  da PE.
Para verificar quais são as variáveis macroeconômicas que influenciam na variável resposta
## basta analisar os pontos abaixo:
• Análise gráfica (conforme exemplo da figura abaixo);
• Cálculo da correlação, seja na mesma data de referência ou correlação cruzada com datas de
referência defasadas ( lags e leads ). Em algumas variáveis macroeconômicas, seu impacto na
variável resposta pode não ser direto, pode demorar algum tempo (dias, meses ou anos) para ser
observado;
• Ajuste do modelo e teste de significância estatística do efeito da variável macro na variável resposta.

<!-- Página 37 -->


37



Gráfico  09 - Exemplo de correlação da inadimplência com variável macroeconômica
Ainda buscando suprir efeitos incoerentes de movimentos de aumento e redução de risco de
crédito perante variações de cenários macroeconômicos, foi realizado uma trava de variação de PD de
até no máximo 10% maior ou maior daquela estipulada pelo modelo de FL . Os motivadores dessas
variações indesejáveis e irreais foram motivados por variações intensas dos cenários macro provocadas
entre o período de desenvolvimento e movimentos como instabilidade política, cenário internacional e
pandemia COVID -19.
Para esses modelos é aplicado um WOE  usados nas construções das regressões logísticas  e um
WOE médio usado para a construções dos fatores de impacto (k de FL) para a PE. Mais detalhes sobre
o k pode ser encontrado nos arquivos  em anexo  nos códigos da PE  em FL .
Para FL foram usados os seguintes valores:


## Tabela 27 – WOE de FL para Parcelados e Consigando
## Variável Produto GH PD 12 Valor
## Parcelados 1 -1,9190277
## Parcelados 2 -0,7001820
## Parcelados 3 0,6960377
## Parcelados 4 2,2134018
## C onsigando 1 -1,6646862
## C onsigando 2 -1,0375432
## C onsigando 3 0,0088408
C onsigando 4 0,8248193WOE_Score

<!-- Página 38 -->


38



Tabela 28 – WOE médio de FL para Parcelados e Consigando


Tabela 29 – WOE de FL para Rotativos


Tabela 30 – WOE médio de FL para Rotativo s

## Resultados
É importante destacar dois pontos: (1) que todas as macrovariáveis disponíveis foram
analisadas; (2) com o objetivo de ter modelos que não tenham grande impacto quanto a provisão final
foi considerado variaveis  com p -valor menor ou igual a 15% .
Sabe -se que todas as variáveis, exceto o PIB, devem ter correlação positiva com a PD, ou seja,
## Variável Produto GH PD 12 Valor
## Parcelados 1 0,2969
## Parcelados 2 0,1110
## Parcelados 3 0,0300
## Parcelados 4 0,0067
## C onsigando 1 0,2009
## C onsigando 2 0,1184
## C onsigando 3 0,0450
## C onsigando 4 0,0204WOE_Score_medio
## Variável Produto GH PD 12 Valor
## Rotativos 1 -2,8107972
## Rotativos 2 -0,8869402
## Rotativos 3 0,3868900
## Rotativos 4 1,0279138WOE_Score
## Variável Produto GH PD 12 Valor
## Rotativos 1 0,8140
## Rotativos 2 0,3900
## Rotativos 3 0,1517
Rotativos 4 0,0861WOE_Score_medio

<!-- Página 39 -->


39

quando a variável cresce a PD deve crescer (quando se tem uma mudança para ratings  de maior risco
tem-se uma piora de PD). Isso corrobora com o significado de cada uma delas, já que o PIB é o único
que quando cresce, deveria abaixar a Probabilidade de Default . Essas correlações são apenas um
balizador para buscar um modelo de regressão de excelência, capaz de explicar a variável resposta com
acurácia.
## 3.5.1.1  Consignado
## Entende -se que , logo, o modelo obtido após o teste de várias combinações de
variáveis explicativas segue abaixo, além de uma imagem das qualificações do modelo desenvolvidos
## em R:
## Equação desenvolvida :
𝑦=− (3.331e +00)   − (3.794e −06  ∗𝑃𝐼𝐵 𝑙𝑎𝑔11)+(3.526e −01∗𝐼𝐶𝐶 𝑙𝑒𝑎𝑑 7 )−(1.034e +00∗
𝑊𝑂 𝐸𝑠𝑐𝑜𝑟𝑒 )


Figura 03 - Parâmetros do modelo para Consignado



<!-- Página 40 -->


40

## 3.5.1.2  Parcelados
Equação desenvolvida :

𝑦=− 8,240e −01 − (3,729e −06 ∗𝑃𝐼𝐵 𝑙𝑒𝑎𝑑 2)+(3,440e −01∗𝐼𝑛𝑎𝑑 _𝑃𝐹𝑙𝑎𝑔1 )−(1,027e +00∗
𝑊𝑂 𝐸𝑠𝑐𝑜𝑟𝑒 )


Figura 04 - Parâmetros do modelo para Parcelados

## 3.5.1.3  Rotativos
A lógica para Rotativos  segue a mesma d e Parcelados , exceto para a escolha das variáveis, uma
vez que a base de dados é diferente. Coloca -se abaixo a equação do modelo e seus parâmetros:

𝑦= −1.368e +00   +(5.450e −03∗𝐼𝑉𝐺 .𝑅𝑙𝑒𝑎𝑑 1)− (−4.163e −06∗𝑃𝐼𝐵 𝑙𝑎𝑔3) −(1.020e +00
∗𝑊𝑂𝐸𝑠𝑐𝑜𝑟𝑒 )


<!-- Página 41 -->


41



Figura 05 - Parâmetros do modelo para Rotativos

## Validação
Para a validação,  os modelos  de parcelados , consignado e  rotativos , foram comparados com a
PD 12 observada neste período para cada um deles. Entende -se que os valores de GHs ficaram bem
definidos, uma vez que não existe uma inversão de PD média entre eles, ou seja, não se cruzam em
nenhum momento.
Além disso, as curvas pontilhadas referentes ao modelo Forward Looking  ficaram próximas das
curvas preenchidas que representam a PD observada, exceto em algumas faixas de risco em pontos
específicos .

<!-- Página 42 -->


42


Gráfico 10 – PD FL estimada vs observada para Rotativos

Gráfico 11 – PD FL estimada vs observada para Parcelados

<!-- Página 43 -->


43


Gráfico 12 – PD FL estimada vs observada para Consigando


## 3.6  Extrapolação PD 12 para PD vida
## Dados
Para estimar a PD vida derivamos uma relação PD vida x PD 12 dos dados observados .
## Metodologia
A partir da definição de PD 12, acumulado ponto a ponto, do prazo remanescente do contrato e
da marcação da PD vida para 24 meses, ajustou -se uma função polinomial simples de extrapolação
considerando como variável explicativa log (𝑃𝐷 12∗𝑡), onde 𝑡 é o ponto de observação acumulado.
A vantagem desta metodologia é que permite chegar em valores de PD vida para cada prazo
remanescente (𝑡) e cada PD 12 estimada .
Para rotativo s, em decorrência do seu prazo remanescente, foi considerado como a PD vida
a PD 12  para cada GH existente no modelo de score behaviour .


<!-- Página 44 -->


44

## Resultados
Para calcular o valor estimado da PD vida foi desenvolvido um modelo que relaciona a PD 12 e o
tempo a decorrer do contrato com a PD vida (curva acumulada ponto a ponto). Abaixo seguem as funções
polinomiais que levam a PD 12 à PD vida para cada segmento em cada rating (GH de risco):

## 3.6.1.1  Parcelados
## GH f(PD12,t)
## 1 - 0,0875 x3 - 0,0635 x2 + 0,2383 x + 0,1902
## 2 0,0145 x3 - 0,053 x2 + 0,1167 x + 0,1016
## 3 0,174 x4 + 0,5651 x3  + 0,7085 x2 + 0,4475 x + 0,1331
4 - 0,0078 x4 - 0,0647 x3  - 0,1778 x2 - 0,1908 x - 0,0632

## Tabela 31 - Funções PD vida  para P arcelados
## Onde PD 12 é a PD 12 do rating , sendo assim:
## 𝑡={𝑝𝑟𝑎𝑧𝑜  𝑟𝑒𝑚𝑎𝑛𝑒𝑠𝑐𝑒𝑛𝑡𝑒 ,𝑝𝑎𝑟𝑎  𝑝𝑎𝑟𝑐𝑒𝑙𝑎𝑑𝑜
## 12,   e
𝑥=log (𝑃𝐷 12×𝑡)


## 3.6.1.2  Consignado
## GH f(PD12,t)
## 1 -0,0354 x3 - 0,0072 x2 + 0,1817 x + 0,1408
## 2 0,0827 x3 - 0,0539 x2 + 0,0946 x + 0,1044
## 3 - 0,0905 x4   - 0,0948 x3   + 0,0473 x2 + 0,1359 x + 0,0767
4 - 2,2098 x4   -8,9562 x4 - 14,198 x3   - 10,931 x2 - 4,0139 x - 0,5273

## Tabela 32 - Funções PD vida  para Consignado
## Onde PD 12 é a PD 12 do rating , sendo assim:
## 𝑡={𝑝𝑟𝑎𝑧𝑜  𝑟𝑒𝑚𝑎𝑛𝑒𝑠𝑐𝑒𝑛𝑡𝑒 ,𝑝𝑎𝑟𝑎  𝑐𝑜𝑛𝑠𝑖𝑔𝑛𝑎𝑑𝑜
12   e

<!-- Página 45 -->


45

𝑥=log (𝑃𝐷 12×𝑡)


## Validação
Como validação das equações desenvolvidas, segue abaixo os gráficos que comparam a PD vida
estimada pelas equações para cada rating comparada com a PD vida, observados em 24 meses:

Gráfico 12 - Extrapolação PD vida Parcelados



<!-- Página 46 -->


46

Gráfico 13 - Extrapolação PD vida Consignado

Nota -se que a PD vida observada no eixo das abscissas nos primeiros 24 pontos (curvas
preenchidas), tanto para Parcelados  quanto para Consignado , comporta -se de forma bastante semelhante
com a PD vida estimada pelas funções (curvas pontilhadas), ou seja, justifica -se como previsão de seu
comportamento futuro.
## 3.7  Loss Given Default (LGD)
## Dados
No cálculo da LGD, o público -alvo muda, foram considerados todos os contratos que entraram
em default  de janeiro  de 2021 até dezembro de 2022 e foram  observadas suas recuperações na janela
definida .
## Premissas
O modelo de LGD foi desenvolvido em visão  de contrato .
## Metodologia
A Loss Given  Default  (LGD) é o percentual esperado de perda de um cliente dado o default . A
LGD é um componente importante para a modelagem do risco de crédito da instituição para que a
mesma consiga através de modelos mensurar qual é a probabilidade esperada de perda dada a
contratação/renovação de contratos e clientes, podendo estender anál ises específicas para os diferentes
tipos  de garantias, percentual de cobertura das garantias, entre outras informações do cliente.
A fórmula padrão para o cálculo do LGD é a seguinte, lembrando que os pagamentos e custos devem
## sempre ser trazidos a valor presente:
## 𝐿𝐺𝐷 𝑉𝑃=1−∑𝑃𝑎𝑔𝑎𝑚𝑒𝑛𝑡𝑜𝑠 𝑉𝑃−∑𝐶𝑢𝑠𝑡𝑜𝑠 𝑉𝑃
## 𝐸𝐴𝐷
Para todos os contratos a conta de pagamentos e recuperações de garantias realizadas é feit a por
diferença de saldo em aberto dos contratos a cada fechamento de mês. Todos os saldos são trazidos a
valor presente pela taxa contratual mês a mês.
Devido característica da carteira e cobrança da carteira do Banpará  e a observação de estudo de

<!-- Página 47 -->


47

estabilização de recuperações apresentado no tópico de definição de WO, busca -se todos os pagamentos
e custos de contratos problemáticos ao longo de uma janela de 30 meses.  Este período garante que
mesmo contratos que ainda não apresentam deterioração na data do primeiro default , se vierem a atrasar,
vão ser contemplados no LGD do cliente.
Após a marcação da variável resposta, foram feitos alguns testes de correlação com variáveis
explicativas existentes no Banpará . Com isso, utilizou o de árvore de decisão como metodologia de
modelo, conforme demonstrado adiante.  Agrupou -se os grupos com percentuais semelhantes ao longo
do tempo, quando as carteiras foram analisadas e separadas por variáveis explicativas que apresentaram
relação estatística com a definição de LGD.
O cálculo  de LGD também contempla uma análise de custos para a recuperação da dívida, porém
as bases enviadas não possuíam dados suficientes para que fosse implementada dentro do histórico
utilizado. Em vista disso, foi construída um a estimação de impacto no LGD ocas ionado pelos  custo s.
Para esse cálculo  foram considerados  o valor mais alto de custo de 2020  da base de SMS , uma vez que
a base possui apenas três meses disponíveis;  para a base de chamadas foi considerado o valor de R$ 200
reais  que se aproxima do valor mais alto do s dois meses  disponíveis ; e para comissão a média  dos valores
do mês 5 ao 12 de 2021 . Com base nesses valores foi estimado o custo por saldo contábil com base no
valor original dos contratos do ano de 20 20 e estimado o custo para cada grupo homogêneo desenvolvido
no estudo do LGD.  Esse valor é aplicado diretamente n a marcação do LGD, contrato a contrato para
cálculo  da perda esperada .
## Resultados
Selecionamos a segmentação mais adequada  a partir das variáveis de Faixa de Atraso , Valor
Original do Contrato , Prazo do Contrato  (medido em  dias)  e Ocupação . Com as variáveis e os
agrupamentos busca -se os comportamentos médios de LGD, que melhor segmentam o público . Para
melhor visualização os grupos foram separados em dois nos gráficos abaixo.


<!-- Página 48 -->


48


Gráfico  14 – Grupos homogêneos do LGD  de Rotativos  com atrasos até 120 dias segmentado por
valor original do contrato menores que 500 e maiores que 500




Gráfico  15 – Grupos homogêneos do LGD  de Rotativos  com atraso s entre 120 e 210
segmentado pelas mesmas feixas do valor original do contrato do grafico anterior

<!-- Página 49 -->


49


Gráfico  16 – Grupos homogêneos do LGD  de Rotativos com atraso  superior a 210


Gráfico  17 – Grupos homogêneos do LGD  de Parcelados  com atraso até 120 segmentado por
prazo contrato  maior ou igual e menor a 360


<!-- Página 50 -->


50


Gráfico  18 – Grupos homogêneos do LGD  de Parcelados com atraso s entre 120 e 210
segmentado por prazo contrato  maior ou igual e menor a 360



Gráfico  19 – Grupos homogêneos do LGD  de Parcelados com atrasos maiores que 210



<!-- Página 51 -->


51


Gráfico  20 – Grupos homogêneos do LGD  de Consignado com atrasos até 120


Gráfico  21 – Grupos homogêneos do LGD  de Consignado com atrasos entre 120 e 210
segmentado por ocupação

<!-- Página 52 -->


52


Gráfico  22 – Grupos homogêneos do LGD  de Consignado com atrasos maiores que 210
segmentado por ocupação


Dessa forma , foram definidas as regras do LGD conforme a tabela abaixo:

Tabela 33 – Regras para a con strução  do LGD

Com base no estudo relaizado anteriormento o fator aplicado de custo para o LGD ficou conforme a
tabela abaixo :

GH Tipo de Produto Faixa atraso Valor Original do Contrato Prazo Contrato Ocupação LGD
## 1 Consignado 0-120 42,51%
## 2 Consignado 120-210 Outras Ocupacões 80,02%
## 3 Consignado 120-210 Servidor Público ou Funcionário de Empresa Pública 71,85%
## 4 Consignado > 210 Outras Ocupacões 90,58%
## 5 Consignado > 210 Servidor Público ou Funcionário de Empresa Pública 88,20%
## 6 Parcelados 0-120 < 360 47,80%
## 7 Parcelados 0-120 >= 360 63,32%
## 8 Parcelados 120-210 78,91%
## 9 Parcelados > 210 90,50%
## 10 Rotativos 0-120 < 500 19,51%
## 11 Rotativos 0-120 >= 500 29,42%
## 12 Rotativos 120-210 < 500 27,31%
## 13 Rotativos 120-210 >= 500 40,52%
14 Rotativos > 210 57,20%

<!-- Página 53 -->


53


Tabela 34 – Valores de custos por GH do LGD


## 3.7.1.1  Descrição das Variávei s:
• Faixa de Atraso : Quantidade de dias em atraso ;
• Valor do Contrato : Valor do contrato original  em reais ;
•  Prazo : Duração  do contrato  em dias ;
• Ocupação : Ocupação no cliente separado entre Servidor público  ou de empresa pública e outros .

## 3.8  LGD Forward Looking
## Dados
Para a construção do modelo de LGD Forward Looking , utilizou -se bases de dados de janeiro
de 202 1 a dezembro  de 20 21, já para a base de informações macroeconômicas utilizada para os testes
com a série de LGD, foram recolhidas séries históricas do site do BACEN.  Pelos motivos já explicados
anteriormente não foi desenvolvido um modelo para consignado.

## GH LGD Fator de Custos LGD
## 1 1.007
## 2 1.007
## 3 1.005
## 4 1.005
## 5 1.005
## 6 1.006
## 7 1.006
## 8 1.009
## 9 1.007
## 10 1.005
## 11 1.005
## 12 1.007
## 13 1.007
## 14 1.007
## 15 1.007
## 16 1.007
## 17 1.007
18 1.007

<!-- Página 54 -->


54

## Metodologia
A metodologia aplicada foi a mesma utilizada para projetar a curva observada de PD, ou seja,
busca -se realizar uma regressão linear com as variáveis de Grupos Homogêneos, além das variáveis
macroeconômicas que incorporem um efeito futuro na média observada  de LGD Forward Looking .
Nesse modelo também é adicionado a variável WOE_LGD  ( que para esse caso é o mesmo que o
WOE_SCORE  apresentada nos modelos abaixo ) que segue o mesmo princípio apresentado na
explicação de Forward Looking.
Sendo assim, a fim de garantir a precisão do modelo, foram consideradas análises e a validação
das variáveis utilizadas, certificando -se de que as previsões sejam robustas e confiáveis em diferentes
cenários. Foram considerados as primícias adotadas nos modelos de Forward Looking  da PD 12 para
esse modelo respeitando as suas especificidades.
Os valores WOE utilizado foram:


Tabela 35 – WOE de FL LGD para Rotativos


## Tabela 36 – WOE médio de FL LGD para Rotativos
## Variável Produto GH LGD Valor
## Rotativos 10 0,9161298
## Rotativos 11 0,3739961
## Rotativos 12 0,4778749
## Rotativos 13 -0,1172315
## Rotativos 14 -0,7910918WOE_Score_LGD
## Variável Produto GH LGD Valor
## Rotativos 10 0,1951
## Rotativos 11 0,2942
## Rotativos 12 0,2731
## Rotativos 13 0,4052
Rotativos 14 0,5720WOE_Score_LGD_medio

<!-- Página 55 -->


55


Tabela 37 – WOE de FL LGD para Parcelados

## Tabela 38 – WOE médio de FL LGD para Parcelados
## Resultados
Foi desenvolvido dois modelos, um para parcelado e outro para rotativos . Não foi desenvolvido
um modelo específico  para consignado dado as justificativas já explicitadas anteriormente para os
contratos dessa carteira .

Modelo para parcelados :

## 𝑦=7,240e −01−( 4,426e −06∗𝑃𝐼𝐵 𝑙𝑒𝑎𝑑 7)+(9,324e −02∗𝐸𝑛𝑑𝑖𝑣 _𝑛𝑜𝑣𝑜 𝑙𝑎𝑔11)−(1.179e
## +00∗𝑊𝑂 𝐸_𝐿𝐺𝐷 𝑠𝑐𝑜𝑟𝑒 )
## Variável Produto GH LGD Valor
## Parcelados 6 0,9459423
## Parcelados 7 0,3119159
## Parcelados 8 -0,4616235
## Parcelados 9 -1,3961726WOE_Score_LGD
## Variável Produto GH LGD Valor
## Parcelados 6 0,4780
## Parcelados 7 0,6332
## Parcelados 8 0,7891
Parcelados 9 0,9050WOE_Score_LGD_medio

<!-- Página 56 -->


56


Figura 05 – Qualificações estatísticas do modelo de LGD FL  Parcelados

Modelo para rotativos:

## 𝑦=−2,645e −01  +(1,493e −01∗𝑇𝐽𝑇 𝑙𝑒𝑎𝑑 3)−(4,624e −06∗𝑃𝐼𝐵 𝑙𝑎𝑔1)−(1,182e +00
∗𝑊𝑂𝐸_𝐿𝐺𝐷 𝑠𝑐𝑜𝑟𝑒 )

<!-- Página 57 -->


57


Figura 06 – Qualificações estatísticas do modelo de LGD FL Rotativos


A validação foi realizada por meio de análise gráfica em que a simulação mostrou uma
suavização da variabilidade no tempo.


Gráfico 23 – LGD médio vs FL  LGD  para parcelados  por GH


<!-- Página 58 -->


58


Gráfico 24 – LGD médio vs FL  LGD  para parcelados por GH


Gráfico 25 – LGD médio vs FL  LGD  para parcelados por GH


<!-- Página 59 -->


59


Gráfico 26 – LGD médio vs FL  LGD  para rotativos por GH


Gráfico 27 – LGD médio vs FL  LGD  para rotativos por GH


<!-- Página 60 -->


60


Gráfico 28 – LGD médio vs FL  LGD  para rotativos por GH

Observou -se que o modelo desenvolvido apresenta uma suavização da variabilidade no tempo
quanto ao bad rating  mostrando -se aderente .

Gráfico 29 – LGD médio vs FL LGD  Parcelados


<!-- Página 61 -->


61


Gráfico 30 – LGD médio vs FL LGD  Rotativos

## 3.9  Exposure At Default (EAD)
## Dados
Para o cálculo do EAD realizamos o estudo de CCF  para contratos de produtos rotativos que
possuem limite de crédito não concedido que será definido em 3.viii.c. , e para ele, utilizamos a base
desde Jul/2020 até Jun/2022, considerando a penas  os contratos de limite .
## Premiss as
Adotamos a premissa de que o  EAD é o próprio saldo contábil para parcelados, e para contratos
rotativos,  temos: 𝐸𝐴𝐷 =𝑆𝑎𝑙𝑑𝑜  𝑢𝑡𝑖𝑙𝑖𝑧𝑎𝑑𝑜 +𝐶𝐶𝐹 ∗𝑙𝑖𝑚𝑖𝑡𝑒  𝑛ã𝑜 𝑢𝑡𝑖𝑙𝑖𝑧𝑎𝑑𝑜 . No cálculo do CCF,
utilizamos visão contrato . Neste cálculo não houve correção para valor presente  devido ao curto período
de avaliação  (apenas 12 meses) .
## Metodologia
No cálculo d a perda esperada  foi considerado, além do saldo utilizado na data base, o limite não
utilizado. Porém , como não se espera que todo o limite disponível na data de referência venha a ser

<!-- Página 62 -->


62

utilizado no futuro, foi feito um estudo para definir qual o fator de conversão (CC F) deste limite não
utilizado  em crédito.
O fator de conversão de crédito (CC F) é o percentual do limite  não utilizado  a se transformar
em uma operação de crédito, ou seja, o percentual de limite não utilizado que pode vir a ser utilizado no
futuro (neste caso, 12 meses à frente). Este cálculo é feito somente para os contratos  que ainda possuem
limites disponíveis a serem utilizados , ou seja, caso o contrato  já tenha utilizado todo o limite no mês
de referência, consideraremos todo o limite como EAD.
Vale ressaltar que o percentual de utilização de limite não é igual ao CCF, sendo o primeiro
calculado no ponto de observação considerando a amostra total de operações rotativ as e o segundo uma
“previsão” do que virá a ser utilizado nos próximos 12 meses considerando a amostra de observações
apenas a parte não utilizada dos limites rotativos. Na figura abaixo , um exemplo prático desta visão:

## Figura 07 - Ilustração construção CCF
## Para o cálculo do CCF, utiliza -se a seguinte equação:
## 𝐶𝐶𝐹 𝑖=$𝑆𝑎𝑙𝑑𝑜  𝑑𝑜 𝑙𝑖𝑚𝑖𝑡𝑒  𝑢𝑡𝑖𝑙𝑖𝑧𝑎𝑑𝑜  𝑛𝑜 𝑃𝑖−$𝑆𝑎𝑙𝑑𝑜  𝑑𝑜 𝑙𝑖𝑚𝑖𝑡𝑒  𝑢𝑡𝑖𝑙𝑖𝑧𝑎𝑑𝑜  𝑛𝑜 𝑃𝑂
## $𝑆𝑎𝑙𝑑𝑜  𝑑𝑜 𝑙𝑖𝑚𝑖𝑡𝑒  𝑵ã𝒐 𝒖𝒕𝒊𝒍𝒊𝒛𝒂𝒅𝒐  𝑛𝑜 𝑃𝑂
Sendo PO o ponto de observação e  𝑖=1,2,3,⋯ o tempo decorrido desde PO.
Se 𝐶𝐶𝐹 𝑖>1 então deve -se fixar  𝐶𝐶𝐹 𝑖=1 , isto é, para casos de utilização superior ao limite
não utilizado no ponto de observação (PO), considera -se que foi utilizado 100% do limite disponível no
PO.
Se 𝐶𝐶𝐹 𝑖<0 , então fixa -se 𝐶𝐶𝐹 𝑖=0, isto é, para casos de utilização inferior a utilização no
PO, considera -se que não foi utilizado nada do limite disponível no PO.
## Feito isto, o cálculo do CCF final é uma média dos  𝐶𝐶𝐹 𝑖
𝐶𝐶𝐹 𝑔=𝑚é𝑑𝑖𝑎𝑖=112(𝐶𝐶𝐹 𝑖)

<!-- Página 63 -->


63


## Figura 08 - Ilustração do cálculo do CCF
## Resultados
Com base na explicação do CCF acima, foram construídos os  CCFs para PF e PJ segmentados
por regra de negócios :

Tabela  39 – CCF

## 3.10 Perda Esperada
## Regras
## Para o cálculo da PE, são necessários alguns requisitos:
• Cada contrato deve ser alocado em um estágio;
## Produto Tipo Pessoa Default 12 CCF Média
## Aditamento depositante PF e PJ Sim 0,00%
## Aditamento depositante PF e PJ Não 0,02%
## Aditamento depositante PF e PJ Total 0,01%
## Produto Tipo Pessoa Default 12 CCF Média
## Cartão PF e PJ Sim 6,36%
## Cartão PF e PJ Não 7,83%
## Cartão PF e PJ Total 7,98%
## Produto Tipo Pessoa Default 12 CCF Média
## Conta garantia PF e PJ Sim 14,30%
## Conta garantia PF e PJ Não 2,31%
## Conta garantia PF e PJ Total 9,19%
## Produto Tipo Pessoa Default 12 CCF Média
## Cheque Especial PF e PJ Sim 20,58%
## Cheque Especial PF e PJ Não 6,55%
## Cheque Especial PF e PJ Total 13,76%
## 𝑪𝑪𝑭 =𝒎é𝒅𝒊𝒂
## 𝑡1
## 𝑡2
## 𝑡12
## ⋯
## 𝑡5
## 𝑡0
## 𝑡0
## 𝑡0
𝑡0

<!-- Página 64 -->


64

• Em cada estágio, para cada contrato deve ser calculado um valor de perda esperada;
• A perda esperada deve ser calculada a partir de modelos estatísticos baseados em
informações históricas e projeções futuras.

Contudo, o cálculo das perdas esperadas segue as regras de estágio, cura de estágio, PD 12, PD
Lifetime, PD Forward Looking, LGD, LGD Forward Looking, EAD, conforme descritos nos tópicos
## acima e são resumidas da seguinte forma:
## • Estágio 1:
𝑃𝐸=Mín (PD12 ,PDlt )×𝐾𝑃𝐷𝐹𝐿×𝐿𝐺𝐷 ×𝐾𝐿𝐺𝐷𝐹𝐿×𝐸𝐴𝐷

## • Estágio 2:
𝑃𝐸=PDlt ×𝐾𝑃𝐷𝐹𝐿×𝐿𝐺𝐷 ×𝐾𝐿𝐺𝐷𝐹𝐿×𝐸𝐴𝐷

• Estágio 3:                     𝑃𝐸=100% ×𝐿𝐺𝐷 ×𝐾𝐿𝐺𝐷𝐹𝐿×𝐸𝐴𝐷

Onde, K_PD_FL = PD_FL/PD12 e K_LGD_FL = LGD_FL/LGD.

No cálculo do estágio 3, é necessário atender a uma exigência normativa que compara a provisão
calculada pelo modelo com o Piso Mínimo de Perda Incorrida, conforme descrito na Resolução 352.
Nesses casos, se a provisão do Piso Mínimo for maior que a do modelo, a perda final dos contratos deve
ser substituída pela do Piso Mínimo. A seguir, é apresentada a tabela com o percentual de perda incorrida
(Piso Mínimo) para cada tipo de carteira e faixa de atraso.


<!-- Página 65 -->


65


Tabela  40: Pisos  Mínimos  Inadimplidos  por Faixa  de Atraso  no Pagamento.
## Regras Adicionais
Ainda a 4966 explora alguns conceitos adicionais objetivos que devemos acrescentar no
## cálculo:
• Toda a Reestruturação de Contratos em Prejuízo deve ser alocada inicialmente com
100% de provisão .
• Foi utilizado a definição de níveis mínimos de provisionamento da resolução 309, logo
caso um contrato em inadimplência e estágio 3 possuir um nível de provisionamento menor
que mínimo, da classificação de carteira, será utilizado o “piso”. Segundo a norma , para
## cada tipo de produto no estágio 3 o provisionamento mínimo deve ter pisos de
provisionamento diferentes de acordo com a carteira que o produto pertence.
•   Como facultativo pela resolução 4966, admite -se regra de cura para que o contrato de
reestruturação de prejuízo saia de uma alocação de 100% e volte ao patamar de provisão de
estágio 3. Toda a Reestruturação de Contratos em Prejuízo que tenha mais de 30% d e
amortização retorna ao patamar de estágio 3.

<!-- Página 66 -->


66


Para a construção do provisionamento mínimo foi considerado os produtos com base na
modalidade de cada operação e realizado a classificação quanto a sua carteira conforme as tabelas
abaixo :


Tabela 41 – Classificação para produtos com Garantia

<!-- Página 67 -->


67


Tabela 42 – Classificação para produtos sem Garantia


São realizadas algumas considerações mais técnicas para a implementação do cálculo. Segue as
considerações:

Para a PD são feitas as considerações:

• Se o contrato está nos estágios 1 ou 2 e é um contrato de concessão de crédito , a
probabilidade de inadimplência é ajustada para o valor da PD concessão  de 12 meses .
• Se o contrato está no estágio 1 e a PD de longo prazo  (PD LT)  é menor que a PD de 12
meses, a PD final é ajustada como PD LT.
• Se a PD LT for maior ou igual à PD de 12 meses, a PD de 12 meses é utilizada no
cálculo.
• Para contratos no segundo estágio 2, é usada a PD LT.
## • Se o contrato está no terceiro estágio  3, é assumido um risco máximo, com a
probabilidade de inadimplência definida como 100%.

## Cálculo da Perda Esperada Ajustada:
## Modalidade.Operação Carteira Modalidade.Operação Descrição
## 101 C5  Adiantamento a depositantes - adiantamento a depositantes
## 301 C3  Direitos creditórios descontados - desconto de duplicatas
## 215 C4  Empréstimos - capital de giro com prazo de vencimento até 365 dias
## 215 C4  Empréstimos - capital de giro com prazo de vencimento até 365 dias
216 C4  Empréstimos - capital de giro com prazo de vencimento superior a 365 dias
216 C4  Empréstimos - capital de giro com prazo de vencimento superior a 365 dias
## 202 C5  Empréstimos - crédito pessoal - com consignação em folha de pagamento
## 203 C5  Empréstimos - crédito pessoal - sem consignação em folha de pagamento
## 203 C5  Empréstimos - crédito pessoal - sem consignação em folha de pagamento
## 204 C5  Empréstimos - crédito rotativo vinculado a cartão de crédito
210 C5  Empréstimos - cartão de crédito – compra, fatura parcelada ou saque financiado pela instituição
## 213 C5  Empréstimos - cheque especial
## 213 C5  Empréstimos - cheque especial
## 214 C5  Empréstimos - conta garantida
## 218 C5  Empréstimos - cartão de crédito - não migrado
## 299 C5  Empréstimos - outros empréstimos
## 299 C5  Empréstimos - outros empréstimos
## 499 C5  Financiamento - outros financiamentos
## 503 C4  Financiamento à Exportação - adiantamento sobre cambiais entregues
## 502 C4  Financiamento à Exportação - adiantamento sobre contratos de câmbio
## 502 C4  Financiamento à Exportação - adiantamento sobre contratos de câmbio
701 C5  Financimento com interveniência - aquisição de bens com interveniência - veículos automotores
702 C5  Financimento com interveniência - aquisição de bens com interveniência - outros bens
702 C5  Financimento com interveniência - aquisição de bens com interveniência - outros bens
## 801 C4  Financiamentos rurais - Custeio
## 802 C4  Financiamentos rurais - Investimento
## 790 C5  Financimento com interveniência - financiamento de projeto
## 790 C5  Financimento com interveniência - financiamento de projeto
## 901 C5  Financiamento imobiliário - financiamento habitacional - SFH
## 902 C5  Financiamento imobiliário - financiamento habitacional - Exceto SFH
903 C5  Financiamento imobiliário - financiamento imobiliário - empreendimentos, exceto habitacional
1304 C5  Outros créditos - cartão de crédito - compra à vista e parcelado lojista

<!-- Página 68 -->


68

• Se o contrato está no terceiro estágio de recuperação, a PE é calculada não considera o
impacto do modelo de FL PD, apenas FL LGD

## Ajuste para Contratos originário de prejuízo :
• Se um contrato foi originário de um contrato em prejuízo  e seu saldo devedor representa
mais de 50% do valor original, assume -se um risco total, com a perda sendo equivalente
ao saldo devedor.
• Para contratos renegociados com menor exposição e sem atraso, a PE é calculada
usando a abordagem padrão.
## Definição do Piso Mínimo da Perda Esperada:
• Para contratos em estágio 3, se houver uma provisão mínima definida, essa provisão é
multiplicada pelo saldo devedor para obter a perda mínima esperada.
• Para os demais contratos, esse valor é considerado como zero.
• A PE final é ajustada para garantir que nunca fique abaixo da perda mínima estabelecida
para contratos no terceiro estágio de recuperação.

## Resultados
Após o desenvolvimento de modelos para PD e LGD e, também, da especificação da definição
do EAD, efetuou -se o cálculo da Perda Esperada para o mês base de dezembro  de 202 3. Segue abaixo
a tabela de referência:

Tabela 43 - Perda Esperada total para  dezembro  de 202 3


## Tabela 44 - Divisão da Perda Esperada para Consignado  em dezembro  de 202 3
## Estágio Saldo Contábil/EAD PE PE  COM PISO MÍNIMO % PE
1 12.340.515.282,23 R$             210.763.272,76 R$                   210.763.272,76 R$                       1,71%
2 339.382.151,10 R$                   35.340.223,10 R$                     35.340.223,10 R$                         10,41%
3 269.453.798,69 R$                   182.916.658,10 R$                   183.782.686,90 R$                       68,21%
Total Geral 12.949.351.232,02 R$            429.020.153,96 R$                  429.886.182,75 R$                       3,32%
## Estágio Saldo Contábil/EAD PE PE  COM PISO MÍNIMO % PE
1 9.693.947.038,33 R$               140.461.467,58 R$                   140.461.467,58 R$                       1,45%
2 41.654.641,30 R$                     3.307.463,92 R$                       3.307.463,92 R$                            7,94%
3 102.367.990,57 R$                   69.865.499,70 R$                     70.032.206,03 R$                         68,41%
Total Geral 9.837.969.670,20 R$               213.634.431,20 R$                  213.801.137,54 R$                       2,17%

<!-- Página 69 -->


69



Tabela 45 - Divisão da Perda Esperada para Parcelados  em dezembro  de 202 3


Tabela 46 - Divisão da Perda Esperada para Rotativos  em dezembro  de 202 3




Para a PE de 06/2024 foram observados os seguintes resultados:


Tabela 47 - Perda Esperada total para  junho  de 202 4


Tabela 48 - Divisão da Perda Esperada para Consignado  em junho  de 202 4

## Estágio Saldo Contábil/EAD PE PE  COM PISO MÍNIMO % PE
1 2.591.245.493,27 R$               68.393.360,19 R$                     68.393.360,19 R$                         2,64%
2 193.690.983,38 R$                   25.156.366,97 R$                     25.156.366,97 R$                         12,99%
3 127.733.997,28 R$                   96.480.767,18 R$                     96.518.103,82 R$                         75,56%
Total Geral 2.912.670.473,93 R$               190.030.494,34 R$                  190.067.830,99 R$                       6,53%
## Estágio Saldo Contábil/EAD PE PE  COM PISO MÍNIMO % PE
1 55.322.750,63 R$                     1.908.444,99 R$                       1.908.444,99 R$                            3,45%
2 104.036.526,42 R$                   6.876.392,20 R$                       6.876.392,20 R$                            6,61%
3 39.351.810,84 R$                     16.570.391,23 R$                     17.232.377,04 R$                         43,79%
Total Geral 198.711.087,89 R$                  25.355.228,42 R$                     26.017.214,23 R$                         13,09%
## Estágio Saldo Contábil/EAD PE PE COM PISO MÍNIMO % PE
1 13.261.936.671,01 R$             204.881.776,08 R$                   204.881.776,08 R$                   1,54%
2 306.844.732,68 R$                   30.612.986,85 R$                     30.612.986,85 R$                     9,98%
3 282.693.802,68 R$                   196.306.487,54 R$                   197.244.766,70 R$                   69,77%
Total Geral 13.851.475.206,37 R$             431.801.250,48 R$                   432.739.529,63 R$                   3,12%
## Estágio Saldo Contábil/EAD PE PE COM PISO MÍNIMO % PE
1 10.197.623.757,95 R$             124.515.202,85 R$                   124.515.202,85 R$                   1,22%
2 47.838.165,15 R$                     3.415.395,59 R$                        3.415.395,59 R$                        7,14%
3 109.138.724,25 R$                   78.031.871,09 R$                     78.228.819,19 R$                     71,68%
Total Geral 10.354.600.647,35 R$             205.962.469,53 R$                   206.159.417,64 R$                   1,99%

<!-- Página 70 -->


70


Tabela 49 - Divisão da Perda Esperada para Parcelados  em junho  de 2024


Tabela 50 - Divisão da Perda Esperada para Rotativos  em junho  de 202 4

## Onde:
PE (Perda Total na Visão 4966): Essa métrica se refere à perda total de acordo com as diretrizes
estabelecidas na Resolução CMN n° 4.966. Define -se critérios ou padrões específicos para calcular a
perda total em um determinado contexto financeiro ou regulató rio;
PE COM PISO MÍNIMO  (Perda Total na Visão 4966 com Provisão Mínima):  Essa métrica se refere
à perda total de acordo com as diretrizes estabelecidas na Resolução CMN n° 4.966 utilizando um valor
de provisão mínimo para contratos do estágio 3.
Saldo Contábil : Refere -se aos valores e montantes financeiros relacionados a contas ou transações
específicas, de acordo com os critérios estabelecidos na Resolução CMN n° 4.966.
Saldo Contábil /EAD : Refere -se aos valores do saldo contábil mais o limite não utilizado .
4. Anexos

## Estágio Saldo Contábil/EAD PE PE COM PISO MÍNIMO % PE
1 3.012.603.640,22 R$               78.799.705,96 R$                     78.799.705,96 R$                     2,62%
2 153.334.719,98 R$                   21.173.503,28 R$                     21.173.503,28 R$                     13,81%
3 134.332.592,14 R$                   101.929.622,53 R$                   101.961.289,86 R$                   75,90%
Total Geral 3.300.270.952,34 R$               201.902.831,78 R$                   201.934.499,10 R$                   6,12%
## Estágio Saldo Contábil/EAD PE PE COM PISO MÍNIMO % PE
1 51.709.272,84 R$                     1.566.867,27 R$                        1.566.867,27 R$                        3,03%
2 105.671.847,55 R$                   6.024.087,98 R$                        6.024.087,98 R$                        5,70%
3 39.222.486,29 R$                     16.344.993,92 R$                     17.054.657,65 R$                     43,48%
Total Geral 196.603.606,68 R$                   23.935.949,17 R$                     24.645.612,89 R$                     12,54%