<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Estou pesquisando sobre ECL e a resolução BACEN 4966/2021 e estou desenvolvendo um sistema para o banco calcular a ECL para enviar ao banco, mas preciso saber qual é o formato dos dados, quais dados e como deve ser enviado essas informações de ECL para o BACEN. Faça uma pesquisa e me informe os resultados pois preciso adequar o meu sistema para enviar os dados do jeito que o BACEN quer recebê-los.

Perfeito! Agora vou gerar um relatório executivo completo para o usuário com todas as informações pesquisadas.

## Relatório Técnico: ECL e Resolução BACEN 4966/2021 – Formato e Envio de Dados para o BACEN

A Resolução CMN 4966/2021, em vigor desde 01 de janeiro de 2025, estabelece novos padrões para o cálculo e envio de informações sobre perdas esperadas de crédito (Expected Credit Loss – ECL) ao Banco Central do Brasil. Este relatório detalha o formato técnico dos dados, a estrutura de transmissão e os requisitos de conformidade que seu sistema deve atender.

### 1. Documento Obrigatório e Data-Base

O envio de dados ECL é realizado exclusivamente por meio do **Documento 3040 (Dados de Risco de Crédito)** do Sistema de Informações de Crédito (SCR). Os dados devem ser remetidos mensalmente até o **9º dia útil do mês seguinte**, com data-base no último dia do mês de referência. A seção específica para ECL, denominada **ContInstFinRes4966**, tornou-se obrigatória a partir da data-base de janeiro de 2025, conforme a Instrução Normativa BCB 414.[^1][^2][^3]

### 2. Formato Técnico dos Dados

#### Estrutura XML e Codificação

O arquivo deve ser estruturado em **XML (eXtensible Markup Language)** com as seguintes características:

- **Versão XML**: 1.0
- **Codificação**: UTF-8
- **Compactação**: Arquivo .ZIP para envio
- **Particionamento**: Permitido para instituições com alto volume de dados

O cabeçalho do documento obedece ao seguinte padrão:[^3]

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Doc3040 
  CNPJ="XXXXXXXX"
  DtBase="AAAA-MM"
  Remessa="R"
  Parte="P"
  TpArq="F"
  NomeResp="Nome do Responsável"
  EmailResp="email@instituicao.com"
  TelResp="DDNNNNNNNN"
  TotalCli="Número de clientes"
  MetodApPE="C ou S"
  MetodDifTJE="S ou N">
```

Onde:

- **CNPJ**: Identificador de 8 dígitos da instituição remetente
- **DtBase**: Período de referência (formato AAAA-MM)
- **Remessa**: Número sequencial de envios para mesma data-base
- **MetodApPE**: Metodologia de apuração de perdas esperadas ("C" = Completa, "S" = Simplificada)
- **MetodDifTJE**: Indicador de metodologia diferenciada para taxa de juros efetiva


### 3. Campos Obrigatórios para ECL (Tag ContInstFinRes4966)

```
A partir de janeiro de 2025, a tag `<ContInstFinRes4966>` substitui a anterior `<ContInstFin>` e deve conter os seguintes campos:[^1][^3]
```

| **Campo** | **Descrição** | **Formato** | **Obrigatoriedade** |
| :-- | :-- | :-- | :-- |
| **ClassificacaoAtivoFinanceiro** | Categoria contábil | 1=Custo amortizado, 2=VJORA, 3=VJR | Sim |
| **EstagioDo** | Estágio do instrumento | 1, 2 ou 3 | Sim (metodologia C) |
| **QtdTitulos** | Quantidade de títulos | Inteiro positivo | Sim |
| **VlrContabilBruto** | Valor bruto antes da provisão | Decimal (2 casas) | Sim |
| **VlrPerdaAcumulada** | Provisão para perdas esperadas | Decimal (2 casas) | Sim |
| **VlrJusto** | Valor justo do instrumento | Decimal (2 casas) | Conforme classificação |
| **TaxaJurosEfetiva** | Taxa de juros efetiva anual | Percentual | Sim |
| **RendaMes** | Rendas do mês corrente | Decimal (2 casas) | Sim |
| **AlocacaoEstag1** | Tipo de PD utilizada (Estágio 1) | Código 01-09 | Conforme modelo |
| **CarteiraProvisaoMin** | Carteira para provisão mínima | C1, C2, C3, C4, C5 | Sim |
| **TratRiscoCredito** | Tratamento do risco de crédito | Código numérico | Sim |

#### Elementos Aninhados: Estágio e Perdas

A tag `<ContInstFinRes4966>` deve conter elementos adicionais para detalhar estágios e perdas:[^4][^5]

```xml
<ContInstFinRes4966 ClassificacaoAtivoFinanceiro="1" 
                    EstagioDo="1" 
                    VlrContabilBruto="100000.00"
                    VlrPerdaAcumulada="5000.00"
                    ... atributos adicionais>
  
  <!-- Informação de Estágio (vigência jan/2026) -->
  <Estagio MotivoAlocacao="01" 
           DataBaseAlocacao="2025-01-31"/>
  
  <!-- Informação de Perdas Reconhecidas -->
  <Perda MotivoDaPerda="1" 
         VlrPerda="2500.00"/>
