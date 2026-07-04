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

# 3) Gasto per capita em Saúde e Educação - 2024, ranqueado
for cod, nome in [("10", "Saúde"), ("12", "Educação")]:
    rodar(
        f"3. Gasto PAGO per capita em {nome} (função {cod}) - 2024",
        f"""
        SELECT capital, populacao,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS total_pago,
               ROUND(SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) / populacao, 2) AS pago_per_capita
        FROM finbra
        WHERE ano = 2024 AND tipo_conta = 'funcao' AND codigo_funcao = '{cod}'
        GROUP BY capital, populacao
        ORDER BY pago_per_capita DESC
        """,
        n=30,
    )
    
    # 4) Evolução 2020-2024 de Maceió vs média das capitais, gasto per capita em Saúde
rodar(
    "4. Evolução do gasto per capita PAGO em Saúde: Maceió vs média das capitais (2020-2024)",
    """
    WITH por_capital AS (
        SELECT ano, capital, populacao,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE tipo_conta = 'funcao' AND codigo_funcao = '10' AND ano BETWEEN 2020 AND 2024
        GROUP BY ano, capital, populacao
    ),
    per_capita AS (
        SELECT ano, capital, pago / populacao AS pago_per_capita
        FROM por_capital
    )
    SELECT ano,
           ROUND(MAX(CASE WHEN capital = 'Maceió' THEN pago_per_capita END), 2) AS maceio,
           ROUND(AVG(pago_per_capita), 2) AS media_capitais
    FROM per_capita
    GROUP BY ano
    ORDER BY ano
    """,
)

# 5) Dentro de Saúde, quais subfunções concentram o gasto em Maceió (2024)?
rodar(
    "5. Subfunções que concentram o gasto PAGO em Saúde - Maceió, 2024",
    """
    SELECT subfuncao_nome,
           SUM(valor) AS total_pago,
           ROUND(100.0 * SUM(valor) / SUM(SUM(valor)) OVER (), 1) AS pct_do_total
    FROM finbra
    WHERE ano = 2024 AND capital = 'Maceió'
      AND codigo_funcao = '10' AND tipo_conta IN ('subfuncao', 'demais_subfuncoes')
      AND estagio_despesa = 'Despesas Pagas'
    GROUP BY subfuncao_nome
    ORDER BY total_pago DESC
    """,
)

