# Plano de Entrega - Módulo PRINAD (Banpará)

Abaixo está o plano detalhado para extrair, organizar e documentar o módulo PRINAD conforme solicitado.

## 1. Estrutura de Diretórios
Criarei a seguinte estrutura de pastas em `e:\Projetos\risco_bancario\banpara\`:
- `modelos/`: Contém todo o código fonte do modelo (treinamento, classificação, pipeline).
- `artefatos/`: Contém os binários treinados (.joblib) e relatórios (.json).
- `api/`: Contém a API FastAPI e seus utilitários diretos.
- `docs/`: Contém a documentação técnica solicitada.

## 2. Seleção e Cópia de Arquivos

### Diretório `modelos/`
Copiarei os scripts de processamento e lógica de negócio de `backend/prinad/src/`:
- `classifier.py` (Lógica de classificação e Rating)
- `train_model.py` (Script de treinamento)
- `data_pipeline.py` (Carregamento e preparação)
- `feature_engineering.py` (Engenharia de features)
- `historical_penalty.py` (Penalidades históricas)
- `data_balancing.py` (Balanceamento de dados)
- `optimize_model.py` (Otimização de hiperparâmetros)
- `model_monitoring.py` (Monitoramento e drift)
- `scr_data_generator.py` (Gerador de dados mock SCR)
- `data_consolidator_prinad.py` (Consolidação de bases)

### Diretório `artefatos/`
Copiarei todo o conteúdo de `backend/prinad/modelo/`:
- Modelos: `ensemble_model.joblib`, `preprocessor.joblib`, `shap_explainer.joblib`
- Metadados: `feature_names.joblib`, `training_metrics.joblib`
- Relatórios: `*.json`

### Diretório `api/`
Copiarei os scripts de interface de `backend/prinad/src/`:
- `api.py` (Aplicação principal)
- `api_monitoring.py` (Endpoints de monitoramento)
*Nota: Ajustarei os imports no `api.py` para localizar os módulos na pasta `../modelos`.*

## 3. Criação de Documentação (`docs/`)

### `requisitos_dados.md`
Documento detalhando os inputs necessários:
- Schema do CSV de Clientes (Dados Cadastrais).
- Schema do CSV Comportamental (V-columns).
- Schema dos dados do SCR (BACEN).
- Dicionário de variáveis explicativo.

### `api_documentation.md`
Guia de uso da API:
- Descrição dos endpoints (`/simple_classify`, `/explained_classify`, etc.).
- Exemplos de Request/Response (JSON).
- Instruções de execução local.

### `notebook_completo.md`
Arquivo Markdown formatado para fácil conversão em Jupyter Notebook, contendo:
1.  **Setup**: Imports e configurações.
2.  **Carregamento**: Células de código para ler os CSVs (explicando que os dados não estão inclusos).
3.  **Pré-processamento**: Limpeza, tratamento de nulos e engenharia de features.
4.  **Treinamento**: Pipeline de treino, balanceamento (SMOTE) e calibração.
5.  **Avaliação**: Geração de métricas (AUC, Gini, KS) e gráficos (código para plotar).
6.  **Reporte**: Exibição dos resultados e salvamento dos artefatos.

## 4. Execução
Após sua confirmação, executarei as cópias e a criação dos arquivos de documentação.
