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

ig, ax = plt.subplots(figsize=(8, 9))
ax.barh(df1["capital"], df1["taxa"], color=cores_destacando_maceio(df1["capital"]))
ax.set_xlabel("Taxa de execução financeira (%) — Pago / Empenhado")
ax.set_title("Taxa de execução financeira geral por capital — 2024")
ax.set_xlim(80, 100)
for i, v in enumerate(df1["taxa"]):
    ax.text(v + 0.1, i, f"{v:.1f}%", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "01_taxa_execucao_geral_2024.png")
plt.close()
print("[OK] 01_taxa_execucao_geral_2024.png")


# 2) Evolução do gasto per capita PAGO em Saúde: Maceió vs média das capitais
df2 = con.execute("""
    WITH por_capital AS (
        SELECT ano, capital, populacao,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE tipo_conta = 'funcao' AND codigo_funcao = '10' AND ano BETWEEN 2020 AND 2024
        GROUP BY ano, capital, populacao
    )
    SELECT ano,
           MAX(CASE WHEN capital = 'Maceió' THEN pago / populacao END) AS maceio,
           AVG(pago / populacao) AS media_capitais
    FROM por_capital GROUP BY ano ORDER BY ano
""").df()

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(df2["ano"], df2["maceio"], marker="o", color=COR_MACEIO, label="Maceió")
ax.plot(df2["ano"], df2["media_capitais"], marker="o", color=COR_OUTRAS, label="Média das 26 capitais")
ax.set_ylabel("Gasto per capita pago em Saúde (R$)")
ax.set_title("Gasto per capita em Saúde: Maceió vs média das capitais (2020-2024)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "02_evolucao_saude_percapita.png")
plt.close()
print("[OK] 02_evolucao_saude_percapita.png")

