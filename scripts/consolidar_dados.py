from pathlib import Path
import pandas as pd
import re   

PASTA_EXTRAIDOS = Path(__file__).resolve().parent.parent / "dados_extraidos"
PASTA_SAIDA = Path(__file__).resolve().parent.parent / "dados_consolidados"
ARQUIVO_PARQUET = PASTA_SAIDA / "consolidado.parquet"

#Separador de função e subfunção 
PADRAO_FUNCAO = re.compile(r"^(\d{2}) - (.+)$")

CONTAS_AGREGADAS = {
    "Despesas Exceto Intraorçamentárias",
    "Despesas Intraorçamentárias",
} 

def ler_um_csv(caminho_csv: Path, ano: int) -> pd.DataFrame:
    df = pd.read_csv(
        caminho_csv,
        sep=";",
        skiprows=3,          # pula as 3 linhas de metadados (Exercício/Escopo/Tabela)
        encoding="latin-1",  # ISO-8859-1, senão acentos quebram
        decimal=",",         # vírgula é separador decimal no padrão BR
        thousands=".",
    )
    df["ano"] = ano
    return df

def classificar_conta(valor_conta: str) -> pd.Series:
    """Classifica a coluna `Conta` em: tipo_conta, codigo_funcao, funcao_nome,
    codigo_subfuncao, subfuncao_nome."""
    if valor_conta in CONTAS_AGREGADAS:
        return pd.Series(["total_agregado", None, None, None, None])

    if valor_conta.startswith("FU") and " - " in valor_conta:
        # ex: "FU10 - Demais Subfunções"
        codigo_funcao = valor_conta[2:4]
        return pd.Series(["demais_subfuncoes", codigo_funcao, None, None, valor_conta.split(" - ", 1)[1]])

    m_sub = PADRAO_SUBFUNCAO.match(valor_conta)
    if m_sub:
        cod_funcao, cod_sub, nome_sub = m_sub.groups()
        return pd.Series(["subfuncao", cod_funcao, None, f"{cod_funcao}.{cod_sub}", nome_sub])

    m_func = PADRAO_FUNCAO.match(valor_conta)
    if m_func:
        cod_funcao, nome_funcao = m_func.groups()
        return pd.Series(["funcao", cod_funcao, nome_funcao, None, None])

    return pd.Series(["outro", None, None, None, None])

def consolidar() -> pd.DataFrame:
    pastas_ano = sorted(p for p in PASTA_EXTRAIDOS.iterdir() if p.is_dir())
    if not pastas_ano:
        raise FileNotFoundError(
            f"Nada em {PASTA_EXTRAIDOS}. Rode antes o script 01_extrair_dados.py"
        )

    dataframes = []
    for pasta in pastas_ano:
        ano = int(pasta.name)
        csvs = list(pasta.glob("*.csv"))
        for csv in csvs:
            df_ano = ler_um_csv(csv, ano)
            dataframes.append(df_ano)
            print(f"[OK] {ano}: {len(df_ano):,} linhas lidas de {csv.name}")

    df = pd.concat(dataframes, ignore_index=True)
