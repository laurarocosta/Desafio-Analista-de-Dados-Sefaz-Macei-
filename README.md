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
## Critério 1 — Tratamento dos dados

```python
pd.read_csv(caminho, sep=";", skiprows=3, encoding="latin-1",
            decimal=",", thousands=".")
```

Antes de escrever o código, **inspecionei o arquivo bruto** com
`open(..., encoding="latin-1")` para confirmar cada uma dessas características
(as 3 linhas de metadados, o cabeçalho real na 4ª linha, o `;` e a vírgula
decimal) em vez de confiar apenas no README.

**Dados incompletos (2025):** a primeira coisa que o script de consolidação
imprime é a contagem de capitais por ano:

| Ano | Capitais |
|---|---|
| 2020–2024 | 26 |
| 2025 | **11** |
