# Cozinha Consciente — Projeto Aplicado III

Sistema de recomendação híbrido de receitas que combina filtragem colaborativa e filtragem baseada em conteúdo, com reordenação por índice nutricional e por aproveitamento de ingredientes já disponíveis.

Universidade Presbiteriana Mackenzie — Tecnologia em Banco de Dados
Grupo: Ryan Rodrigues Pereira, Nour Hussein Barakat, Guilherme de Araújo Espírito Santo, André Cavina Oliveira

## Entregas

| Item | Onde |
|---|---|
| Documento do projeto (versão final, Etapa 4) | [`docs/Projeto_Aplicado_III_Cozinha_Consciente.pdf`](docs/Projeto_Aplicado_III_Cozinha_Consciente.pdf) e [`.docx`](docs/Projeto_Aplicado_III_Cozinha_Consciente.docx) |
| Protótipo (site público) | https://cozinha-consciente.streamlit.app · código em [`app/`](app/) |
| Avaliação pelos usuários | aba **Avaliar** do site (respostas na planilha do Google Forms do grupo) |
| Vídeo de apresentação (YouTube) | _link a inserir_ |
| Vídeo da aplicação na comunidade | _link a inserir_ |
| Resultados da Etapa 4 (tabelas e figuras) | [`docs/resultados_etapa4/`](docs/resultados_etapa4/) |

## Protótipo (site)

A pessoa informa os ingredientes que tem em casa e recebe receitas que aproveitam esses itens, ordenadas com a reordenação nutricional do projeto (λ ajustável, padrão 0,35). Detalhes na seção 4.10 do documento.

```
pip install -r app/requirements.txt
streamlit run app/app.py
```

O catálogo do site (`app/dados/receitas.parquet`, 3,3 MB) é gerado a partir dos dados brutos com `python -m tools.build_app_data`.

Publicação no [Streamlit Community Cloud](https://share.streamlit.io): **Create app** → repositório `oR1ann/Sistema_de_Recomendacoes`, branch `main`, arquivo `app/app.py`.

## Base de dados

`Food.com Recipes and Interactions` (Kaggle): https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions

Baixe `RAW_recipes.csv` e `RAW_interactions.csv` e coloque em `data/raw/`.

## Como reproduzir

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.eda                # análise exploratória (Etapa 2)
python -m src.run_poc            # treino e avaliação com os parâmetros de src/config.py (configuração ajustada)
python -m src.tuning             # ajuste na validação e reavaliação no teste (Etapa 3, ~4 min)
python -m src.etapa4             # resultados finais: 3 protocolos, testes estatísticos, faixas de usuário (Etapa 4)
python -m tools.make_figs_etapa4 # figuras da seção 4 do documento (lê docs/resultados_etapa4/)
```

Saídas em `data/processed/`: `eda_resumo.json`, `figuras/`, `poc_stats.json`, `poc_metrics.csv`, as tabelas `tuning_*.csv` e `etapa4_*.csv`.
As tabelas e figuras usadas no documento estão versionadas em `docs/resultados_etapa3/` e `docs/resultados_etapa4/`.

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
| `src/etapa4.py` | resultados finais: robustez ao protocolo, testes estatísticos, faixas de atividade e exemplo de lista (Etapa 4) |
| `notebooks/02_poc_modelos.ipynb` | prova de conceito com os parâmetros iniciais (Etapa 2, protocolo corrigido) |
| `notebooks/03_ajuste_e_reavaliacao.ipynb` | análise dos resultados preliminares, ajuste e reavaliação (Etapa 3) |
| `docs/resultados_etapa3/` | tabelas, configuração final e figuras da Etapa 3 |
| `docs/resultados_etapa4/` | tabelas e figuras da seção 4 (Resultados) |
| `docs/Projeto_Aplicado_III_Cozinha_Consciente.*` | documento final do projeto (PDF e DOCX) |
| `docs/fluxograma_metodologia.png` | Figura 1 do documento (visão geral da metodologia) |
| `tools/make_synthetic.py` | amostra sintética para teste de integridade |
| `tools/make_flowchart.py`, `tools/build_nbs_etapa3.py` | geram o fluxograma e os notebooks da Etapa 3 |
| `tools/make_figs_etapa4.py` | gera as figuras da Etapa 4 |
| `app/` | protótipo: site em Streamlit (`app.py`), recomendador por ingredientes (`recomendador.py`), dicionário português→inglês (`ingredientes_pt.py`) e catálogo reduzido (`dados/`) |
| `tools/build_app_data.py` | gera o catálogo reduzido usado pelo site |
| `extensao/` | cartilha e registros da ação extensionista (Etapa 4) |

## Parâmetros (configuração ajustada na validação — Etapa 3)

RANDOM_STATE=42 · feedback positivo: nota ≥ 4 · k-core 5 em usuários e itens · split temporal leave-one-out · avaliação com 1 positivo + 99 negativos em posição aleatória · k=10 · SVD 32 fatores · ItemKNN 500 vizinhos · TF-IDF min_df=5, n-gramas (1,2), até 50.000 termos · normalização z-score · pesos do híbrido popularidade 0,6 / ItemKNN 0,1 / SVD 0,1 / conteúdo 0,2 · λ nutricional 0,35.

Configuração inicial (Etapa 2): SVD 64 fatores, ItemKNN 200 vizinhos, pesos SVD 0,5 / ItemKNN 0,3 / conteúdo 0,2, normalização min-max, λ 0,30.
