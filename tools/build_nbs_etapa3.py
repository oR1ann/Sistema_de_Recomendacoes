import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell


def save(cells, path):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("criado", path)


# =============================================================== 02 — PoC
poc = [
md("""# Etapa 2 — Prova de Conceito dos Modelos de Recomendação
## Cozinha Consciente — Sistema de Recomendação Híbrido de Receitas

Objetivo: treinar uma versão inicial de cada abordagem sobre a base real e verificar se a técnica
proposta é viável. Este notebook usa os **parâmetros iniciais** definidos na Etapa 2; o ajuste
desses parâmetros é feito no notebook `03_ajuste_e_reavaliacao.ipynb`.

> **Nota de revisão do protocolo.** Na primeira execução da prova de conceito, o item relevante
> ocupava sempre a posição 0 da lista de candidatos e os desempates de escore o favoreciam, o que
> inflava modelos com muitos escores iguais a zero (principalmente o ItemKNN). O protocolo foi
> corrigido: a posição do item relevante agora é aleatória e o desempate é estável. Os números
> abaixo já usam o protocolo corrigido."""),
code("""import sys
sys.path.append("..")

import pandas as pd
import matplotlib.pyplot as plt

from src import config
from src.data_preparation import build_dataset, describe
from src.recommenders import (Dataset, PopularityRecommender, ItemKNNRecommender,
                              SVDRecommender, ContentTFIDFRecommender, HybridRecommender)
from src.evaluate import evaluate, comparison_table

# parâmetros INICIAIS da prova de conceito (Etapa 2)
SVD_FATORES_INICIAL = 64
KNN_VIZINHOS_INICIAL = 200
PESOS_INICIAIS = {"svd": 0.5, "itemknn": 0.3, "content": 0.2}
LAMBDA_INICIAL = 0.30"""),
md("""## 1. Preparação da base
Deduplicação, descarte de nota 0, feedback implícito (nota ≥ 4), k-core 5/5, decomposição da coluna
`nutrition` e divisão temporal *leave-one-out* (última interação → teste, penúltima → validação)."""),
code("""recipes, train, valid, test = build_dataset()
pd.Series(describe(recipes, train, valid, test))"""),
md("## 2. Matriz usuário-item e treinamento dos modelos iniciais"),
code("""ds = Dataset(train, recipes)
print("Matriz usuário-item:", ds.R.shape, "| interações:", ds.R.nnz)

pop = PopularityRecommender().fit(ds)
knn = ItemKNNRecommender().fit(ds, neighbors=KNN_VIZINHOS_INICIAL)
svd = SVDRecommender().fit(ds, factors=SVD_FATORES_INICIAL)
cnt = ContentTFIDFRecommender().fit(ds)

comps = {"svd": svd, "itemknn": knn, "content": cnt}
hyb = HybridRecommender(comps, weights=PESOS_INICIAIS, health_lambda=0.0, norm="minmax").fit(ds)
hyb_h = HybridRecommender(comps, weights=PESOS_INICIAIS, health_lambda=LAMBDA_INICIAL, norm="minmax").fit(ds)"""),
md("""## 3. Avaliação (conjunto de teste)
Para cada caso de teste: 1 item relevante + 99 negativos não vistos, em posição aleatória; métricas @10."""),
code("""results = [evaluate(m, ds, test) for m in (pop, knn, svd, cnt, hyb, hyb_h)]
table = comparison_table(results)
table[["HitRate@10", "Precision@10", "MAP@10", "NDCG@10", "Cobertura_catalogo",
       "Vies_popularidade", "IndiceNutricional@10"]]"""),
code("""ax = table["NDCG@10"].plot(kind="barh", color="#2E5496")
ax.set_title("NDCG@10 por modelo (parâmetros iniciais)")
ax.invert_yaxis()
plt.tight_layout(); plt.show()"""),
md("""## 4. Discussão da prova de conceito

- A **popularidade** foi o melhor modelo isolado (HitRate 0,507; NDCG 0,328). Isso é esperado no
  protocolo com negativos sorteados ao acaso: itens populares quase sempre superam itens aleatórios.
- O **ItemKNN** ficou muito abaixo (HitRate 0,180, próximo ao acaso, que é 0,10): com a poda para
  200 vizinhos, muitos candidatos recebem escore zero. Sua cobertura de catálogo é a maior (96,6%).
- O **SVD** ficou em posição intermediária (HitRate 0,349) e o **conteúdo TF-IDF** foi o mais fraco
  entre os não colaborativos (0,213), mas é o que mais favorece receitas saudáveis (índice 0,568).
- O **híbrido inicial** (pesos definidos a priori, sem componente de popularidade) ficou *abaixo* da
  popularidade e, em NDCG, até do SVD isolado: pesos fixos escolhidos sem validação não funcionam.
- A **reordenação nutricional** (λ = 0,30) elevou o índice nutricional médio de 0,545 para 0,626
  (+14,8%) ao custo de 5,0% de NDCG, o que confirma a viabilidade do compromisso relevância ×
  saudabilidade.

**Conclusão:** a técnica é viável, mas o pipeline precisa de ajustes (hiperparâmetros, pesos do
híbrido, normalização e escolha de λ com critério explícito). Isso é feito na Etapa 3, sempre
usando a **validação** para decidir e o **teste** apenas para a reavaliação final."""),
]
save(poc, "notebooks/02_poc_modelos.ipynb")

