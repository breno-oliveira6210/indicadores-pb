from ingestion import listar_arquivos
from cleaning import limpar_arquivo

validos, invalidos = listar_arquivos()

for item in validos:
    df_limpo = limpar_arquivo(
        caminho=item["caminho_completo"],
        tipo=item["tipo"],
        mes=item["mes"],
        ano=item["ano"],
    )
    print(f"\n{item['arquivo']} -> {len(df_limpo)} linhas após limpeza")
    print(df_limpo.head(2).to_string())