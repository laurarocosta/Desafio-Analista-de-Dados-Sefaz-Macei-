# Minha solução — Desafio Analista de Dados | Sefaz Maceió

Este documento descreve **como resolvi o desafio**, as **decisões técnicas** de
cada etapa.
---
## Como rodar do zero (reprodutibilidade)

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/01_extrair_dados.py     # Passo 1: descompacta dados_compactos/*.zip
python scripts/02_consolidar_dados.py  # Passos 2 e 3: consolida e salva Parquet
python scripts/03_analise.py           # Passo 4: indicadores (imprime no terminal)
python scripts/04_gerar_graficos.py    # Passo 4: gera os gráficos do relatório
```

