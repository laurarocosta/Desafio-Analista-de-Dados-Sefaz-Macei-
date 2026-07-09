from pathlib import Path
import duckdb
import matplotlib.pyplot as plt
import numpy as np

PARQUET = Path(__file__).resolve().parent.parent / "dados_consolidados" / "consolidado.parquet"
PASTA_GRAFICOS = Path(__file__).resolve().parent.parent / "analise" / "graficos"
PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW finbra AS SELECT * FROM read_parquet('{PARQUET}')")

plt.rcParams["figure.dpi"] = 110
COR_MACEIO = "#e61174"
COR_OUTRAS = "#4c72b0"
# Paleta Okabe-Ito, segura para as formas mais comuns de daltonismo
# (deuteranopia/protanopia não distinguem vermelho de verde, mas
# distinguem bem azul de laranja).
COR_ACIMA_MEDIA = "#0072B2"   # azul
COR_ABAIXO_MEDIA = "#E69F00"  # laranja


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

fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(df1["capital"], df1["taxa"], color=cores_destacando_maceio(df1["capital"]))
ax.set_xlabel("Taxa de execução financeira (%) — Pago / Empenhado")
ax.set_title("Taxa de execução financeira geral por capital — 2024")
ax.set_xlim(0, 100)
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


# 3) Subfunções que concentram o gasto em Saúde - Maceió, 2024
df3 = con.execute("""
    SELECT subfuncao_nome, SUM(valor) AS total_pago
    FROM finbra
    WHERE ano = 2024 AND capital = 'Maceió'
      AND codigo_funcao = '10' AND tipo_conta IN ('subfuncao', 'demais_subfuncoes')
      AND estagio_despesa = 'Despesas Pagas'
    GROUP BY subfuncao_nome ORDER BY total_pago ASC
""").df()
df3["total_pago_mi"] = df3["total_pago"] / 1_000_000

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(df3["subfuncao_nome"], df3["total_pago_mi"], color=COR_OUTRAS)
ax.set_xlabel("Total pago em 2024 (R$ milhões)")
ax.set_title("Onde Maceió gasta em Saúde — por subfunção (2024)")
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "03_subfuncoes_saude_maceio.png")
plt.close()
print("[OK] 03_subfuncoes_saude_maceio.png")


# 4) Maceió vs média das capitais - diferença na taxa de execução por função
df4 = con.execute("""
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
        FROM base WHERE empenhado > 0
    ),
    agregado AS (
        SELECT funcao_nome,
               MAX(CASE WHEN capital = 'Maceió' THEN taxa_execucao END) AS maceio,
               AVG(taxa_execucao) AS media_capitais
        FROM taxa GROUP BY funcao_nome
    )
    SELECT funcao_nome, maceio - media_capitais AS diferenca_pp
    FROM agregado WHERE maceio IS NOT NULL
    ORDER BY diferenca_pp ASC
""").df()

cores4 = [COR_ACIMA_MEDIA if v >= 0 else COR_ABAIXO_MEDIA for v in df4["diferenca_pp"]]
fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(df4["funcao_nome"], df4["diferenca_pp"], color=cores4)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Diferença em pontos percentuais (Maceió - média das capitais)")
ax.set_title("Maceió vs média das capitais — taxa de execução por função (2024)")
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "04_maceio_vs_media_por_funcao.png")
plt.close()
print("[OK] 04_maceio_vs_media_por_funcao.png")

# 5) Prévia 2025: variação do pago per capita nas 11 capitais declarantes
# (painel balanceado — mesmas capitais nos dois anos; Maceió não declarou 2025)
df5 = con.execute("""
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
        FROM base GROUP BY capital
    )
    SELECT capital, 100.0 * (pc_2025 - pc_2024) / pc_2024 AS variacao
    FROM pivotado ORDER BY variacao ASC
""").df()

cores5 = [COR_ACIMA_MEDIA if v >= 0 else COR_ABAIXO_MEDIA for v in df5["variacao"]]
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(df5["capital"], df5["variacao"], color=cores5)
ax.axvline(0, color="black", linewidth=0.8)
# margem extra nas pontas para os rótulos não cortarem na borda
vmin, vmax = df5["variacao"].min(), df5["variacao"].max()
ax.set_xlim(vmin - 2.5, vmax + 2.5)
ax.set_xlabel("Variação do total pago per capita, 2024 → 2025 (%)")
ax.set_title("Prévia 2025 (painel balanceado): apenas as 11 capitais que declararam\n(valores nominais; Maceió não está entre as declarantes)")
for i, v in enumerate(df5["variacao"]):
    ax.text(v + (0.15 if v >= 0 else -0.15), i, f"{v:+.1f}%", va="center",
            ha="left" if v >= 0 else "right", fontsize=8)
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "05_previa_2025_painel_balanceado.png")
plt.close()
print("[OK] 05_previa_2025_painel_balanceado.png")

