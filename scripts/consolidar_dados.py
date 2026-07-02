from pathlib import Path
import pandas as pd
import re   

PASTA_EXTRAIDOS = Path(__file__).resolve().parent.parent / "dados_extraidos"
PASTA_SAIDA = Path(__file__).resolve().parent.parent / "dados_consolidados"
ARQUIVO_PARQUET = PASTA_SAIDA / "consolidado.parquet"

#Separador de função e subfunção 
PADRAO_FUNCAO = re.compile(r"^(\d{2}) - (.+)$")
