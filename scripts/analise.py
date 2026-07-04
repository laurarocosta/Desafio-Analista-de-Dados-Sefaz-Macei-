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

# 2) Taxa de execução por função (Saúde e Educação), todas as capitais, 2024,
# ranqueado, mostrando onde Maceió está
for cod, nome in [("10", "Saúde"), ("12", "Educação")]:
    rodar(
        f"2. Taxa de execução em {nome} (função {cod}) por capital - 2024",
        f"""
        WITH base AS (
            SELECT capital,
                   SUM(CASE WHEN estagio_despesa = 'Despesas Empenhadas' THEN valor END) AS empenhado,
                   SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
            FROM finbra
            WHERE ano = 2024 AND tipo_conta = 'funcao' AND codigo_funcao = '{cod}'
            GROUP BY capital
        )
        SELECT capital, empenhado, pago,
               ROUND(100.0 * pago / empenhado, 1) AS taxa_execucao_pct
        FROM base
        ORDER BY taxa_execucao_pct DESC
        """,
        n=30,
    )
