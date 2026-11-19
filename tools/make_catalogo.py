"""Gera o catalogo (receita, ingredientes, indice_nutricional, popularidade)
que o Apps Script do prototipo le na aba "catalogo".

Usa o mesmo pipeline do projeto:
  - popularidade = numero de interacoes positivas (nota >= 4) no treino,
    depois do k-core e do split temporal (igual a PopularityRecommender);
  - indice_nutricional = health_index em [0, 1] (src/nutrition.py).

Uso:
    python -m tools.make_catalogo              # 5000 receitas mais populares
    python -m tools.make_catalogo --top 20000  # catalogo maior
    python -m tools.make_catalogo --top 0      # catalogo inteiro

Saida: data/processed/catalogo.csv (UTF-8, separador virgula, ponto decimal).
"""
import argparse
import ast

import pandas as pd

from src import config, data_preparation


def _lista_para_texto(valor) -> str:
    try:
        itens = ast.literal_eval(valor) if isinstance(valor, str) else list(valor)
        return ", ".join(str(i).strip() for i in itens)
    except (ValueError, SyntaxError):
        return str(valor)


def main(top: int, saida) -> None:
    rec, train, _, _ = data_preparation.build_dataset(save=False)

    nomes = pd.read_csv(config.RECIPES_CSV, usecols=["id", "name", "ingredients"])
    nomes = nomes.drop_duplicates(subset=["id"]).rename(columns={"id": "recipe_id"})
    nomes["ingredientes"] = nomes["ingredients"].apply(_lista_para_texto)

    pop = train["recipe_id"].value_counts().rename("popularidade").reset_index()
    pop.columns = ["recipe_id", "popularidade"]

    cat = (
        rec[["recipe_id", "health_index"]]
        .merge(nomes[["recipe_id", "name", "ingredientes"]], on="recipe_id")
        .merge(pop, on="recipe_id")
    )
    cat = cat.rename(columns={"name": "receita", "health_index": "indice_nutricional"})
    cat["receita"] = cat["receita"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    cat = cat[cat["receita"] != ""]
    cat = cat.sort_values(["popularidade", "receita"], ascending=[False, True])
    if top and top > 0:
        cat = cat.head(top)

    cat["indice_nutricional"] = cat["indice_nutricional"].round(4)
    cat["popularidade"] = cat["popularidade"].astype(int)
    cat = cat[["receita", "ingredientes", "indice_nutricional", "popularidade"]]
    cat.to_csv(saida, index=False, encoding="utf-8")
    print(f"{len(cat)} receitas gravadas em {saida}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5000,
                    help="quantas receitas mais populares manter (0 = todas)")
    ap.add_argument("--saida", default=str(config.PROC_DIR / "catalogo.csv"))
    args = ap.parse_args()
    main(args.top, args.saida)
