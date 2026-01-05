"""
Módulo para implementar a lógica de triggers para migração de estágios de risco.
Baseado na documentação técnica e requisitos da Resolução CMN nº 4.966.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

# Adicionar o caminho do diretório raiz do projeto ao sys.path, se necessário
# import sys
# import os
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if project_root not in sys.path:
#     sys.path.append(project_root)
# from utils.uteis import PREMISSAS_GERAIS # Exemplo

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de modalidades consideradas Rotativo
MODALIDADES_ROTATIVO = [
    "1304 : Outros créditos - cartão de crédito - compra à vista e parcelado lojista",
    "210 : Empréstimos - cartão de crédito – compra",
    "204 : Empréstimos - crédito rotativo vinculado a cartão de crédito",
    "218 : Empréstimos - cartão de crédito - não migrado",
    "213 : Empréstimos - cheque especial",
    "101 : Adiantamento a depositantes - adiantamento a depositantes",
    "301 : Direitos creditórios descontados - desconto de duplicatas"
]

# Lista de modalidades consideradas Consignado (NOVO)
MODALIDADES_CONSIGNADO = [
    "76 : CONSIGNADO ESTADUAL",
    "89 : CONSIGNADO INATIVO/PENSIONISTA",
    "94 : CONSIGNADO PREFEITURA"
]

# Definição das regras de trigger por CLASSIFICAÇÃO (Rotativo/Parcelado/Consignado)
# Estes valores devem ser extraídos/confirmados pela documentação técnica
REGRAS_AUMENTO_RISCO_POR_CLASSIFICACAO = {
    "Parcelado": { # Usaremos "Parcelado" como a chave para todas as modalidades não-rotativas e não-consignado
        "pd_concessao_min": 0.0186,
        "pd_concessao_max": 0.0548,
        "pd_atual_min": 0.1112,
        "pd_atual_max": 0.2957,
        "novo_estagio": 2
    },
    "Rotativo": {
        "pd_concessao_min": 0.0164,
        "pd_concessao_max": 0.0981,
        "pd_atual_threshold": 0.45, # PD Atual > Threshold
        "novo_estagio": 2
    },
    "Consignado": { # Adicionado
        "pd_concessao_min": 0.0186,
        "pd_concessao_max": 0.0270,
        "pd_atual_min": 0.1105,
        "pd_atual_max": 0.1802,
        "novo_estagio": 2
    }
}

def classificar_tipo_operacao(linha_credito: Optional[str], modalidade_oper: Optional[str]) -> str:
    """Classifica a modalidade de operação em 'Rotativo', 'Parcelado' ou 'Consignado'.
    Verifica primeiro a 'linha_credito' para Consignado, depois 'modalidade_oper' para Rotativo.
    """
    if isinstance(linha_credito, str) and linha_credito in MODALIDADES_CONSIGNADO:
        return "Consignado"
    if isinstance(modalidade_oper, str) and modalidade_oper in MODALIDADES_ROTATIVO:
        return "Rotativo"
    return "Parcelado" # Default para outras modalidades

def avaliar_aumento_significativo_risco(
    df: pd.DataFrame,
    col_pd_concessao_inicial: str = 'pd_concessao_inicial', # Nome da coluna com PD da concessão
    col_pd_behavior_atual: str = 'pd_behavior_atual',       # Nome da coluna com PD behavior atual
    col_estagio_atual: str = 'estagio',
    col_id_contrato: str = 'ID_Contrato', # Ou qualquer identificador único do contrato
    col_modalidade_operacao: str = 'Modalidade Oper.', # Para Rotativo/Parcelado
    col_linha_credito: str = 'Linha de Crédito' # Para Consignado
) -> pd.DataFrame:
    """
    Avalia o aumento significativo do risco de crédito comparando a PD atual (behavior)
    com a PD no momento da concessão, com regras específicas por tipo de operação.
    Pode levar à migração para o Estágio 2 (ou outro, conforme regras).

    Args:
        df: DataFrame com os dados dos contratos, incluindo PDs e estágio atual.
        col_pd_concessao_inicial: Nome da coluna contendo a PD calculada na concessão.
        col_pd_behavior_atual: Nome da coluna contendo a PD behavior mais recente.
        col_estagio_atual: Nome da coluna do estágio de risco atual.
        col_id_contrato: Nome da coluna do identificador do contrato.
        col_modalidade_operacao: Nome da coluna que identifica a modalidade para Rotativo/Parcelado.
        col_linha_credito: Nome da coluna que identifica a linha de crédito para Consignado.

    Returns:
        DataFrame com a coluna de estágio potencialmente atualizada.
    """
    logging.info(f"Avaliando aumento significativo de risco para {len(df)} contratos com base na modalidade e linha de crédito.")
    df_triggers = df.copy()

    cols_necessarias = [
        col_pd_concessao_inicial, col_pd_behavior_atual,
        col_estagio_atual, col_id_contrato,
        col_modalidade_operacao, col_linha_credito # Adicionada col_linha_credito
    ]
    for col in cols_necessarias:
        if col not in df_triggers.columns:
            # Se a coluna não for essencial para todas as classificações, podemos apenas logar um aviso
            # e continuar, mas para este caso, ambas são usadas na classificação.
            if col == col_linha_credito and col_modalidade_operacao in df_triggers.columns:
                 logging.warning(f"Coluna '{col}' (para Consignado) não encontrada. Operações de Consignado podem não ser classificadas corretamente.")
                 # Criar a coluna com None para evitar erro no apply, se ela não existir.
                 # No entanto, a lógica de classificação já lida com None.
            elif col == col_modalidade_operacao and col_linha_credito in df_triggers.columns:
                 logging.warning(f"Coluna '{col}' (para Rotativo/Parcelado) não encontrada. Operações Rotativo/Parcelado podem não ser classificadas corretamente.")
            else:
                logging.error(f"Coluna essencial '{col}' não encontrada no DataFrame. Abortando trigger específico.")
                return df_triggers

    # Classificar operações
    # Lidar com o caso de colunas ausentes, passando None para a função de classificação
    # A função classificar_tipo_operacao já trata Optional[str]
    def get_classification(row):
        linha_cred_val = row[col_linha_credito] if col_linha_credito in row else None
        modalidade_op_val = row[col_modalidade_operacao] if col_modalidade_operacao in row else None
        return classificar_tipo_operacao(linha_cred_val, modalidade_op_val)

    df_triggers['_tipo_oper_classificada'] = df_triggers.apply(get_classification, axis=1)

    mascara_aplicavel_geral = (
        (df_triggers[col_estagio_atual] == 1) &
        pd.notnull(df_triggers[col_pd_concessao_inicial]) &
        pd.notnull(df_triggers[col_pd_behavior_atual]) &
        (df_triggers[col_pd_concessao_inicial] > 0)
    )

    df_aplicavel = df_triggers[mascara_aplicavel_geral]
    if df_aplicavel.empty:
        logging.info("Nenhum contrato em Estágio 1 com PDs válidas para avaliação de aumento de risco.")
        df_triggers.drop(columns=['_tipo_oper_classificada'], inplace=True, errors='ignore')
        return df_triggers

    ids_migrados_total = []

    for classificacao, regras in REGRAS_AUMENTO_RISCO_POR_CLASSIFICACAO.items():
        logging.info(f"Avaliando classificação: {classificacao}")
        df_classif_especifica = df_aplicavel[df_aplicavel['_tipo_oper_classificada'] == classificacao]

        if df_classif_especifica.empty:
            logging.info(f"Nenhum contrato aplicável para a classificação '{classificacao}'.")
            continue

        pd_concessao = df_classif_especifica[col_pd_concessao_inicial]
        pd_atual = df_classif_especifica[col_pd_behavior_atual]
        ids_contrato_classif = df_classif_especifica[col_id_contrato]
        novo_estagio_regra = regras["novo_estagio"]

        migrar_classif = pd.Series(False, index=df_classif_especifica.index)

        if classificacao == "Parcelado":
            if not pd_concessao.empty: # Checagem para evitar erro em Series vazias
                cond_pd_concessao = (pd_concessao >= regras["pd_concessao_min"]) & (pd_concessao <= regras["pd_concessao_max"])
                cond_pd_atual = (pd_atual >= regras["pd_atual_min"]) & (pd_atual <= regras["pd_atual_max"])
                migrar_classif = cond_pd_concessao & cond_pd_atual
        elif classificacao == "Rotativo":
            if not pd_concessao.empty: # Checagem para evitar erro em Series vazias
                cond_pd_concessao = (pd_concessao >= regras["pd_concessao_min"]) & (pd_concessao <= regras["pd_concessao_max"])
                cond_pd_atual = (pd_atual > regras["pd_atual_threshold"])
                migrar_classif = cond_pd_concessao & cond_pd_atual
        elif classificacao == "Consignado": # Adicionado
            if not pd_concessao.empty:
                cond_pd_concessao = (pd_concessao >= regras["pd_concessao_min"]) & (pd_concessao <= regras["pd_concessao_max"])
                cond_pd_atual = (pd_atual >= regras["pd_atual_min"]) & (pd_atual <= regras["pd_atual_max"])
                migrar_classif = cond_pd_concessao & cond_pd_atual
        # Adicionar elif para outras classificações com regras diferentes, se houver.
        # Se não houver regra específica para uma classificação, nenhum trigger de aumento de risco será aplicado para ela,
        # a menos que uma regra genérica seja definida abaixo.

        ids_migrar_desta_classif = ids_contrato_classif[migrar_classif].tolist()

        if ids_migrar_desta_classif:
            # Aplicar a migração no DataFrame original df_triggers
            df_triggers.loc[df_triggers[col_id_contrato].isin(ids_migrar_desta_classif), col_estagio_atual] = novo_estagio_regra
            logging.info(f"{len(ids_migrar_desta_classif)} contratos da classificação '{classificacao}' migrados para Estágio {novo_estagio_regra} por aumento de risco.")
            ids_migrados_total.extend(ids_migrar_desta_classif)
        else:
            logging.info(f"Nenhum contrato da classificação '{classificacao}' migrou por aumento de risco específico.")

    if not ids_migrados_total:
        logging.info("Nenhum contrato migrou para Estágio 2 ou superior por aumento significativo de risco nesta avaliação (baseado em regras específicas por classificação).")

    # Remover a coluna temporária de classificação
    df_triggers.drop(columns=['_tipo_oper_classificada'], inplace=True, errors='ignore')
    return df_triggers

def aplicar_triggers_qualitativos(
    df: pd.DataFrame,
    col_linha_credito: str, # Adicionada para identificar reestruturações
    col_estagio_atual: str = 'estagio',
    col_id_contrato: str = 'ID_Contrato'
) -> pd.DataFrame:
    """
    Aplica triggers qualitativos baseados na identificação de reestruturações.
    Contratos identificados como reestruturação (via palavras-chave na coluna 'Linha de Crédito')
    são movidos para o Estágio 3.

    Args:
        df: DataFrame com os dados dos contratos.
        col_linha_credito: Nome da coluna contendo informações sobre a linha de crédito,
                           usada para identificar reestruturações.
        col_estagio_atual: Nome da coluna do estágio de risco atual.
        col_id_contrato: Nome da coluna do identificador do contrato.

    Returns:
        DataFrame com a coluna de estágio potencialmente atualizada.
    """
    logging.info(f"Aplicando triggers qualitativos (reestruturações para Estágio 3) para {len(df)} contratos.")
    df_triggers = df.copy()

    if col_linha_credito not in df_triggers.columns:
        logging.warning(f"Coluna '{col_linha_credito}' não encontrada. Não é possível aplicar triggers qualitativos baseados em reestruturação.")
        return df_triggers    # Palavras-chave para identificar reestruturações na coluna 'Linha de Crédito'
    # O regex ignora maiúsculas/minúsculas e acentuação para 'confissao' e 'renegociacao'
    palavras_chave_reneg = r'(?:CONFISS[AÃ]O|RENEGOCIA[CÇ][AÃ]O)'

    # Garante que a coluna é do tipo string para aplicar o .str.contains e lida com NaNs    # .str.contains retorna NaN para valores não string, fillna(False) trata isso.
    # Usando regex sem grupos de captura para evitar warning
    mascara_restruturacao = (
        df_triggers[col_linha_credito]
        .astype(str) # Garante que é string para evitar erros com tipos mistos
        .str.contains(palavras_chave_reneg, case=False, regex=True, na=False)
    )

    # Aplica a migração para Estágio 3 se for uma reestruturação e o estágio atual for menor que 3
    condicao_migrar_para_e3 = mascara_restruturacao & (df_triggers[col_estagio_atual] < 3)
    ids_migrar_para_e3 = df_triggers.loc[condicao_migrar_para_e3, col_id_contrato].tolist()

    if ids_migrar_para_e3:
        df_triggers.loc[condicao_migrar_para_e3, col_estagio_atual] = 3
        logging.info(f"{len(ids_migrar_para_e3)} contratos migrados para Estágio 3 devido à identificação como reestruturação (via '{col_linha_credito}').")
    else:
        logging.info(f"Nenhum contrato novo migrou para Estágio 3 com base nos triggers qualitativos de reestruturação (via '{col_linha_credito}').")

    return df_triggers

def aplicar_triggers_atraso(
    df: pd.DataFrame,
    col_dias_atraso: str = 'Dias Atraso', # Nome da coluna com dias em atraso
    col_estagio_atual: str = 'estagio',
    col_id_contrato: str = 'ID_Contrato'
) -> pd.DataFrame:
    """
    Aplica triggers baseados em dias de atraso.
    - Mais de 30 dias de atraso: geralmente Estágio 2.
    - Mais de 90 dias de atraso: geralmente Estágio 3.

    Args:
        df: DataFrame com os dados dos contratos.
        col_dias_atraso: Nome da coluna contendo os dias em atraso.
        col_estagio_atual: Nome da coluna do estágio de risco atual.
        col_id_contrato: Nome da coluna do identificador do contrato.

    Returns:
        DataFrame com a coluna de estágio potencialmente atualizada.
    """
    logging.info(f"Aplicando triggers de atraso para {len(df)} contratos.")
    df_triggers = df.copy()

    if col_dias_atraso not in df_triggers.columns:
        logging.error(f"Coluna de dias de atraso '{col_dias_atraso}' não encontrada.")
        return df_triggers # Retorna o DF original se a coluna chave estiver faltando

    # Trigger para Estágio 3 (mais de 90 dias de atraso) - tem prioridade
    condicao_estagio3_atraso = (df_triggers[col_dias_atraso] > 90)
    ids_migrar_estagio3_atraso = df_triggers.loc[condicao_estagio3_atraso, col_id_contrato].tolist()
    if ids_migrar_estagio3_atraso:
        df_triggers.loc[df_triggers[col_id_contrato].isin(ids_migrar_estagio3_atraso), col_estagio_atual] = 3
        logging.info(f"{len(ids_migrar_estagio3_atraso)} contratos migrados para Estágio 3 (atraso > 90 dias).")

    # Trigger para Estágio 2 (mais de 30 dias de atraso E não já em Estágio 3)
    condicao_estagio2_atraso = (
        (df_triggers[col_dias_atraso] > 30) &
        (df_triggers[col_dias_atraso] <= 90) & # Apenas se não for pego pela regra de >90 dias
        (df_triggers[col_estagio_atual] < 2)   # Apenas se não estiver já em Estágio 2 ou 3 por outro motivo
    )
    ids_migrar_estagio2_atraso = df_triggers.loc[condicao_estagio2_atraso, col_id_contrato].tolist()
    if ids_migrar_estagio2_atraso:
        df_triggers.loc[df_triggers[col_id_contrato].isin(ids_migrar_estagio2_atraso), col_estagio_atual] = 2
        logging.info(f"{len(ids_migrar_estagio2_atraso)} contratos migrados para Estágio 2 (atraso > 30 e <= 90 dias).")

    return df_triggers

def aplicar_arrasto_contraparte(
    df: pd.DataFrame,
    col_id_contraparte: str = 'ID_Contraparte', # Nome da coluna com ID da contraparte/cliente
    col_estagio_atual: str = 'estagio',
    col_id_contrato: str = 'ID_Contrato',
    aplicar_arrasto: bool = True
) -> pd.DataFrame:
    """
    Aplica a regra de arrasto de contraparte: se um contrato de uma contraparte
    for para o Estágio 3, todos os outros contratos da mesma contraparte devem
    também ser migrados para o Estágio 3 (com exceções).

    Args:
        df: DataFrame com os dados dos contratos.
        col_id_contraparte: Nome da coluna do identificador da contraparte.
        col_estagio_atual: Nome da coluna do estágio de risco atual.
        col_id_contrato: Nome da coluna do identificador do contrato.
        aplicar_arrasto: Flag para habilitar/desabilitar a lógica de arrasto.

    Returns:
        DataFrame com a coluna de estágio potencialmente atualizada.
    """
    if not aplicar_arrasto:
        logging.info("Arrasto de contraparte desabilitado.")
        return df

    logging.info(f"Aplicando regra de arrasto de contraparte para {len(df)} contratos.")
    df_triggers = df.copy()

    if col_id_contraparte not in df_triggers.columns:
        logging.error(f"Coluna de ID da contraparte '{col_id_contraparte}' não encontrada. Arrasto não aplicado.")
        return df_triggers

    # Identificar todas as contrapartes que têm pelo menos um contrato em Estágio 3
    contrapartes_com_estagio3 = df_triggers[df_triggers[col_estagio_atual] == 3][col_id_contraparte].unique()

    if len(contrapartes_com_estagio3) > 0:
        logging.info(f"Encontradas {len(contrapartes_com_estagio3)} contrapartes com ao menos um contrato em Estágio 3.")

        # Marcar todos os contratos dessas contrapartes que ainda não estão em Estágio 3
        # (e que não são o próprio contrato que originou o Estágio 3, embora a condição já cubra isso)
        condicao_arrasto = (
            df_triggers[col_id_contraparte].isin(contrapartes_com_estagio3) &
            (df_triggers[col_estagio_atual] < 3)
        )

        ids_contratos_arrastados = df_triggers.loc[condicao_arrasto, col_id_contrato].tolist()

        if ids_contratos_arrastados:
            df_triggers.loc[condicao_arrasto, col_estagio_atual] = 3
            logging.info(f"{len(ids_contratos_arrastados)} contratos adicionais migrados para Estágio 3 devido à regra de arrasto.")
        else:
            logging.info("Nenhum contrato adicional migrado por arrasto (todos os contratos das contrapartes afetadas já estavam em Estágio 3 ou não havia outros).")
    else:
        logging.info("Nenhuma contraparte com contratos em Estágio 3 encontrada para aplicar arrasto.")

    return df_triggers

def aplicar_todos_triggers_estagios(
    df_original: pd.DataFrame,
    col_pd_concessao: str, # PD na concessão para avaliar aumento de risco
    col_pd_behavior: str,  # PD behavior atual para avaliar aumento de risco
    col_dias_atraso: str,
    col_id_contraparte: Optional[str] = None, # Opcional, só usado se arrasto for habilitado
    aplicar_arrasto_flag: bool = False,
    col_modalidade_operacao_param: str = 'Modalidade Oper.', # Novo parâmetro com sufixo
    col_linha_credito_param: str = 'Linha de Crédito' # Novo parâmetro com sufixo
    # Adicionar outros parâmetros conforme as colunas reais do DataFrame
    # Ex: col_tipo_renegociacao, etc.
) -> pd.DataFrame:
    """
    Orquestra a aplicação de todas as lógicas de trigger para determinar o estágio final.
    A ordem de aplicação pode ser importante.
    Geralmente: Atraso/Qualitativo para E3 -> Aumento Risco para E2 -> Atraso para E2.
    Arrasto é aplicado por último sobre o resultado.

    Args:
        df_original: DataFrame de entrada.
        col_pd_concessao: Nome da coluna com PD da concessão.
        col_pd_behavior: Nome da coluna com PD behavior atual.
        col_dias_atraso: Nome da coluna com dias em atraso.
        col_id_contraparte: Nome da coluna com ID da contraparte (para arrasto).
        aplicar_arrasto_flag: Se True, aplica a regra de arrasto.

    Returns:
        DataFrame com a coluna 'estagio' (ou 'estagio_final') atualizada.
    """
    if df_original.empty:
        logging.warning("DataFrame de entrada para aplicar_todos_triggers_estagios está vazio.")
        return df_original

    df_processado = df_original.copy()

    # Assumindo que 'estagio' já existe e foi pré-classificado (ex: por classificar_estagio_aprimorado)
    # Se não, precisaria ser inicializado aqui.
    if 'estagio' not in df_processado.columns:
        logging.warning("Coluna 'estagio' não encontrada. Inicializando com 1. A classificação inicial por atraso deve ocorrer antes.")
        # Uma classificação básica por dias de atraso poderia ser um fallback aqui,
        # mas o ideal é que 'classificar_estagio_aprimorado' já tenha rodado.
        # Por simplicidade, vamos assumir que ela já existe ou será criada antes.
        # Se for criada aqui, a lógica de aplicar_triggers_atraso pode ser redundante ou precisar de ajuste.
        # df_processado['estagio'] = 1 # Fallback muito simples
        # Para este esqueleto, vamos focar nos triggers adicionais.
        # A função `classificar_estagio_aprimorado` de `utils.uteis` já faz uma primeira passagem.
        # Os triggers aqui refinam essa classificação.

    logging.info("Iniciando aplicação de todos os triggers de estágio...")

    # 1. Triggers de Atraso (especialmente para E3, que tem alta prioridade)
    #    e também para E2 se não houver outros triggers mais fortes.
    #    A função aplicar_triggers_atraso já lida com a prioridade E3 > E2.
    df_processado = aplicar_triggers_atraso(
        df_processado,
        col_dias_atraso=col_dias_atraso,
        col_estagio_atual='estagio',
        col_id_contrato='ID_Contrato' # Assumindo que existe
    )

    # 2. Triggers Qualitativos (podem levar a E2 ou E3)
    #    Estes devem ser aplicados após o atraso inicial para E3,
    #    mas podem sobrescrever E1 ou E2 de atrasos menores se o qualitativo for mais severo.
    df_processado = aplicar_triggers_qualitativos(
        df_processado,
        col_linha_credito=col_linha_credito_param, # Passando a coluna para identificar reestruturações
        col_estagio_atual='estagio',
        col_id_contrato='ID_Contrato'
    )

    # 3. Avaliação de Aumento Significativo de Risco (PD Concessão vs PD Behavior)
    #    Este trigger geralmente leva para E2 e deve ser avaliado para contratos
    #    que ainda estão em E1 após os triggers de atraso e qualitativos mais severos.
    df_processado = avaliar_aumento_significativo_risco(
        df_processado,
        col_pd_concessao_inicial=col_pd_concessao,
        col_pd_behavior_atual=col_pd_behavior,
        col_estagio_atual='estagio',
        col_id_contrato='ID_Contrato',
        col_modalidade_operacao=col_modalidade_operacao_param, # Usar o novo parâmetro
        col_linha_credito=col_linha_credito_param # Usar o novo parâmetro
    )

    # 4. Arrasto de Contraparte (aplicado por último, se habilitado)
    #    Se col_id_contraparte não for fornecido e aplicar_arrasto_flag for True, logar um aviso.
    if aplicar_arrasto_flag:
        if col_id_contraparte and col_id_contraparte in df_processado.columns:
            df_processado = aplicar_arrasto_contraparte(
                df_processado,
                col_id_contraparte=col_id_contraparte,
                col_estagio_atual='estagio',
                col_id_contrato='ID_Contrato',
                aplicar_arrasto=True
            )
        elif not col_id_contraparte:
            logging.warning("Arrasto de contraparte habilitado, mas nome da coluna 'col_id_contraparte' não fornecido.")
        else: # col_id_contraparte fornecido mas não existe no df
             logging.warning(f"Arrasto de contraparte habilitado, mas coluna '{col_id_contraparte}' não encontrada no DataFrame.")

    # Poderia haver uma etapa final para garantir que o estágio não diminuiu indevidamente
    # se a lógica de aplicação não for estritamente hierárquica.
    # Ex: df_processado['estagio'] = df_processado[['estagio_inicial_calculado_por_atraso', 'estagio_trigger_qualitativo', ...]].max(axis=1)
    # Mas a ordem de aplicação acima tenta lidar com isso.

    logging.info("Aplicação de todos os triggers de estágio concluída.")
    return df_processado

# Exemplo de como poderia ser usado (requer DataFrame com as colunas corretas):
if __name__ == '__main__':
    # Criar um DataFrame de exemplo
    data_exemplo = {
        'ID_Contrato': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'ID_Contraparte': ['C1', 'C1', 'C2', 'C2', 'C3', 'C3', 'C4', 'C4', 'C5', 'C5'],
        'estagio':             [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # Estágio inicial (pode vir de classificar_estagio_aprimorado)
        'Dias Atraso':         [0, 35, 95, 10, 0, 40, 100, 0, 0, 0],
        'pd_concessao_inicial':[0.01, 0.02, 0.01, 0.03, 0.05, 0.02, 0.01, 0.04, 0.02, 0.025], # Ajustado o último valor
        'pd_behavior_atual':   [0.015, 0.025, 0.50, 0.08, 0.15, 0.03, 0.6, 0.05, 0.022, 0.15], # Ajustado o último valor
        'Modalidade Oper.':    ["1304 : Outros créditos - cartão de crédito - compra à vista e parcelado lojista", # Rotativo
                                "210 : Empréstimos - cartão de crédito – compra", # Rotativo
                                "204 : Empréstimos - crédito rotativo vinculado a cartão de crédito", # Rotativo
                                "Produto Parcelado A", # Parcelado
                                "Produto Parcelado B", # Parcelado
                                "101 : Adiantamento a depositantes - adiantamento a depositantes", # Rotativo
                                "301 : Direitos creditórios descontados - desconto de duplicatas", # Rotativo
                                "Produto Parcelado C", # Parcelado
                                "Produto Parcelado D", # Parcelado
                                "Produto Parcelado E"], # Parcelado (para teste Consignado)
        'Linha de Crédito':    [None, # Não Consignado
                                None, # Não Consignado
                                None, # Não Consignado
                                "Linha Parcelada X", # Não Consignado
                                "Linha Parcelada Y", # Não Consignado
                                None, # Não Consignado
                                None, # Não Consignado
                                "Linha Parcelada Z", # Não Consignado
                                "Outra Linha Qualquer", # Não Consignado
                                "76 : CONSIGNADO ESTADUAL"] # Consignado
        # Adicionar colunas para triggers qualitativos se necessário
        # 'tipo_renegociacao': [None, 'parcelamento_fatura', None, None, 'confissao_divida_pj', None, None, None, None, None]
    }
    df_teste = pd.DataFrame(data_exemplo)

    logging.info("\n--- DataFrame Original ---")
    print(df_teste)

    # Aplicar triggers
    df_com_triggers = aplicar_todos_triggers_estagios(
        df_teste,
        col_pd_concessao='pd_concessao_inicial',
        col_pd_behavior='pd_behavior_atual',
        col_dias_atraso='Dias Atraso',
        col_id_contraparte='ID_Contraparte',
        aplicar_arrasto_flag=True,
        col_modalidade_operacao_param='Modalidade Oper.', # Passando explicitamente
        col_linha_credito_param='Linha de Crédito' # Passando explicitamente
    )

    logging.info("\n--- DataFrame Com Triggers Aplicados ---")
    print(df_com_triggers)

    # Verificar migrações esperadas:
    # Contrato 2: E1 -> E2 (atraso > 30d)
    # Contrato 3: E1 -> E3 (atraso > 90d)
    # Contrato 4: E1 -> E2 (PD behavior > 200% PD concessão: 0.08 / 0.03 = 2.66)
    # Contrato 5: E1 -> E2 (PD behavior > 200% PD concessão: 0.15 / 0.05 = 3.0)
    # Contrato 6: E1 -> E2 (atraso > 30d)
    # Contrato 7: E1 -> E3 (atraso > 90d)
    # Contrato 8: E1 -> E3 (arrasto do contrato 7, mesma contraparte C4)
    # Contrato 1: E1 -> E3 (arrasto do contrato 2, que foi para E2 por atraso, mas se C1 tivesse um E3, arrastaria)
    #    - Correção na expectativa: arrasto é para E3. Se Ctr 2 vai para E2, não arrasta Ctr 1 para E3.
    #      Se Ctr 3 (C2) vai para E3, Ctr 4 (C2) deve ir para E3 por arrasto.
    #      Se Ctr 7 (C4) vai para E3, Ctr 8 (C4) deve ir para E3 por arrasto.

    # Refazendo expectativas com a lógica atual:
    # Ctr 1 (C1): E1 (sem trigger direto)
    # Ctr 2 (C1): E1 -> E2 (atraso 35d)
    # Ctr 3 (C2): E1 -> E3 (atraso 95d)
    # Ctr 4 (C2): E1 -> E2 (PD > 2x), depois E2 -> E3 (arrasto de Ctr 3)
    # Ctr 5 (C3): E1 -> E2 (PD > 2x)
    # Ctr 6 (C3): E1 -> E2 (atraso 40d)
    # Ctr 7 (C4): E1 -> E3 (atraso 100d)
    # Ctr 8 (C4): E1 -> E3 (arrasto de Ctr 7)
    # Ctr 9 (C5): E1
    # Ctr 10 (C5): E1 -> E2 (Consignado, PD 0.025->0.15. Encaixa na regra.)

    # Resultados esperados (aproximados, verificar a lógica exata de aplicação e ordem):
    # ID 1: Estágio 1
    # ID 2: Estágio 2
    # ID 3: Estágio 3
    # ID 4: Estágio 3 (arrastado por ID 3)
    # ID 5: Estágio 2
    # ID 6: Estágio 2
    # ID 7: Estágio 3
    # ID 8: Estágio 3 (arrastado por ID 7)
    # ID 9: Estágio 1
    # ID 10: Estágio 2 (Consignado, PD 0.025->0.15. Encaixa na regra.)
    print("\n--- Verificações ---")
    print(f"ID 3 (C2) Estágio: {df_com_triggers[df_com_triggers['ID_Contrato'] == 3]['estagio'].iloc[0]}")
    print(f"ID 4 (C2) Estágio: {df_com_triggers[df_com_triggers['ID_Contrato'] == 4]['estagio'].iloc[0]}")
    print(f"ID 7 (C4) Estágio: {df_com_triggers[df_com_triggers['ID_Contrato'] == 7]['estagio'].iloc[0]}")
    print(f"ID 8 (C4) Estágio: {df_com_triggers[df_com_triggers['ID_Contrato'] == 8]['estagio'].iloc[0]}")
    print(f"ID 10 (C5) Estágio: {df_com_triggers[df_com_triggers['ID_Contrato'] == 10]['estagio'].iloc[0]}") # Teste Consignado

def analisar_triggers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisa triggers de estágios para o DataFrame fornecido.
    
    Args:
        df: DataFrame com dados dos contratos
        
    Returns:
        DataFrame com análise de triggers aplicada
    """
    try:
        logging.info("Iniciando análise de triggers de estágios")
        
        # Criar cópia do DataFrame
        df_resultado = df.copy()
        
        # Inicializar coluna de estágio se não existir
        if 'estagio' not in df_resultado.columns:
            df_resultado['estagio'] = 1  # Estágio padrão
        
        # Adicionar colunas necessárias se não existirem
        if 'pd_concessao_inicial' not in df_resultado.columns:
            df_resultado['pd_concessao_inicial'] = 0.03  # PD padrão de concessão
        
        if 'pd_behavior_atual' not in df_resultado.columns:
            df_resultado['pd_behavior_atual'] = 0.05  # PD padrão behavior
        
        # Classificar estágio baseado em dias de atraso
        if 'Dias Atraso' in df_resultado.columns:
            # Estágio 3: > 90 dias de atraso
            mask_estagio_3 = df_resultado['Dias Atraso'] > 90
            df_resultado.loc[mask_estagio_3, 'estagio'] = 3
            
            # Estágio 2: 30-90 dias de atraso
            mask_estagio_2 = (df_resultado['Dias Atraso'] >= 30) & (df_resultado['Dias Atraso'] <= 90)
            df_resultado.loc[mask_estagio_2, 'estagio'] = 2
        
        # Aplicar trigger de aumento significativo de risco
        # PD atual > 2x PD concessão = migração para estágio 2
        mask_aumento_risco = (
            (df_resultado['estagio'] == 1) &
            (df_resultado['pd_behavior_atual'] > 2 * df_resultado['pd_concessao_inicial'])
        )
        df_resultado.loc[mask_aumento_risco, 'estagio'] = 2
        
        # Adicionar colunas de análise
        df_resultado['trigger_aplicado'] = 'NENHUM'
        df_resultado['motivo_trigger'] = 'SEM_TRIGGER'
        
        # Marcar triggers aplicados
        if 'Dias Atraso' in df_resultado.columns:
            mask_trigger_atraso_3 = df_resultado['Dias Atraso'] > 90
            df_resultado.loc[mask_trigger_atraso_3, 'trigger_aplicado'] = 'ATRASO_90_DIAS'
            df_resultado.loc[mask_trigger_atraso_3, 'motivo_trigger'] = 'ATRASO_SUPERIOR_90_DIAS'
            
            mask_trigger_atraso_2 = (df_resultado['Dias Atraso'] >= 30) & (df_resultado['Dias Atraso'] <= 90)
            df_resultado.loc[mask_trigger_atraso_2, 'trigger_aplicado'] = 'ATRASO_30_DIAS'
            df_resultado.loc[mask_trigger_atraso_2, 'motivo_trigger'] = 'ATRASO_ENTRE_30_90_DIAS'
        
        # Marcar trigger de aumento de risco
        mask_trigger_risco = (
            (df_resultado['pd_behavior_atual'] > 2 * df_resultado['pd_concessao_inicial']) &
            (df_resultado['trigger_aplicado'] == 'NENHUM')
        )
        df_resultado.loc[mask_trigger_risco, 'trigger_aplicado'] = 'AUMENTO_RISCO'
        df_resultado.loc[mask_trigger_risco, 'motivo_trigger'] = 'PD_BEHAVIOR_MAIOR_2X_PD_CONCESSAO'
        
        # Estatísticas
        total_contratos = len(df_resultado)
        estagio_1 = len(df_resultado[df_resultado['estagio'] == 1])
        estagio_2 = len(df_resultado[df_resultado['estagio'] == 2])
        estagio_3 = len(df_resultado[df_resultado['estagio'] == 3])
        
        logging.info(f"Análise de triggers concluída para {total_contratos} contratos")
        logging.info(f"Estágio 1: {estagio_1} contratos ({estagio_1/total_contratos*100:.1f}%)")
        logging.info(f"Estágio 2: {estagio_2} contratos ({estagio_2/total_contratos*100:.1f}%)")
        logging.info(f"Estágio 3: {estagio_3} contratos ({estagio_3/total_contratos*100:.1f}%)")
        
        return df_resultado
        
    except Exception as e:
        logging.error(f"Erro na análise de triggers: {str(e)}")
        # Retornar DataFrame original em caso de erro
        return df
