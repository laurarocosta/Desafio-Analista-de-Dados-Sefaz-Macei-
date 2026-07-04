# Minha solução — Desafio Analista de Dados | Sefaz Maceió

Este documento descreve **como resolvi o desafio**, as **decisões técnicas** de
cada etapa

---

## Como rodar do zero (reprodutibilidade)

```bash
# 1. Instalar as dependências
pip install -r requirements.txt

# 2. Rodar os scripts na ordem
python scripts/extrair_dados.py
python scripts/consolidar_dados.py
python scripts/analise.py
python scripts/gerar_graficos.py
```

O relatório final com os insights está em `analise/relatorio_analise.md`.
Os gráficos ficam em `analise/graficos/`.

## Estrutura do repositório

```
.
├── dados_compactos/          # dados originais do desafio (intocados)
├── dados_extraidos/          # CSVs extraídos dos zips (gerado pelo script 1)
├── dados_consolidados/
│   └── consolidado.parquet   # tabela consolidada dos 6 anos
├── scripts/
│   ├── extrair_dados.py      # Passo 1
│   ├── consolidar_dados.py   # Passos 2 e 3
│   ├── analise.py            # Passo 4 (consultas SQL via DuckDB)
│   └── gerar_graficos.py     # Passo 4 (visualizações)
├── analise/
│   ├── relatorio_analise.md  # Passo 4: insights e conclusões
│   └── graficos/             # 5 PNGs gerados
├── requirements.txt         
└── README.md                 # este arquivo
```

---

## Critério 1 — Tratamento dos dados

```python
pd.read_csv(
    caminho,
    sep=";",            # separador é ponto e vírgula, não vírgula
    skiprows=3,         # as 3 primeiras linhas são metadados, não dados
    encoding="latin-1", # encoding antigo — sem isso os acentos quebram
    decimal=",",        # padrão brasileiro: vírgula como decimal
    thousands=".",
)
```

**Dados incompletos (2025):** logo na primeira análise verifiquei quantas
capitais reportaram por ano. 2025 tem apenas 11 das 26 capitais — menos da
metade. Por isso 2025 foi excluído das comparações gerais. Os dados estão
preservados no Parquet, mas não entram nos rankings nem nas séries temporais.
A exceção é o painel balanceado da análise 8, que compara 2024 × 2025 apenas
dentro das mesmas 11 capitais declarantes.

**Dupla contagem:** a coluna `Conta` tem linhas que são totais das outras.
`"Despesas Exceto Intraorçamentárias"` é a soma de todas as funções, se
somada junto com Saúde, Educação etc., cada real seria contado duas vezes.
Classifiquei cada linha com `tipo_conta` para filtrar explicitamente nas
queries.

## Critério 2 — Qualidade do código

- Scripts organizados por etapa do desafio, com comentários explicando cada
  decisão.
- Caminhos derivados de `Path(__file__)` — o projeto roda em qualquer máquina
  sem precisar ajustar nenhum caminho manualmente.
- Busca por padrão `*.zip` em vez de nome fixo — necessário porque o arquivo
  de 2020 tem um `(1)` no nome que os outros anos não têm (ver dificuldades).
- `requirements.txt` com as dependências necessárias.
- Consultas analíticas em SQL via DuckDB — mais legível que pivots em pandas
  para as agregações condicionais de Empenhado × Pago.

## Critério 3 — Análise e insights


O foco do desafio — **Empenhado × Pago por função, comparando capitais** —
foi respondido com a Taxa de Execução Financeira (Pago ÷ Empenhado × 100).
Principais achados:

1. **Maceió tem execução geral de 92,4% em 2024** (18ª de 26) — mediana, mas
   a média esconde grandes diferenças por função.
2. **Em Saúde, Maceió executa bem**: 97,4%, 5ª melhor entre as capitais. O
   gasto per capita convergiu para a média das capitais a partir de 2023,
   depois de ficar ~15% abaixo em 2020-2022.
3. **Em Educação, o quadro inverte**: execução de 85,5% (4ª pior) e per capita
   de R$ 716/hab — entre os 4 mais baixos das 26 capitais.
4. **Habitação é o maior outlier**: Maceió pagou apenas 30% do que empenhou
   em 2024, contra 85% da média das capitais (diferença de 55 pontos
   percentuais). É o achado mais relevante da análise.
5. **Padrão geral**: funções de obra (Habitação, Saneamento, Agricultura)
   concentram os maiores restos a pagar — coerente com o ciclo mais lento
   de obras e convênios em relação a despesas correntes.