</ContInstFinRes4966>
```

**Motivos de Alocação em Estágios (Anexo 42 do Leiaute)**:[^1]

- **1**: Risco de crédito não aumentou significativamente (Estágio 1)
- **2**: Aumento significativo do risco de crédito (Estágio 2) – redução de rating, deterioração de score, atrasos anormais
- **3**: Deterioração creditícia ou inadimplência (Estágio 3)

**Motivos de Perda (Anexo 44)**:[^1]

- **1**: Reestruturação de operação
- **2**: Abatimento/concessão
- **3**: Outro motivo de reconhecimento de perda


### 4. Cálculo da ECL e Componentes (PD, LGD, EAD)

Embora o BACEN não exija o envio dos componentes individuais (PD, LGD, EAD), o valor de **VlrPerdaAcumulada** deve ser resultado do seguinte cálculo:[^6][^7][^8]

**ECL = PD × LGD × EAD**

Onde:

- **PD (Probabilidade de Default)**: Probabilidade de o devedor não cumprir obrigações no horizonte de tempo relevante. Para Estágio 1: 12 meses. Para Estágios 2 e 3: lifetime (vida útil do instrumento)
- **LGD (Perda em caso de Default)**: Percentual da exposição não recuperado quando ocorre inadimplência (considera garantias e colaterais)
- **EAD (Exposição no Momento do Default)**: Valor total a receber do devedor, incluindo saldo devedor, juros a vencer, encargos contratuais e linhas rotativas potencialmente utilizáveis

Para fins de conformidade regulatória, a instituição deve manter documentação detalhada sobre a metodologia interna de cálculo destes parâmetros, pois o BACEN pode solicitá-la durante supervisão.[^9][^10]

### 5. Método de Transmissão para o BACEN

#### 5.1 Sistema de Transferência de Arquivos (STA)

O envio do Documento 3040 é feito **exclusivamente** via **STA (Sistema de Transferência de Arquivos)**, conforme estabelecido na Carta-Circular BACEN 3.588/2013.[^11][^2]

**Plataforma de acesso**: http://www.bcb.gov.br/Adm/STA/

**Requisitos de acesso Sisbacen**:

1. Usuário master da instituição cadastrado no Sisbacen
2. Transação **PSTA300** (STA) habilitada
3. Serviços **SSCR301** (transmissão) e **SSCR355** (recebimento) habilitados
4. Credenciais de segurança ativos (login e senha)

#### 5.2 Procedimento Técnico de Envio

O fluxo completo de envio segue os seguintes passos:[^12][^2][^13][^11]

**Passo 1: Geração do Arquivo XML**

- Estruturar dados conforme leiaute SCR3040_Leiaute.xls
- Incluir seção ContInstFinRes4966 com valores de ECL
- Respeitar todas as regras de preenchimento (datas em AAAA-MM-DD, decimais com 2 casas, etc.)

**Passo 2: Validação com Aplicativo Validador**

- Baixar ferramenta **validador.exe** em: https://www.bcb.gov.br/estabilidadefinanceira/validador_xml_info
- Obter arquivo **XSD (XML Schema Definition)** correspondente ao documento 3040
- Executar validação: selecionar arquivo XML e arquivo XSD, clicar em "Executar Validação"
- Verificar resultado: mensagem "Processado com Sucesso" em verde (canto inferior esquerdo)
- Localizar arquivo compactado gerado automaticamente (.ZIP) na mesma pasta[^13]

**Passo 3: Compactação**

- Arquivo .ZIP é gerado automaticamente pelo validador
- Alternativamente, compactar manualmente se necessário
- Tamanho máximo: respeitar limites de envio do STA (verificar manual STA Web)

**Passo 4: Acesso ao STA Web**

- Acessar: http://www.bcb.gov.br/Adm/STA/
- Fazer login com credenciais Sisbacen
- Selecionar ambiente: **Homologação** (testes) ou **Produção** (envios reais)
- Menu: Transmissão → Nova Transmissão

**Passo 5: Preenchimento de Metadados**

- **Código do Documento**: ASCR342 (Sistema de Informações de Crédito – Documento 3040)
- **Remetente**: CNPJ da instituição (preenchido automaticamente)
- **Data-Base**: Período de referência dos dados (AAAA-MM)
- **Selecionar arquivo**: Fazer upload do arquivo .ZIP validado

**Passo 6: Submissão e Protocolo**

- Clicar em "Transmitir" ou "Enviar"
- Sistema gera **protocolo de transmissão** (número único)
- Guardar protocolo para rastreamento
- Acesso a consultas de status em "Acompanhamento de Transmissões"

**Passo 7: Monitoramento de Status**
O arquivo passa pelos seguintes estados:[^2]


| **Status** | **Significado** | **Ação Necessária** |
| :-- | :-- | :-- |
| **PROCESSANDO** | Arquivo em análise pelo BACEN | Aguardar conclusão |
| **SUCESSO** | Arquivo aceito e carregado no SCR | Nenhuma |
| **ERRO** | Falha na validação ou processamento | Corrigir e reenviar com nova remessa |
| **REJEITADO** | Arquivo não atende critérios | Revisar leiaute e dados |

### 6. Validação e Regras de Qualidade

#### 6.1 Validação Sintática

O validador XML verifica:[^13]

- Estrutura bem-formada do XML
- Conformidade com schema XSD
- Tipos de dados corretos (numéricos, datas, etc.)
- Comprimento de campos dentro dos limites
- Atributos obrigatórios presentes


#### 6.2 Validação Semântica (Críticas BACEN)

Além da sintaxe, o BACEN aplica regras semânticas por meio da planilha **SCR3040_Criticas.xls**, que incluem:[^14][^13]

- **Coerência entre campos**: VlrContabilBruto ≥ VlrPerdaAcumulada
- **Compatibilidade de estágio**: Estágio coerente com classificação de risco do cliente
- **Unicidade do IPOC**: Cada operação deve ter IPOC único (não repetir)
- **Responsabilidade total**: Soma de operações ≥ R\$ 200,00 para dados individualizados
- **Consistência com COSIF**: Valor contábil deve bater com contabilidade (Plano de Contas COSIF)
- **Datas válidas**: Datas de contratação ≤ datas de vencimento
- **Batimento modalidade**: Valores por modalidade devem reconciliar com saldos contábeis[^14]


#### 6.3 Particionamento de Arquivos

Para instituições com grande volume de dados, o arquivo pode ser dividido em múltiplas partes:[^12]

```xml
<!-- Primeira parte da primeira remessa -->
<Doc3040 CNPJ="12345678" DtBase="2025-01" Remessa="1" Parte="1" TpArq="">
  <!-- Dados do cliente 1 a 500 -->
