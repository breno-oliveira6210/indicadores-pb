import pandas as pd
from ingestion import listar_arquivos
from cleaning import limpar_arquivo

# Para cada tipo, define quais colunas identificam um evento de forma única
CHAVE_UNICA = {
    "ADM": ["codigo_empresa", "nome_funcionario", "data_admissao"],
    "FER": ["codigo_empresa", "nome_funcionario", "data_inicio_gozo", "data_fim_gozo"],
    "RES": ["codigo_empresa", "nome_funcionario", "data_demissao"],
}


def consolidar_por_tipo(tipo, arquivos):
    """Junta todos os arquivos de um mesmo tipo (ADM, FER ou RES) em um único dataframe."""
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
        df["arquivo_origem"] = item["arquivo"]
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def verificar_duplicados(tipo, df):
    chave = CHAVE_UNICA[tipo]
    total_linhas = len(df)

    duplicados = df[df.duplicated(subset=chave, keep=False)]
    total_duplicados = len(duplicados)

    print(f"\n{'=' * 70}")
    print(f"Tipo: {tipo}")
    print(f"{'=' * 70}")
    print(f"Total de linhas (somando todos os meses): {total_linhas}")
    print(f"Linhas envolvidas em duplicidade: {total_duplicados}")

    if total_duplicados > 0:
        print(f"\nExemplo de registros duplicados (mesma pessoa/evento em mais de 1 arquivo):")
        exemplo_chave = duplicados[chave].iloc[0].to_dict()
        exemplo = df[
            (df[chave[0]] == exemplo_chave[chave[0]]) &
            (df[chave[1]] == exemplo_chave[chave[1]])
        ]
        print(exemplo[chave + ["arquivo_origem"]].to_string(index=False))
    else:
        print("Nenhuma duplicidade encontrada para este tipo. ✅")


if __name__ == "__main__":
    validos, invalidos = listar_arquivos()

    for tipo in ["ADM", "FER", "RES"]:
        df_tipo = consolidar_por_tipo(tipo, validos)
        verificar_duplicados(tipo, df_tipo)