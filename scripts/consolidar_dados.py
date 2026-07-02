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
