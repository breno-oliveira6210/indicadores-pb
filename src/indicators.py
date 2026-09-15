import pandas as pd


def adicionar_periodo(df):
    """
    Adiciona a coluna 'periodo' (primeiro dia do mês de referência, como Timestamp)
    para facilitar filtro por intervalo de datas e ordenação cronológica.
    Espera que o dataframe já tenha 'ano_referencia' e 'mes_referencia'.
    """
    df = df.copy()
    
    # 1. Elimina preventivamente os registros com data em branco (NaN)
    df = df.dropna(subset=["ano_referencia", "mes_referencia"])
    
    # 2. Força o retorno ao formato inteiro (removendo o .0) antes de virar texto
    ano_str = df["ano_referencia"].astype(int).astype(str)
    mes_str = df["mes_referencia"].astype(int).astype(str).str.zfill(2)
    
    # 3. Monta a data de forma segura
    df["periodo"] = pd.to_datetime(ano_str + "-" + mes_str + "-01")
    
    return df

def filtrar_periodo(df, data_inicio=None, data_fim=None):
    """Filtra um dataframe (já com coluna 'periodo') pelo intervalo [data_inicio, data_fim]."""
    df = df.copy()
    if data_inicio is not None:
        df = df[df["periodo"] >= pd.to_datetime(data_inicio)]
    if data_fim is not None:
        df = df[df["periodo"] <= pd.to_datetime(data_fim)]
    return df


def volume_por_mes(df, incluir_empresa=False):
    """
    Indicadores 1, 2 e 3: volume de eventos (ADM, FER ou RES) por mês,
    opcionalmente também por empresa.
    """
    colunas_grupo = ["ano_referencia", "mes_referencia"]
    if incluir_empresa:
        colunas_grupo.append("empresa")

    resultado = (
        df.groupby(colunas_grupo)
        .size()
        .reset_index(name="quantidade")
        .sort_values(colunas_grupo)
        .reset_index(drop=True)
    )
    return resultado


def volume_total(df_adm, df_fer, df_res, incluir_empresa=False):
    """
    Indicador 4: volume total (ADM + FER + RES) por mês, opcionalmente por empresa.
    Retorna (total_consolidado, detalhamento_por_tipo) — o segundo é útil para
    gráficos empilhados por tipo de solicitação.
    """
    colunas_grupo = ["ano_referencia", "mes_referencia"]
    if incluir_empresa:
        colunas_grupo.append("empresa")

    partes = []
    for tipo, df in [("ADM", df_adm), ("FER", df_fer), ("RES", df_res)]:
        v = volume_por_mes(df, incluir_empresa=incluir_empresa)
        v["tipo"] = tipo
        partes.append(v)

    detalhado = pd.concat(partes, ignore_index=True)

    total = (
        detalhado.groupby(colunas_grupo)["quantidade"]
        .sum()
        .reset_index()
        .sort_values(colunas_grupo)
        .reset_index(drop=True)
    )
    return total, detalhado


def saldo_liquido_movimentacao(df_adm, df_res, incluir_empresa=False):
    """
    Indicador 5: saldo líquido de movimentação (admissões - rescisões) por mês,
    opcionalmente por empresa. Positivo = crescimento de quadro; negativo = redução.
    Não é "taxa de turnover" (não temos o headcount total ativo).
    """
    colunas_grupo = ["ano_referencia", "mes_referencia"]
    if incluir_empresa:
        colunas_grupo.append("empresa")

    vol_adm = volume_por_mes(df_adm, incluir_empresa=incluir_empresa).rename(
        columns={"quantidade": "admissoes"}
    )
    vol_res = volume_por_mes(df_res, incluir_empresa=incluir_empresa).rename(
        columns={"quantidade": "rescisoes"}
    )

    saldo = pd.merge(vol_adm, vol_res, on=colunas_grupo, how="outer").fillna(0)
    saldo["admissoes"] = saldo["admissoes"].astype(int)
    saldo["rescisoes"] = saldo["rescisoes"].astype(int)
    saldo["saldo_liquido"] = saldo["admissoes"] - saldo["rescisoes"]
    saldo = saldo.sort_values(colunas_grupo).reset_index(drop=True)
    return saldo


def ranking_empresas(df_adm, df_fer, df_res):
    """
    Indicador 6: ranking de empresas por volume total de eventos (ADM + FER + RES).
    Retorna (ranking, detalhamento_por_tipo).
    """
    partes = []
    for tipo, df in [("ADM", df_adm), ("FER", df_fer), ("RES", df_res)]:
        contagem = df.groupby("empresa").size().reset_index(name="quantidade")
        contagem["tipo"] = tipo
        partes.append(contagem)

    detalhado = pd.concat(partes, ignore_index=True)

    ranking = (
        detalhado.groupby("empresa")["quantidade"]
        .sum()
        .reset_index(name="volume_total")
        .sort_values("volume_total", ascending=False)
        .reset_index(drop=True)
    )
    ranking.insert(0, "posicao", range(1, len(ranking) + 1))
    return ranking, detalhado


if __name__ == "__main__":
    # Teste rápido e isolado deste módulo, usando os dados reais já consolidados.
    from consolidacao import consolidar_tudo

    df_adm, df_fer, df_res = consolidar_tudo()
    df_adm = adicionar_periodo(df_adm)
    df_fer = adicionar_periodo(df_fer)
    df_res = adicionar_periodo(df_res)

    print("\n--- Volume de admissões por mês ---")
    print(volume_por_mes(df_adm).to_string(index=False))

    print("\n--- Volume total (ADM+FER+RES) por mês ---")
    total, _ = volume_total(df_adm, df_fer, df_res)
    print(total.to_string(index=False))

    print("\n--- Saldo líquido de movimentação por mês ---")
    print(saldo_liquido_movimentacao(df_adm, df_res).to_string(index=False))

    print("\n--- Ranking de empresas por volume total ---")
    ranking, _ = ranking_empresas(df_adm, df_fer, df_res)
    print(ranking.head(10).to_string(index=False))