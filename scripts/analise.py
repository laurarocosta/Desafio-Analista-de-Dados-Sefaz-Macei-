from pathlib import Path
import duckdb

PARQUET = Path(__file__).resolve().parent.parent / "dados_consolidados" / "finbra_consolidado.parquet"

con = duckdb.connect()
con.execute(f"CREATE VIEW finbra AS SELECT * FROM read_parquet('{PARQUET}')")


def rodar(titulo: str, sql: str, n: int = 15):
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")
    print(con.execute(sql).df().head(n).to_string(index=False))


# 0) Checagem de completude por ano (quantas capitais reportaram)
rodar(
    "0. Completude dos dados por ano (nº de capitais que reportaram)",
    """
    SELECT ano, COUNT(DISTINCT capital) AS capitais
    FROM finbra
    GROUP BY ano
    ORDER BY ano
    """,
)

