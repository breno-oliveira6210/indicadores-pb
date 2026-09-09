import os
import re
from pathlib import Path

# Caminho calculado a partir da localização deste arquivo, não do diretório
# de onde o terminal foi aberto — assim funciona igual rodando de qualquer lugar.
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "data" / "raw"

# Padrão esperado agora: "adm-01-26.xls", "fer-12-27.xls", "res-03-26.xls"
# (tipo, hífen, mês com 2 dígitos, hífen, ano com 2 dígitos, .xls)
PADRAO_NOME = re.compile(r"^(ADM|FER|RES)-(\d{2})-(\d{2})\.xls$", re.IGNORECASE)


def listar_arquivos():
    """
    Percorre a pasta data/raw (e subpastas de ano) e retorna uma lista
    de dicionários com informações extraídas do NOME de cada arquivo.
    Arquivos fora do padrão são reportados separadamente.
    """
    arquivos_validos = []
    arquivos_invalidos = []

    if not PASTA_DADOS.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {PASTA_DADOS.resolve()}")

    for caminho in PASTA_DADOS.rglob("*.xls"):
        nome = caminho.name
        match = PADRAO_NOME.match(nome)

        if match:
            tipo, mes_str, ano_str = match.groups()
            arquivos_validos.append({
                "arquivo": nome,
                "caminho_completo": str(caminho),
                "mes": int(mes_str),
                "ano": 2000 + int(ano_str),  # 26 -> 2026
                "tipo": tipo.upper(),
            })
        else:
            arquivos_invalidos.append(nome)

    return arquivos_validos, arquivos_invalidos


if __name__ == "__main__":
    validos, invalidos = listar_arquivos()

    print(f"\n✅ {len(validos)} arquivo(s) identificado(s) corretamente:\n")
    for item in validos:
        print(f"  {item['arquivo']} -> mês={item['mes']:02d}, ano={item['ano']}, tipo={item['tipo']}")

    if invalidos:
        print(f"\n⚠️  {len(invalidos)} arquivo(s) fora do padrão esperado:\n")
        for nome in invalidos:
            print(f"  {nome}")