from pathlib import Path
import zipfile 

PASTA_ORIGEM = Path(__file__).resolve().parent.parent / "dados_compactos"
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

        with zipfile.ZipFile(caminho_zip) as z:
            for nome_interno in z.namelist():
                z.extract(nome_interno, pasta_ano)
                csvs_extraidos.append(pasta_ano / nome_interno)

        print(f"[OK] {ano}: extraído {caminho_zip.name} -> {pasta_ano}/")

    return csvs_extraidos


if __name__ == "__main__":
    arquivos = extrair_todos_os_zips()
    print(f"\nTotal de arquivos extraídos: {len(arquivos)}")