# ================================================== 03 — ajuste e reavaliação
aj = [
md("""# Etapa 3 — Ajuste do Pipeline e Reavaliação
## Cozinha Consciente — Sistema de Recomendação Híbrido de Receitas

Este notebook documenta como os resultados preliminares (notebook 02) foram analisados e como o
pipeline foi ajustado. Regra do experimento: **todas as escolhas são feitas no conjunto de
validação; o conjunto de teste só é usado na reavaliação final.**

Para reexecutar o ajuste completo (≈ 3 min): `python -m src.tuning`. Este notebook lê as tabelas
já geradas, salvas em `docs/resultados_etapa3/`."""),
code("""import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

RES = Path("../docs/resultados_etapa3")
FIG = RES / "figuras"; FIG.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 200)
cfg = json.loads((RES / "tuning_melhor_config.json").read_text(encoding="utf-8"))
cfg"""),
md("""## 1. Análise dos resultados preliminares
A revisão da prova de conceito apontou quatro pontos:

1. **Protocolo de avaliação.** O item relevante ficava na posição 0 dos candidatos, e os empates de
   escore o favoreciam. A tabela abaixo mostra o efeito (HitRate@10 no teste):"""),
code("""pd.DataFrame({
    "HitRate@10 (protocolo antigo)":     {"Popularidade": 0.5073, "ItemKNN (200 viz.)": 0.6654, "SVD (64 fatores)": 0.3520},
    "HitRate@10 (posição aleatória)":    {"Popularidade": 0.5072, "ItemKNN (200 viz.)": 0.1801, "SVD (64 fatores)": 0.3494},
})"""),
md("""   O ItemKNN parecia o melhor modelo (0,665) apenas por causa dos empates em zero; corrigido, é o pior.
2. **Hiperparâmetros** de SVD (64 fatores) e ItemKNN (200 vizinhos) definidos sem validação.
3. **Pesos do híbrido** (0,5/0,3/0,2) definidos a priori e sem componente de popularidade.
4. **Escolha de λ** (0,30) sem critério explícito.

## 2. Ajuste de hiperparâmetros dos modelos (validação)"""),
code("""comp = pd.read_csv(RES / "tuning_componentes_validacao.csv", index_col=0)
comp[["HitRate@10", "NDCG@10", "Cobertura_catalogo"]]"""),
code("""fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
svd = comp.loc[[i for i in comp.index if i.startswith("svd_")], "NDCG@10"]
knn = comp.loc[[i for i in comp.index if i.startswith("knn_")], "NDCG@10"]
ax[0].plot([int(i.split("_")[1]) for i in svd.index], svd.values, marker="o", color="#2E5496")
ax[0].set_title("SVD: NDCG@10 x fatores (validação)"); ax[0].set_xlabel("fatores latentes")
ax[1].plot([int(i.split("_")[1]) for i in knn.index], knn.values, marker="o", color="#2E5496")
ax[1].set_title("ItemKNN: NDCG@10 x vizinhos (validação)"); ax[1].set_xlabel("vizinhos por item")
for a in ax: a.grid(alpha=.3)
plt.tight_layout(); plt.savefig(FIG / "ajuste_componentes.png", dpi=150); plt.show()"""),
md("""**Leitura:** o SVD melhora com *menos* fatores (32 foi o melhor da grade) e o ItemKNN melhora com
*mais* vizinhos (500 foi o melhor). Ambos estão nas bordas da grade testada, então há espaço para
explorar valores fora dela (ex.: 16 fatores; 1000 vizinhos, que exige mais memória).

## 3. Ajuste dos pesos do híbrido e da normalização (validação)
Grade com passo 0,1 sobre quatro componentes (popularidade, ItemKNN, SVD, conteúdo) e duas
normalizações por usuário (min-max e z-score): 572 configurações."""),
code("""hib = pd.read_csv(RES / "tuning_hibrido_validacao.csv")
hib.head(8)"""),
md("""**Leitura:** o melhor híbrido usa z-score e dá 60% do peso à popularidade, 20% ao conteúdo e 10% a
cada modelo colaborativo. Os componentes personalizados contribuem pouco sozinhos, mas a combinação
supera a popularidade pura.

## 4. Compromisso relevância × saudabilidade (escolha de λ)
Critério definido antes de olhar o teste: **maior λ cuja perda relativa de NDCG@10 na validação seja
de no máximo 10%** em relação a λ = 0."""),
code("""cv = pd.read_csv(RES / "tuning_curva_lambda_valid.csv")
ct = pd.read_csv(RES / "tuning_curva_lambda_test.csv")
fig, ax = plt.subplots(figsize=(6.5, 4))
ax.plot(cv["IndiceNutricional@10"], cv["NDCG@10"], marker="o", label="validação", color="#2E5496")
ax.plot(ct["IndiceNutricional@10"], ct["NDCG@10"], marker="s", label="teste", color="#C55A11")
sel = ct[ct["lambda"] == cfg["HEALTH_LAMBDA"]].iloc[0]
ax.scatter([sel["IndiceNutricional@10"]], [sel["NDCG@10"]], s=160, facecolors="none",
           edgecolors="black", label=f"λ escolhido = {cfg['HEALTH_LAMBDA']}")
ax.set_xlabel("índice nutricional médio das listas"); ax.set_ylabel("NDCG@10")
ax.set_title("Compromisso relevância × saudabilidade"); ax.grid(alpha=.3); ax.legend()
plt.tight_layout(); plt.savefig(FIG / "curva_compromisso.png", dpi=150); plt.show()
cv[["lambda", "HitRate@10", "NDCG@10", "IndiceNutricional@10"]]"""),
md("## 5. Reavaliação final no conjunto de teste (configuração inicial × ajustada)"),
code("""final = pd.read_csv(RES / "tuning_comparacao_teste.csv", index_col=0)
final[["HitRate@10", "NDCG@10", "MAP@10", "Cobertura_catalogo", "Vies_popularidade", "IndiceNutricional@10"]]"""),
code("""ax = final["NDCG@10"].plot(kind="barh", color="#2E5496", figsize=(7, 4.5))
ax.set_title("NDCG@10 no teste: configuração inicial × ajustada"); ax.invert_yaxis()
plt.tight_layout(); plt.savefig(FIG / "comparacao_final.png", dpi=150); plt.show()"""),
md("""## 6. Discussão

- **Ganho do ajuste.** SVD: NDCG 0,228 → 0,250 (+9,6%) com 32 fatores; ItemKNN: 0,100 → 0,109 (+8,4%)
  com 500 vizinhos; híbrido sem reordenação: 0,217 → 0,335 (+54%), em grande parte por incluir a
  popularidade e escolher os pesos na validação.
- **Híbrido × popularidade.** O híbrido ajustado supera a popularidade pura, mas por pouco (NDCG 0,335
  contra 0,328; HitRate 0,519 contra 0,507). O ganho mais claro está na **cobertura de catálogo**
  (0,48 contra 0,17), ou seja, a lista deixa de se concentrar nos mesmos itens.
- **Custo da saudabilidade.** Com λ = 0,35, o índice nutricional médio sobe de 0,534 para 0,677 (+27%)
  e supera os 0,526 da popularidade em 28,8%, com perda de 7,9% de NDCG em relação ao híbrido sem
  reordenação (6,0% em relação à popularidade).
- **Limitações.** (i) O protocolo com 99 negativos sorteados ao acaso favorece itens populares, o que
  explica a força da popularidade; na Etapa 4 convém verificar com negativos amostrados por
  popularidade ou ranking completo. (ii) SVD e ItemKNN ficaram nas bordas da grade. (iii) O ganho
  do híbrido sobre a popularidade é pequeno e não foi testado estatisticamente. (iv) O índice
  nutricional usa limiares por 100 kcal, não por 100 g.

**Configuração final adotada:** SVD com 32 fatores, ItemKNN com 500 vizinhos, normalização z-score,
pesos popularidade 0,6 / conteúdo 0,2 / ItemKNN 0,1 / SVD 0,1 e λ = 0,35."""),
]
save(aj, "notebooks/03_ajuste_e_reavaliacao.ipynb")
