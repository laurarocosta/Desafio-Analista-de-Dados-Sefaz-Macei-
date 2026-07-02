from pathlib import Path
import zipfile 

PASTA_ORIGEM = Path(__file__).resolve().parent.parent / "dados" / "origem"
PASTA_DESTINO = Path(__file__).resolve().parent.parent / "dados_extraidos"

def extrair_todos_os_zips(pasta_origem: Path = PASTA_ORIGEM, pasta_destino: Path = PASTA_DESTINO) -> list[Path]:
    "Percorre todos os arquivos zip na pasta de origem e extrai seu conteúdo pra pasta de destino"
    pasta_destino.mkdir(parents=True, exist_ok=True)
    csvs_extraidos = []     
    
    zips_encontrados = sorted(pasta_origem.rglob("*.zip"))

    if not zips_encontrados:
            raise FileNotFoundError(f"Nenhum .zip encontrado em {pasta_origem}")


    for caminho_zip in zips_encontrados:
        ano = caminho_zip.parent.name  # nome da subpasta = o ano, ex: "2020"
        pasta_ano = pasta_destino / ano
        pasta_ano.mkdir(parents=True, exist_ok=True)
