# Plano de Ação: Correção do Agente e Integração com Dados Reais

Detectei que o Agente atual está configurado para usar **PostgreSQL** e consome dados **mockados** (fictícios) em vez de consultar o banco real. Além disso, não há um script automático para carregar os CSVs da pasta `/dados` para o banco.

## 1. Ajuste de Infraestrutura de Banco de Dados
- **Problema:** O código atual (`backend/agente/database.py`) usa drivers de PostgreSQL (`psycopg2`), mas o projeto especifica MySQL (`dbrisco`).
- **Ação:** Refatorar a conexão para usar **MySQL** (via `mysql-connector-python` ou `pymysql`), alinhando com o restante do sistema.

## 2. Migração de Dados (ETL)
- **Problema:** Os arquivos CSV em `e:\Projetos\risco_bancario\dados` (`base_clientes.csv`, `base_3040.csv`, etc.) não estão no banco de dados.
- **Ação:** Criar um script `backend/scripts/carga_dados_csv.py` que:
    1.  Lê os arquivos CSV da pasta `/dados`.
    2.  Trata tipos de dados (datas, números).
    3.  Insere os registros nas tabelas correspondentes do banco `dbrisco`.

## 3. "Lobotomia" do Agente (Remoção de Mocks)
- **Problema:** O arquivo `tools_orquestrador.py` importa funções de `mock_data.py`.
- **Ação:**
    1.  Editar `tools_orquestrador.py` para remover dependências de mock.
    2.  Implementar consultas SQL reais dentro da função `obter_dados()` para buscar:
        -   **PRINAD:** Consultar tabela de classificações/clientes.
        -   **ECL:** Consultar tabela de resultados de perda esperada.
        -   **Portfólio:** Calcular agregados (SUM, AVG) diretamente via SQL.

## 4. Teste Integrado
- **Objetivo:** Garantir que o Agente responda com dados reais.
- **Passo a Passo:**
    1.  Rodar o script de carga (ETL).
    2.  Iniciar o Backend (FastAPI).
    3.  Iniciar o Frontend (Vite).
    4.  **Teste no Browser:** Perguntar ao Agente "Qual o total da carteira?" e verificar se o valor bate com a soma do CSV (e não com o valor fixo do mock).

Gostaria que eu prosseguisse com este plano, começando pela refatoração da conexão de banco para MySQL e criação do script de carga?