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

