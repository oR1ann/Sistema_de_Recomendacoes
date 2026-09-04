# Cozinha Consciente — Projeto Aplicado III

Sistema de recomendação híbrido de receitas que combina filtragem colaborativa e
filtragem baseada em conteúdo, com reordenação por índice nutricional e por
aproveitamento de ingredientes já disponíveis.

Universidade Presbiteriana Mackenzie — Tecnologia em Banco de Dados
Grupo: Ryan Rodrigues Pereira, Nour Hussein Barakat, Guilherme de Araújo Espírito Santo, André Cavina Oliveira

## Base de dados

`Food.com Recipes and Interactions` (Kaggle):
https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions

Baixe `RAW_recipes.csv` e `RAW_interactions.csv` e coloque em `data/raw/`.

## Como reproduzir

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.eda            # análise exploratória (Etapa 2)
python -m src.run_poc        # prova de conceito: treino + avaliação
```

Saídas em `data/processed/`: `eda_resumo.json`, `figuras/`, `poc_stats.json`,
`poc_metrics.csv`.

Para validar o pipeline sem os dados reais:
`python -m tools.make_synthetic` gera uma amostra com o mesmo esquema.
**Os números produzidos a partir dela não são resultados experimentais.**

## Estrutura

| Caminho | Função |
|---|---|
| `src/config.py` | parâmetros centrais (limiares, k-core, pesos do híbrido) |
| `src/nutrition.py` | decomposição do vetor nutricional e índice nutricional (FSA/OMS por 100 kcal) |
| `src/data_preparation.py` | limpeza, k-core, split temporal leave-one-out |
| `src/recommenders.py` | Popularidade, ItemKNN, PureSVD, TF-IDF de conteúdo e híbrido |
| `src/evaluate.py` | métricas de ranqueamento e métricas além da acurácia |
| `src/eda.py` | análise exploratória e figuras |
| `src/run_poc.py` | executa a prova de conceito de ponta a ponta |
| `tools/make_synthetic.py` | amostra sintética para teste de integridade |
| `app/` | protótipo (Etapa 3) |
| `extensao/` | cartilha e registros da ação extensionista (Etapa 4) |

## Parâmetros da prova de conceito

RANDOM_STATE=42 · feedback positivo: nota ≥ 4 · k-core 5 em usuários e itens ·
split temporal leave-one-out · avaliação com 1 positivo + 99 negativos amostrados ·
k=10 · SVD 64 fatores · ItemKNN 200 vizinhos · TF-IDF min_df=5, n-gramas (1,2) ·
pesos do híbrido SVD 0,5 / ItemKNN 0,3 / conteúdo 0,2 · λ nutricional 0,30.