</Doc3040>

<!-- Segunda parte da primeira remessa -->
<Doc3040 CNPJ="12345678" DtBase="2025-01" Remessa="1" Parte="2" TpArq="">
  <!-- Dados do cliente 501 a 1000 -->
</Doc3040>

<!-- Última parte (indicada por TpArq="F") -->
<Doc3040 CNPJ="12345678" DtBase="2025-01" Remessa="1" Parte="3" TpArq="F">
  <!-- Dados do cliente 1001 a N -->
</Doc3040>
```

**Regra**: Apenas a última parte deve ter atributo `TpArq="F"`. As partes anteriores omitem este atributo.

### 7. Exemplo Prático Completo

Abaixo, um exemplo de arquivo 3040 com ECL para uma operação em Estágio 2:[^15]

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Doc3040 
  CNPJ="12345678" 
  DtBase="2025-01" 
  Remessa="1" 
  Parte="1" 
  TpArq="F"
  NomeResp="João da Silva" 
  EmailResp="joao.silva@banco.com" 
  TelResp="1133334444"
  TotalCli="2"
  MetodApPE="C"
  MetodDifTJE="N">
  
  <!-- Cliente 1: Pessoa Jurídica -->
  <Cli Tp="2" Cd="00038166" Autorzc="S" PorteCli="1" TpCtrl="01" 
       IniRelactCli="2020-01-15" CongEcon="000000">
    
    <!-- Operação 1: Financiamento Estágio 2 -->
    <Op DetCli="00038166000101" 
        Contrt="FIN2024001" 
        NatuOp="01" 
        Mod="0401" 
        OrigemRec="0101" 
        Indx="01" 
        VarCamb="978"
        DtVencOp="2027-01-31" 
        CEP="01310100" 
        TaxEft="12.50" 
        DtContr="2023-01-15"
        ProvConsttd="8500.00" 
        Cosif="1.6.2.10.01.10-2" 
        IPOC="123456780401200038166FIN2024001">
      
      <!-- Vencimentos -->
      <Venc v110="25000.00" v120="25000.00" v130="25000.00" v140="25000.00"/>
      
      <!-- Contabilização ECL (Nova - Jan/2025) -->
      <ContInstFinRes4966
        ClassificacaoAtivoFinanceiro="1"
        EstagioDo="2"
        QtdTitulos="1"
        VlrContabilBruto="100000.00"
        VlrPerdaAcumulada="8500.00"
        VlrJusto="91500.00"
        TaxaJurosEfetiva="12.50"
        RendaMes="1041.67"
        AlocacaoEstag1="05"
        CarteiraProvisaoMin="C2"
        TratRiscoCredito="01">
        
        <!-- Detalhamento Estágio (vigência jan/26) -->
        <Estagio MotivoAlocacao="02" DataBaseAlocacao="2024-11-30"/>
        
        <!-- Perda Reconhecida -->
        <Perda MotivoDaPerda="1" VlrPerda="4250.00"/>
      </ContInstFinRes4966>
    </Op>
  </Cli>
  
  <!-- Cliente 2: Pessoa Física -->
  <Cli Tp="1" Cd="12345678901" Autorzc="N" PorteCli="3" TpCtrl="01"
       IniRelactCli="2021-06-01" FatAnual="96000.00">
    
    <!-- Operação 2: Crédito Pessoal Estágio 1 -->
    <Op DetCli="12345678901" 
        Contrt="CRED20240045"
        NatuOp="01"
        Mod="0203"
        OrigemRec="0101"
        Indx="01"
        VarCamb="978"
        DtVencOp="2026-12-31"
        CEP="01310100"
        TaxEft="18.75"
        DtContr="2024-01-15"
        ProvConsttd="625.00"
        Cosif="1.6.1.20.01.10-4"
        IPOC="123456780203112345678901CRED20240045">
      
      <!-- Vencimentos -->
      <Venc v20="3125.00" v40="3125.00" v60="3125.00" v80="3125.00" 
            v110="3125.00" v120="3125.00" v130="3125.00" v140="3125.00"/>
      
      <!-- Contabilização ECL -->
      <ContInstFinRes4966
        ClassificacaoAtivoFinanceiro="1"
        EstagioDo="1"
        QtdTitulos="1"
        VlrContabilBruto="25000.00"
        VlrPerdaAcumulada="625.00"
        VlrJusto="24375.00"
        TaxaJurosEfetiva="18.75"
        RendaMes="390.63"
        AlocacaoEstag1="01"
        CarteiraProvisaoMin="C1"
        TratRiscoCredito="01">
        
        <Estagio MotivoAlocacao="01" DataBaseAlocacao="2025-01-31"/>
      </ContInstFinRes4966>
    </Op>
  </Cli>
</Doc3040>
```


