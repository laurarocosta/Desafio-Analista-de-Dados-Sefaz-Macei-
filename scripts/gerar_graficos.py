from pathlib import Path
import duckdb
import matplotlib.pyplot as plt

PARQUET = Path(__file__).resolve().parent.parent / "dados_consolidados" / "finbra_consolidado.parquet"
PASTA_GRAFICOS = Path(__file__).resolve().parent.parent / "analise" / "graficos"
PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW finbra AS SELECT * FROM read_parquet('{PARQUET}')")

plt.rcParams["figure.dpi"] = 110
COR_MACEIO = "#e61174"
COR_OUTRAS = "#4c72b0"

def cores_destacando_maceio(labels):
    return [COR_MACEIO if l == "Maceió" else COR_OUTRAS for l in labels]


# 1) Taxa de execução financeira geral por capital, 2024
df1 = con.execute("""
    WITH base AS (
        SELECT capital,
               SUM(CASE WHEN estagio_despesa = 'Despesas Empenhadas' THEN valor END) AS empenhado,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE ano = 2024 AND conta_original = 'Despesas Exceto Intraorçamentárias'
        GROUP BY capital
    )
    SELECT capital, 100.0 * pago / empenhado AS taxa
    FROM base ORDER BY taxa ASC
""").df()
