from pathlib import Path
import duckdb

PARQUET = Path(__file__).resolve().parent.parent / "dados_consolidados" / "consolidado.parquet"

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

# 6) Em quais funções as capitais mais "empurram" gasto para Restos a Pagar
# (Empenhado - Pago, em % do empenhado), média entre capitais, 2024
rodar(
    "6. Funções com maior % do orçamento empenhado que virou 'restos a pagar' (média das capitais, 2024)",
    """
    WITH base AS (
        SELECT capital, funcao_nome,
               SUM(CASE WHEN estagio_despesa = 'Despesas Empenhadas' THEN valor END) AS empenhado,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE ano = 2024 AND tipo_conta = 'funcao'
        GROUP BY capital, funcao_nome
    ),
    taxa AS (
        SELECT capital, funcao_nome,
               100.0 * (empenhado - pago) / NULLIF(empenhado, 0) AS pct_nao_pago
        FROM base
        WHERE empenhado > 0
    )
    SELECT funcao_nome, ROUND(AVG(pct_nao_pago), 1) AS media_pct_nao_pago_entre_capitais
    FROM taxa
    GROUP BY funcao_nome
    ORDER BY media_pct_nao_pago_entre_capitais DESC
    """,
    n=27,
)

# 7) Onde Maceió se destaca: taxa de execução de Maceió vs média das capitais,
# por função, 2024 -- ordenado pela maior diferença (positiva = Maceió melhor)
rodar(
    "7. Maceió vs média das capitais - diferença na taxa de execução por função (2024)",
    """
    WITH base AS (
        SELECT capital, funcao_nome,
               SUM(CASE WHEN estagio_despesa = 'Despesas Empenhadas' THEN valor END) AS empenhado,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE ano = 2024 AND tipo_conta = 'funcao'
        GROUP BY capital, funcao_nome
    ),
    taxa AS (
        SELECT capital, funcao_nome, 100.0 * pago / NULLIF(empenhado, 0) AS taxa_execucao
        FROM base
        WHERE empenhado > 0
    ),
    agregado AS (
        SELECT funcao_nome,
               MAX(CASE WHEN capital = 'Maceió' THEN taxa_execucao END) AS maceio,
               AVG(taxa_execucao) AS media_capitais
        FROM taxa
        GROUP BY funcao_nome
    )
    SELECT funcao_nome, ROUND(maceio, 1) AS maceio_pct, ROUND(media_capitais, 1) AS media_capitais_pct,
           ROUND(maceio - media_capitais, 1) AS diferenca_pp
    FROM agregado
    WHERE maceio IS NOT NULL
    ORDER BY diferenca_pp DESC
    """,
    n=27,
)

# 8) Prévia de 2025 SEM distorcer a amostra: painel balanceado.
# Em vez de descartar 2025 por completo (só 11 de 26 capitais reportaram),
# comparamos 2024 vs 2025 APENAS nas mesmas 11 capitais presentes nos dois anos.
# Assim a variação reflete mudança real de gasto, não mudança de amostra.
# Atenção: Maceió NÃO está entre as declarantes de 2025, então esta prévia
# nada diz sobre Maceió — apenas sobre a tendência do painel.
rodar(
    "8. Prévia 2025 (painel balanceado): total pago per capita, mesmas 11 capitais em 2024 e 2025",
    """
    WITH declarantes_2025 AS (
        SELECT DISTINCT capital FROM finbra WHERE ano = 2025
    ),
    base AS (
        SELECT f.ano, f.capital, f.populacao,
               SUM(CASE WHEN f.estagio_despesa = 'Despesas Pagas' THEN f.valor END) AS pago
        FROM finbra f
        JOIN declarantes_2025 d USING (capital)
        WHERE f.ano IN (2024, 2025)
          AND f.conta_original = 'Despesas Exceto Intraorçamentárias'
        GROUP BY f.ano, f.capital, f.populacao
    ),
    pivotado AS (
        SELECT capital,
               MAX(CASE WHEN ano = 2024 THEN pago / populacao END) AS pc_2024,
               MAX(CASE WHEN ano = 2025 THEN pago / populacao END) AS pc_2025
        FROM base
        GROUP BY capital
    )
    SELECT capital,
           ROUND(pc_2024, 2) AS pago_per_capita_2024,
           ROUND(pc_2025, 2) AS pago_per_capita_2025,
           ROUND(100.0 * (pc_2025 - pc_2024) / pc_2024, 1) AS variacao_pct
    FROM pivotado
    ORDER BY variacao_pct DESC
    """,
    n=15,
)

print("\n\nAnálise concluída.")

# 8) Prévia de 2025 SEM distorcer a amostra: painel balanceado.
# Em vez de descartar 2025 por completo (só 11 de 26 capitais reportaram),
# comparamos 2024 vs 2025 APENAS nas mesmas 11 capitais presentes nos dois anos.
# Assim a variação reflete mudança real de gasto, não mudança de amostra.
# Atenção: Maceió NÃO está entre as declarantes de 2025, então esta prévia
# nada diz sobre Maceió — apenas sobre a tendência do painel.
rodar(
    "8. Prévia 2025 (painel balanceado): total pago per capita, mesmas 11 capitais em 2024 e 2025",
    """
    WITH declarantes_2025 AS (
        SELECT DISTINCT capital FROM finbra WHERE ano = 2025
    ),
    base AS (
        SELECT f.ano, f.capital, f.populacao,
               SUM(CASE WHEN f.estagio_despesa = 'Despesas Pagas' THEN f.valor END) AS pago
        FROM finbra f
        JOIN declarantes_2025 d USING (capital)
        WHERE f.ano IN (2024, 2025)
          AND f.conta_original = 'Despesas Exceto Intraorçamentárias'
        GROUP BY f.ano, f.capital, f.populacao
    ),
    pivotado AS (
        SELECT capital,
               MAX(CASE WHEN ano = 2024 THEN pago / populacao END) AS pc_2024,
               MAX(CASE WHEN ano = 2025 THEN pago / populacao END) AS pc_2025
        FROM base
        GROUP BY capital
    )
    SELECT capital,
           ROUND(pc_2024, 2) AS pago_per_capita_2024,
           ROUND(pc_2025, 2) AS pago_per_capita_2025,
           ROUND(100.0 * (pc_2025 - pc_2024) / pc_2024, 1) AS variacao_pct
    FROM pivotado
    ORDER BY variacao_pct DESC
    """,
    n=15,
)

print("\n\nAnálise concluída.")