# 6) Educação por subfunção: Maceió vs média das capitais
# Mostra ONDE trava a execução de Educação em Maceió
df6 = con.execute("""
    WITH base AS (
        SELECT capital, subfuncao_nome,
               SUM(CASE WHEN estagio_despesa = 'Despesas Empenhadas' THEN valor END) AS empenhado,
               SUM(CASE WHEN estagio_despesa = 'Despesas Pagas' THEN valor END) AS pago
        FROM finbra
        WHERE ano = 2024 AND codigo_funcao = '12' AND tipo_conta = 'subfuncao'
        GROUP BY capital, subfuncao_nome
    ),
    taxa AS (
        SELECT capital, subfuncao_nome, 100.0 * pago / NULLIF(empenhado, 0) AS taxa
        FROM base WHERE empenhado > 0
    )
    SELECT subfuncao_nome,
           MAX(CASE WHEN capital = 'Maceió' THEN taxa END) AS maceio,
           AVG(taxa) AS media
    FROM taxa GROUP BY subfuncao_nome
    HAVING maceio IS NOT NULL
    ORDER BY maceio ASC
""").df()

y = np.arange(len(df6))
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(y + 0.2, df6["maceio"], height=0.4, color=COR_MACEIO, label="Maceió")
ax.barh(y - 0.2, df6["media"], height=0.4, color=COR_OUTRAS, label="Média das capitais")
ax.set_yticks(y)
ax.set_yticklabels(df6["subfuncao_nome"])
ax.set_xlabel("Taxa de execução (%) — Pago / Empenhado")
ax.set_title("Educação por subfunção: onde trava a execução de Maceió (2024)")
ax.legend(loc="lower right")
ax.set_xlim(0, 105)
for yi, (m, md) in enumerate(zip(df6["maceio"], df6["media"])):
    ax.text(m + 1, yi + 0.2, f"{m:.1f}%", va="center", fontsize=8)
    ax.text(md + 1, yi - 0.2, f"{md:.1f}%", va="center", fontsize=8, color="#555")
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "06_educacao_subfuncoes_maceio_vs_media.png")
plt.close()
print("[OK] 06_educacao_subfuncoes_maceio_vs_media.png")


# 7) Deflação por IPCA: a evolução do per capita de Saúde é real, ou é
# em boa parte inflação? Índices oficiais do IPCA (IBGE/BCB), acumulado
# anual: 2020=4,52% | 2021=10,06% | 2022=5,79% | 2023=4,62% | 2024=4,83%.
# Convertendo tudo para poder de compra de dez/2024 (ano-base), pela
# multiplicação em cadeia da inflação de cada ano até 2024.
IPCA_ANUAL = {2020: 0.0452, 2021: 0.1006, 2022: 0.0579, 2023: 0.0462, 2024: 0.0483}


def fator_deflator_para_2024(ano: int) -> float:
    """Fator que converte R$ do ano informado em R$ de dez/2024
    (poder de compra), multiplicando a inflação acumulada de cada
    ano seguinte até 2024, em cadeia."""
    fator = 1.0
    for a in range(ano + 1, 2025):
        fator *= (1 + IPCA_ANUAL[a])
    return fator


df7 = df2.copy()  # reaproveita a consulta de evolução de Saúde per capita (nominal)
df7["deflator"] = df7["ano"].apply(fator_deflator_para_2024)
df7["maceio_real"] = df7["maceio"] * df7["deflator"]
df7["media_real"] = df7["media_capitais"] * df7["deflator"]

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(df7["ano"], df7["maceio"], marker="o", linestyle="--", color=COR_MACEIO,
        alpha=0.45, label="Maceió (nominal)")
ax.plot(df7["ano"], df7["maceio_real"], marker="o", color=COR_MACEIO,
        label="Maceió (a preços de dez/2024)")
ax.plot(df7["ano"], df7["media_capitais"], marker="o", linestyle="--", color=COR_OUTRAS,
        alpha=0.45, label="Média das capitais (nominal)")
ax.plot(df7["ano"], df7["media_real"], marker="o", color=COR_OUTRAS,
        label="Média das capitais (a preços de dez/2024)")
ax.set_ylabel("Gasto per capita pago em Saúde (R$)")
ax.set_title("Saúde per capita: valores nominais vs. deflacionados pelo IPCA\n(2020-2024, a preços de dezembro de 2024)")
ax.legend(fontsize=8, loc="upper left")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "07_saude_percapita_deflacionado_ipca.png")
plt.close()
print("[OK] 07_saude_percapita_deflacionado_ipca.png")

print("\nTodos os gráficos foram salvos em", PASTA_GRAFICOS)