"""Gera o catálogo reduzido usado pelo site (app/dados/receitas.parquet).

Usa as mesmas receitas do modelo avaliado (após limpeza e k-core) e guarda apenas o
necessário para recomendar: nome, tempo, ingredientes, marcadores, nutrientes por
porção, índice nutricional e popularidade. Passos e descrições não são copiados; o site
aponta para a página original da receita no Food.com.
"""
import ast

import numpy as np
import pandas as pd

from src import config
from src.data_preparation import build_dataset

OUT = config.BASE_DIR / "app" / "dados" / "receitas.parquet"


def main():
    rec, train, valid, test = build_dataset(save=False)
    raw = pd.read_csv(config.RECIPES_CSV, usecols=["id", "ingredients", "tags"]).rename(
        columns={"id": "recipe_id"})
    pop = pd.concat([train, valid, test])["recipe_id"].value_counts().rename("avaliacoes_positivas")

    cat = rec.merge(raw, on="recipe_id", how="left").join(pop, on="recipe_id")
    cat["ingredientes"] = cat["ingredients"].apply(lambda x: "|".join(ast.literal_eval(x)))
    cat["tags"] = cat["tags"].apply(lambda x: "|".join(ast.literal_eval(x)))
    cat["avaliacoes_positivas"] = cat["avaliacoes_positivas"].fillna(0).astype(np.int32)
    keep = ["recipe_id", "name", "minutes", "n_ingredients", "calories", "total_fat_g",
            "saturated_fat_g", "sugar_g", "sodium_mg", "protein_g", "health_index",
            "avaliacoes_positivas", "ingredientes", "tags"]
    cat = cat[keep].copy()
    for c in ("calories", "total_fat_g", "saturated_fat_g", "sugar_g", "sodium_mg", "protein_g", "health_index"):
        cat[c] = cat[c].astype(np.float32).round(3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cat.to_parquet(OUT, index=False, compression="zstd")
    print(f"{len(cat)} receitas gravadas em {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
