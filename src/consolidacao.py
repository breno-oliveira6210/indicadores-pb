import pandas as pd
from ingestion import listar_arquivos
from cleaning import limpar_arquivo

# Coluna que define a data "oficial" de cada tipo de evento,
# usada tanto para deduplicar quanto para saber o mês/ano real do evento
COLUNA_DATA_EVENTO = {
    "ADM": "data_admissao",
    "FER": "data_inicio_gozo",
    "RES": "data_demissao",
}

# Colunas que identificam um evento de forma única (usadas só para deduplicar)
CHAVE_UNICA = {
    "ADM": ["codigo_empresa", "nome_funcionario", "data_admissao"],
    "FER": ["codigo_empresa", "nome_funcionario", "data_inicio_gozo", "data_fim_gozo"],
    "RES": ["codigo_empresa", "nome_funcionario", "data_demissao"],
}


def consolidar_tipo(tipo, arquivos):
    """
    Junta todos os arquivos de um mesmo tipo, remove duplicatas e recalcula
    o mês/ano de referência com base na DATA REAL do evento (não no nome do arquivo).
    """
    partes = []
    for item in arquivos:
        if item["tipo"] != tipo:
            continue
        df = limpar_arquivo(
            caminho=item["caminho_completo"],
            tipo=item["tipo"],
            mes=item["mes"],
            ano=item["ano"],
        )
        partes.append(df)

    df_completo = pd.concat(partes, ignore_index=True)

    # Remove duplicatas, mantendo a primeira ocorrência de cada evento único
    chave = CHAVE_UNICA[tipo]
    df_completo = df_completo.drop_duplicates(subset=chave, keep="first")

    # Recalcula mes_referencia / ano_referencia com base na data real do evento,
    # em vez de confiar no nome do arquivo de origem
    coluna_data = COLUNA_DATA_EVENTO[tipo]
    df_completo["mes_referencia"] = df_completo[coluna_data].dt.month
    df_completo["ano_referencia"] = df_completo[coluna_data].dt.year

    return df_completo


def consolidar_tudo():
    """Retorna um único dataframe com ADM + FER + RES já limpos e deduplicados."""
    validos, invalidos = listar_arquivos()

    if invalidos:
        print(f"⚠️  Arquivos fora do padrão (ignorados): {invalidos}")

    partes = []
    for tipo in ["ADM", "FER", "RES"]:
        df_tipo = consolidar_tipo(tipo, validos)
        partes.append(df_tipo)
        print(f"{tipo}: {len(df_tipo)} eventos únicos após deduplicação")

    return partes  # lista com 3 dataframes: [df_adm, df_fer, df_res]


if __name__ == "__main__":
    df_adm, df_fer, df_res = consolidar_tudo()

    print("\nAmostra ADM:")
    print(df_adm.head(3).to_string())

    print("\nAmostra FER (verificando se deduplicação funcionou):")
    print(df_fer.head(3).to_string())

    print("\nAmostra RES:")
    print(df_res.head(3).to_string())