### 8. Cronograma de Implementação e Requisitos Adicionais

**Data-base**: Janeiro 2025
**Seções ativas**:

- ContInstFinRes4966: Obrigatória
- ContInstFin (antiga): Descontinuada
- ClassCli, ClassOp (antigas): Descontinuadas

**Motivos de alocação em estágios** (Arts. 37-39 da Res. 4.966): Vigência a partir de janeiro 2026.[^1]

Até então, informar apenas estágio, sem detalhamento do motivo.

### 9. Recomendações para Adequação de Sistema

Para atender aos requisitos técnicos da Resolução 4966/2021, recomenda-se:

1. **Integração com Contabilidade (COSIF)**: Automatizar reconciliação de saldos contábeis com valores reportados em VlrContabilBruto
2. **Modelos de Risco**: Implementar cálculo de PD, LGD, EAD com documentação interna de metodologias
3. **Alocação de Estágios**: Definir regras objetivas de SICR (aumento significativo de risco de crédito) conforme Art. 37 da Resolução
4. **Validação Integrada**: Incorporar validador BACEN em pipeline de processamento antes de STA
5. **Particionamento**: Implementar quebra automática de arquivos para grandes volumes (>10.000 operações)
6. **Rastreabilidade**: Manter logs de cada remessa, protocolo e status de processamento
7. **Testes em Homologação**: Executar testes completos antes do primeiro envio em produção
8. **Auditoria e Conformidade**: Documentar metodologias de ECL para fiscalização regulatória

