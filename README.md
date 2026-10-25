# Cozinha Consciente — Projeto Aplicado III

Sistema de recomendação híbrido de receitas que combina filtragem colaborativa e filtragem baseada em conteúdo, com reordenação por índice nutricional e por aproveitamento de ingredientes já disponíveis.

Universidade Presbiteriana Mackenzie — Tecnologia em Banco de Dados
Grupo: Ryan Rodrigues Pereira, Nour Hussein Barakat, Guilherme de Araújo Espírito Santo, André Cavina Oliveira

## Base de dados

`Food.com Recipes and Interactions` (Kaggle): https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions

Baixe `RAW_recipes.csv` e `RAW_interactions.csv` e coloque em `data/raw/`.

## Como reproduzir

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.eda            # análise exploratória (Etapa 2)
python -m src.run_poc        # treino e avaliação com os parâmetros de src/config.py (configuração ajustada)
python -m src.tuning         # ajuste na validação e reavaliação no teste (Etapa 3, ~3 min)
```

Saídas em `data/processed/`: `eda_resumo.json`, `figuras/`, `poc_stats.json`, `poc_metrics.csv` e as tabelas `tuning_*.csv`.
As tabelas e figuras da Etapa 3 usadas no documento estão versionadas em `docs/resultados_etapa3/`.

Para validar o pipeline sem os dados reais: `python -m tools.make_synthetic` gera uma amostra com o mesmo esquema. **Os números produzidos a partir dela não são resultados experimentais.**

## Estrutura

| Caminho | Função |
|---|---|
| `src/config.py` | parâmetros centrais (configuração ajustada na Etapa 3) |
| `src/nutrition.py` | decomposição do vetor nutricional e índice nutricional (FSA/OMS por 100 kcal) |
| `src/data_preparation.py` | limpeza, k-core, split temporal leave-one-out |
| `src/recommenders.py` | Popularidade, ItemKNN, PureSVD, TF-IDF de conteúdo e híbrido |
| `src/evaluate.py` | protocolo de avaliação e métricas (ranqueamento e além da acurácia) |
| `src/tuning.py` | ajuste de hiperparâmetros na validação e reavaliação no teste (Etapa 3) |
| `src/eda.py` | análise exploratória e figuras |
| `src/run_poc.py` | treino e avaliação de ponta a ponta com `src/config.py` |
| `notebooks/02_poc_modelos.ipynb` | prova de conceito com os parâmetros iniciais (Etapa 2, protocolo corrigido) |
| `notebooks/03_ajuste_e_reavaliacao.ipynb` | análise dos resultados preliminares, ajuste e reavaliação (Etapa 3) |
| `docs/resultados_etapa3/` | tabelas, configuração final e figuras da Etapa 3 |
| `docs/fluxograma_metodologia.png` | Figura 1 do documento (visão geral da metodologia) |
| `tools/make_synthetic.py` | amostra sintética para teste de integridade |
| `tools/make_flowchart.py`, `tools/build_nbs_etapa3.py` | geram o fluxograma e os notebooks da Etapa 3 |
| `app/` | protótipo (Etapa 4) |
| `extensao/` | cartilha e registros da ação extensionista (Etapa 4) |

## Parâmetros (configuração ajustada na validação — Etapa 3)

RANDOM_STATE=42 · feedback positivo: nota ≥ 4 · k-core 5 em usuários e itens · split temporal leave-one-out · avaliação com 1 positivo + 99 negativos em posição aleatória · k=10 · SVD 32 fatores · ItemKNN 500 vizinhos · TF-IDF min_df=5, n-gramas (1,2), até 50.000 termos · normalização z-score · pesos do híbrido popularidade 0,6 / ItemKNN 0,1 / SVD 0,1 / conteúdo 0,2 · λ nutricional 0,35.

Configuração inicial (Etapa 2): SVD 64 fatores, ItemKNN 200 vizinhos, pesos SVD 0,5 / ItemKNN 0,3 / conteúdo 0,2, normalização min-max, λ 0,30.