6. **Por subfunção em Saúde**: 58,5% do pago em Maceió vai para Assistência
   Hospitalar e 27,5% para Atenção Básica.
7. **Prévia 2025 com painel balanceado**: comparei 2024 × 2025 apenas dentro
   das 11 capitais declarantes. Maceió não está entre elas — o que é, em si,
   um achado relevante para um órgão que depende da declaração no prazo.

## Critério 4 — Organização do repositório

- Separação clara entre dado bruto (`dados_compactos/`), intermediário
  (`dados_extraidos/`), consolidado (`dados_consolidados/`) e produto final
  (`analise/`).
- Decisão do Passo 3 documentada: escolhi **Parquet + DuckDB** juntos.
  Parquet resolve o armazenamento (arquivo tipado e comprimido, sem precisar
  repetir o parsing das 4 pegadinhas a cada análise). DuckDB resolve a
  consulta (lê o Parquet direto com SQL, sem carregar tudo em memória). Para
  este volume (~50 mil linhas), pandas daria conta, a escolha foi pela
  legibilidade das queries e por um fluxo que escala se a série crescer.

## Critério 5 — Processo público (commits)

O desenvolvimento foi feito em etapas, com commits por passo funcional:
extração → consolidação → análise → gráficos → documentação. Cada commit
reflete o que foi feito naquele momento, incluindo as correções de bug
descritas abaixo.

---

## Dificuldades 

**1. O arquivo de 2020 tem um nome diferente dos outros.**

Ao inspecionar a pasta `dados_compactos/`, percebi que o zip de 2020 tem
`(1)` no nome — `finbra_CAP_DespesasporFuncao(AnexoI-E) (1).zip` — enquanto
os outros 5 anos têm nomes sem esse sufixo.

Se eu tivesse buscado pelo nome exato, o script funcionaria para 2021-2025 e
quebraria (ou ignoraria silenciosamente) o arquivo de 2020. A solução foi
buscar por padrão `*.zip` com `rglob`, que encontra qualquer arquivo com
essa extensão independente do nome. O ano é extraído do nome da pasta pai
(`caminho.parent.name`), não do nome do arquivo.

Essa foi uma decisão de prevenção — percebi o problema antes de rodar —
mas só porque inspecionei os arquivos antes de escrever o código. Sem essa
checagem, o erro só apareceria nos resultados finais (ano de 2020 sumindo
dos rankings).

**2. A dupla contagem na coluna `Conta`.**

Ao explorar os dados, vi que a coluna `Conta` tem uma linha chamada
`"Despesas Exceto Intraorçamentárias"` que aparece em todas as capitais e
todos os anos. Só depois de entender o formato percebi que essa linha é a
**soma de todas as funções** — ou seja, se eu agrupasse tudo sem filtrar,
cada real entraria duas vezes: uma vez na função e outra no total.

O dado não avisa isso de nenhuma forma — parece uma linha normal. A solução
foi classificar cada linha da coluna `Conta` em categorias (`funcao`,
`subfuncao`, `total_agregado`, `demais_subfuncoes`) e filtrar explicitamente
nas queries.

**3. `PADRAO_SUBFUNCAO` não definido.**

Durante o desenvolvimento do `consolidar_dados.py`, o VS Code apontou que
a variável `PADRAO_SUBFUNCAO` era usada na função `classificar_conta` mas
nunca tinha sido definida no topo do arquivo, só existia `PADRAO_FUNCAO`.
Sem isso, o script quebraria com `NameError` na primeira linha real de dado
que passasse pelo `if`. Corrigi adicionando:

```python
PADRAO_SUBFUNCAO = re.compile(r"^(\d{2})\.(\d{3}) - (.+)$")
```

Junto com uma proteção para valores não-string no topo da função, caso
alguma linha viesse com `Conta` vazio ou NaN.

---

## Limitações conhecidas

- **Valores não deflacionados**: a série 2020-2024 mistura efeito de inflação
  com decisão de política pública. Idealmente os valores seriam corrigidos
  pelo IPCA antes de comparar anos.
- **População como estimativa**: o valor de `População` vem do próprio
  arquivo Siconfi — não confirmei se a metodologia é homogênea entre capitais
  ao longo dos anos.
- **Habitação sem investigação de causa**: os dados mostram *o quê* (30% de
  execução), mas não *por quê*. Responder isso exigiria cruzar com contratos,
  cronogramas de obra e restos a pagar de anos anteriores.
- **Subfunção detalhada só em Saúde**: o aprofundamento por subfunção foi
  feito como demonstração — Educação seria a candidata natural para continuar,
  dado o resultado encontrado.
