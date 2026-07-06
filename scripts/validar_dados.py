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
       # 4. Nenhuma linha ficou sem classificação na coluna Conta
    if "tipo_conta" in df.columns:
        outros = (df["tipo_conta"] == "outro").sum()
        resultados.append(check(
            "Classificação de Conta cobriu 100% das linhas",
            outros == 0,
            f"linhas 'outro': {outros}",
        ))

    # 5. Fechamento contábil: soma das subfunções = total da função
    # (testado na função Saúde de Maceió em 2024 — se a classificação
    # estivesse errada, essa soma não bateria)
    filtro = (df["ano"] == 2024) & (df["capital"] == "Maceió") & (df["codigo_funcao"] == "10") & (df["estagio_despesa"] == "Despesas Pagas")
    total_funcao = df[filtro & (df["tipo_conta"] == "funcao")]["valor"].sum()
    total_subfuncoes = df[filtro & (df["tipo_conta"].isin(["subfuncao", "demais_subfuncoes"]))]["valor"].sum()
    diferenca = abs(total_funcao - total_subfuncoes)
    resultados.append(check(
        "Fechamento: soma das subfunções = total da função (Saúde/Maceió/2024)",
        diferenca < 1.0,  # tolerância de R$ 1 para arredondamento de ponto flutuante
        f"diferença: R$ {diferenca:.2f}",
    ))

    # 6. Sem duplicatas exatas (mesma capital, ano, conta e estágio duplicados)
    duplicatas = df.duplicated(subset=["ano", "capital", "conta_original", "estagio_despesa"]).sum()
    resultados.append(check(
        "Sem linhas duplicadas (capital + ano + conta + estágio)",
        duplicatas == 0,
        f"duplicatas: {duplicatas}",
    ))

    print()
    if all(resultados):
        print(f"✔ Todas as {len(resultados)} validações passaram. Base íntegra.")
        return 0
    falhas = len(resultados) - sum(resultados)
    print(f"✘ {falhas} validação(ões) falhou(aram). Revise a consolidação.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
