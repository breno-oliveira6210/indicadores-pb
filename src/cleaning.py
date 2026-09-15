import pandas as pd


def _converter_data(serie):
    """Converte uma coluna de datas no formato dd/mm/aaaa para datetime."""
    return pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce", dayfirst=True)


def _converter_valor(serie):
    """Converte valores monetários com vírgula decimal (ex: '2862,91') para float."""
    if serie.dtype == object:
        return (
            serie.astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .replace("nan", None)
            .astype(float)
        )
    return serie.astype(float)


def limpar_admissoes(df, mes, ano):
    df = df.rename(columns={
        "codi_emp": "codigo_empresa",
        "cp_nome_emp": "empresa",
        "nome": "nome_funcionario",
        "admissao": "data_admissao",
        "data_nascimento": "data_nascimento",
        "salario": "salario",
        "situacao": "situacao",
    })

    df["data_admissao"] = _converter_data(df["data_admissao"])
    df["data_nascimento"] = _converter_data(df["data_nascimento"])
    df["salario"] = _converter_valor(df["salario"])

    df["mes_referencia"] = mes
    df["ano_referencia"] = ano
    df["tipo"] = "ADM"

    colunas_finais = [
        "empresa", "codigo_empresa", "nome_funcionario",
        "data_admissao", "salario", "situacao",
        "mes_referencia", "ano_referencia", "tipo",
    ]
    return df[colunas_finais]


def limpar_ferias(df, mes, ano):
    df = df.rename(columns={
        "codi_emp": "codigo_empresa",
        "sq_nome_emp": "empresa",
        "nome": "nome_funcionario",
        "inicio_gozo": "data_inicio_gozo",
        "fim_gozo": "data_fim_gozo",
        "valor_remuneracao": "valor_remuneracao",
    })

    df["data_inicio_gozo"] = _converter_data(df["data_inicio_gozo"])
    df["data_fim_gozo"] = _converter_data(df["data_fim_gozo"])
    df["valor_remuneracao"] = _converter_valor(df["valor_remuneracao"])

    df["mes_referencia"] = mes
    df["ano_referencia"] = ano
    df["tipo"] = "FER"

    colunas_finais = [
        "empresa", "codigo_empresa", "nome_funcionario",
        "data_inicio_gozo", "data_fim_gozo", "valor_remuneracao",
        "mes_referencia", "ano_referencia", "tipo",
    ]
    return df[colunas_finais]


def limpar_rescisoes(df, mes, ano):
    df = df.rename(columns={
        "codi_emp": "codigo_empresa",
        "sq_nome_emp": "empresa",
        "nome": "nome_funcionario",
        "admissao": "data_admissao",
        "demissao": "data_demissao",
        "salario": "salario",
        "motivo": "motivo_desligamento",
    })

    df["data_admissao"] = _converter_data(df["data_admissao"])
    df["data_demissao"] = _converter_data(df["data_demissao"])
    df["salario"] = _converter_valor(df["salario"])

    df["mes_referencia"] = mes
    df["ano_referencia"] = ano
    df["tipo"] = "RES"

    colunas_finais = [
        "empresa", "codigo_empresa", "nome_funcionario",
        "data_admissao", "data_demissao", "salario", "motivo_desligamento",
        "mes_referencia", "ano_referencia", "tipo",
    ]
    return df[colunas_finais]


LIMPADORES = {
    "ADM": limpar_admissoes,
    "FER": limpar_ferias,
    "RES": limpar_rescisoes,
}


def limpar_arquivo(caminho, tipo, mes, ano):
    """Lê e limpa um único arquivo, retornando o dataframe padronizado."""
    df_bruto = pd.read_excel(caminho, engine="xlrd")
    funcao_limpeza = LIMPADORES[tipo]
    return funcao_limpeza(df_bruto, mes, ano)