### Conclusão

O envio de dados ECL para o BACEN conforme a Resolução 4966/2021 exige conformidade técnica rigorosa com o formato XML, validação obrigatória via STA e reconciliação contábil precisas. A implementação de um sistema robusto, integrado à contabilidade e com controles de qualidade, é essencial para garantir a conformidade regulatória e evitar rejeições de arquivos. As datas-base a partir de janeiro de 2025 marca o início desta nova era de reporte de perdas esperadas, substituindo o modelo anterior baseado em perdas incorridas.

***

**Referências**,  ,  ,  ,  ,  ,  ,  ,  ,  ,  ,  ,  ,  ,  ,  [^7][^16][^8][^10][^5][^9][^6][^11][^2][^3][^4][^15][^12][^13][^14][^1]
<span style="display:none">[^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79]</span>

<div align="center">⁂</div>

[^1]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_Leiaute.xls

[^2]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/ManualEnvio3040.pdf

[^3]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR_InstrucoesDePreenchimento_Doc3040.pdf

[^4]: https://repositorio.cgu.gov.br/bitstream/1/77524/5/Decisao_333_2023_julgamento_Pedrasul.pdf

[^5]: https://www.editoraroncarati.com.br/v2/Diario-Oficial/Diario-Oficial/INSTRUCAO-NORMATIVA-BCB-Nº-414-DE-16-10-2023.html

[^6]: https://okai.com.br/blog/o-impacto-da-resolucao-cmn-4966-na-utilizacao-do-raroc-para-concessao-de-credito

[^7]: https://pt.linkedin.com/pulse/o-impacto-da-resolução-cmn-4966-na-utilização-do-raroc-lobo-k7ucf

[^8]: https://profamr.app/indicacao-de-artigo-cessao-de-credito-e-res-cmn-4966/

[^9]: https://www.pwc.com.br/pt/setores-de-atividade/financeiro/2023/resolucao-4966_23-VF-15-12.pdf

[^10]: https://lume.ufrgs.br/bitstream/handle/10183/279245/001211210.pdf?sequence=1\&isAllowed=y

[^11]: https://okai.com.br/blog/guia-completo-resolucao-bcb-n-4292024-objetivos-e-impactos-nos-cadocs

[^12]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/ManualParticionamento.pdf

[^13]: https://www.bcb.gov.br/content/estabilidadefinanceira/leiaute_de_documentos/scrdoc3040/manualvalidador3040.pdf

[^14]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_RegrasValidacaoBacen.xls

[^15]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/exemploDocPadraoInfosBasicas.xml

[^16]: https://cashway.io/resolucao-cmn-4966/

[^17]: https://www.pwc.com.br/pt/sala-de-imprensa/artigo/as-novas-exigencias-da-resolucao-cmn-n-4966-21-para-as-instituicoes-financeiras.html

[^18]: https://dimensa.com/blog/resolucao-4966/

[^19]: https://www.youtube.com/watch?v=30qyFUjz31U

[^20]: https://kpmg.com/in/en/insights/2025/01/expected-credit-loss-ecl.html

[^21]: https://www.deloitte.com/br/pt/services/audit-assurance/analysis/resolucao-4966-beneficios-industria-financeira-valorizacao-profissionais.html

[^22]: https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolução+CMN\&numero=4966

[^23]: https://www.bis.org/bcbs/publ/d311.pdf

[^24]: https://www.fbmeducacao.com.br/artigos/desafios-resolucao-4966-sociedades-credito-direto/

[^25]: https://assets.kpmg.com/content/dam/kpmg/br/pdf/2024/01/Harmonizacao-IFRS-9-Instituicoes-Financeiras-Brasil.pdf

[^26]: https://www.federalreserve.gov/econres/feds/files/2023063pap.pdf

[^27]: https://www.topazevolution.com/blog/resolucao-4966-regulamentacao-contabil-para-a-transparencia-e-confiabilidade-financeira

[^28]: https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?conteudo=cosif\&tipoDocumento=Resolução+CMN

[^29]: https://www.esrb.europa.eu/pub/pdf/reports/esrb.report190116_expectedcreditlossapproachesEuropeUS.en.pdf

[^30]: https://www.deloitte.com/br/pt/services/audit-assurance/perspectives/resolucao-cmn-4966.html

