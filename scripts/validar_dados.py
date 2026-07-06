from pathlib import Path
import sys
import pandas as pd

PARQUET = Path(__file__).resolve().parent.parent / "dados_consolidados" / "consolidado.parquet"

def check(nome: str, condicao: bool, detalhe: str = "") -> bool:
    status = "PASSOU" if condicao else "FALHOU"
    print(f"[{status}] {nome}" + (f" — {detalhe}" if detalhe else ""))
    return condicao


def main() -> int:
    if not PARQUET.exists():
        print(f"ERRO: {PARQUET} não existe. Rode antes o consolidar_dados.py")
        return 1

    df = pd.read_parquet(PARQUET)
    resultados = []

    # 1. Volume esperado: 6 anos consolidados
    anos = sorted(df["ano"].unique())
    resultados.append(check(
        "6 anos presentes (2020-2025)",
        anos == [2020, 2021, 2022, 2023, 2024, 2025],
        f"anos encontrados: {anos}",
    ))
    # 2. 26 capitais em cada ano completo (2020-2024)
    capitais_por_ano = df[df["ano"] <= 2024].groupby("ano")["capital"].nunique()
    resultados.append(check(
        "26 capitais em cada ano de 2020 a 2024",
        (capitais_por_ano == 26).all(),
        f"mín/máx: {capitais_por_ano.min()}/{capitais_por_ano.max()}",
    ))
    
    # 3. Nenhum valor nulo após conversão numérica
    nulos = df["valor"].isna().sum()
    resultados.append(check(
        "Zero nulos na coluna valor",
        nulos == 0,
        f"nulos: {nulos}",
    ))