from pathlib import Path
import zipfile 

PASTA_ORIGEM = Path(__file__).resolve().parent.parent / "dados" / "origem"

def extrair_todos_os_zips(pasta_origem: Path = PASTA_ORIGEM, pasta_destino: Path = PASTA_DESTINO) -> list[Path]:
    "Percorre todos os arquivos zip na pasta de origem e extrai seu conteúdo pra pasta de destino"
    pasta_destino.mkdir(parents=True, exist_ok=True)
    csvs_extraidos = [] 