[^31]: https://www.fdic.gov/accounting/current-expected-credit-losses-cecl

[^32]: https://itera.com.br/blog/resolucao-4966-gestao-riscos

[^33]: https://www.afeam.am.gov.br/scr/

[^34]: https://www3.bcb.gov.br/ifdata/

[^35]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_Manual_de_Consulta_Web_Service.pdf

[^36]: https://www.bcb.gov.br/acessoinformacao/sistematransferenciaarquivos

[^37]: https://www.youtube.com/watch?v=lboErNcYEVA

[^38]: https://pic.bankofchina.com/bocappd/brazil/202211/P020221123842336999875.pdf

[^39]: https://www.bcb.gov.br/meubc/relatoriocontasrelacionamentos

[^40]: https://www.gov.br/pt-br/servicos/obter-relatorio-do-sistema-de-informacoes-de-credito-scr

[^41]: https://www.bcb.gov.br/estabilidadefinanceira/instituicaopagamento

[^42]: https://www.youtube.com/watch?v=raPmAwixHCU

[^43]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/Manual_SubstituicaoParcial_3042.pdf

[^44]: https://www.bcb.gov.br/estabilidadefinanceira/comunicacaodados

[^45]: https://www.bcb.gov.br/estabilidadefinanceira/scr

[^46]: https://www.bcb.gov.br/estabilidadefinanceira/monitoramento

[^47]: https://cosif.com.br/publica.asp?arquivo=res-cmn-4966

[^48]: https://www.bcb.gov.br/estabilidadefinanceira/validador_xml_info

[^49]: https://www.bcb.gov.br/estabilidadefinanceira/relacao_instituicoes_funcionamento

[^50]: https://www.b3bee.com.br/site/2022/06/28/validacao-de-cadoc-xml-e-json/

[^51]: https://www.e-auditoria.com.br/blog/validador-xml/

[^52]: https://giro.tech/cadoc-3040/

[^53]: https://www.gov.br/pt-br/servicos/enviar-documentos-pelo-protocolo-digital-do-banco-central

[^54]: https://www.matera.com/br/blog/cadoc-3040/

[^55]: https://www.legisweb.com.br/legislacao/?legislacao=357787

[^56]: https://www.dattos.com.br/blog/cadoc/

[^57]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/Manual_de_Consulta_Garantidores_Registradoras.pdf

[^58]: https://pt.scribd.com/document/387248886/SCR3040-Criticas

[^59]: https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040

[^60]: https://www.sydle.com/br/blog/resolucao-4966-67fe6d2b8fd208761e4bcb93

[^61]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_Criticas.xls

[^62]: https://www.legisweb.com.br/legislacao/?legislacao=423489

[^63]: https://evertectrends.com/pt-br/como-calcular-a-ifrs-9/

[^64]: https://www.cieesc.org.br/site/calculadora-de-recesso-remunerado/

[^65]: https://pt.scribd.com/document/701408431/SCR3040-Leiaute-1

[^66]: https://www.youtube.com/watch?v=d_bMGt_5jcI

[^67]: https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Instrução+Normativa+BCB\&numero=414

[^68]: https://pt.scribd.com/document/805860184/SCR-Instrucoes-De-Preenchimento-Doc3040

[^69]: https://kpmg.com/br/pt/home/insights/2025/09/resolucao-4966.html

[^70]: https://cosif.com.br/publica.asp?arquivo=res-cmn-4966-04

[^71]: https://www.legisweb.com.br/legislacao/?id=450715

[^72]: https://pt.linkedin.com/pulse/nova-era-do-risco-de-crédito-res-4966-parte-x-perda-donelian-gbcdf

[^73]: https://okai.com.br/blog/instrucao-normativa-bcb-n627-novas-categorias-no-scr-e-fortalecimento-da-gestao-de-risco-de-credito

[^74]: https://cmsarquivos.febraban.org.br/Arquivos/documentos/PDF/IRM_abril_20.pdf

[^75]: https://pesquisa.in.gov.br/imprensa/servlet/INPDFViewer?jornal=515\&pagina=154\&data=03%2F10%2F2025\&captchafield=firstAccess

[^76]: https://www.b3.com.br/data/files/83/82/F4/55/733B7910C2881879AC094EA8/Manual de Operacoes - FUNCOES TVM.pdf

[^77]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/exemploLimiteCredito.xml

[^78]: https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3045-46_Leiaute.xls

[^79]: https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040_faq

