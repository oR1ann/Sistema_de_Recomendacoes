"""Preparacao da base Food.com para o sistema de recomendacao."""
import ast
import re
import unicodedata

import numpy as np
import pandas as pd

from src import config, nutrition


def _norm_text(value) -> str:
    if isinstance(value, str) and value.startswith("["):
        try:
            value = " ".join(ast.literal_eval(value))
        except (ValueError, SyntaxError):
            pass
    if not isinstance(value, str):
        return ""
    txt = unicodedata.normalize("NFKD", value.lower())
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def load_raw():
    recipes = pd.read_csv(config.RECIPES_CSV)
    interactions = pd.read_csv(config.INTERACTIONS_CSV)
    return recipes, interactions


def prepare_recipes(recipes: pd.DataFrame) -> pd.DataFrame:
    df = recipes.drop_duplicates(subset=["id"]).copy()
    df = nutrition.parse_nutrition(df)
    df = nutrition.pdv_to_grams(df)
    df["health_index"] = nutrition.health_index(df)
    df["ingredients_txt"] = df["ingredients"].apply(_norm_text)
    df["tags_txt"] = df["tags"].apply(_norm_text)
    df["name_txt"] = df["name"].apply(_norm_text)
    df["content_txt"] = (
        df["name_txt"] + " " + df["tags_txt"] + " " + df["ingredients_txt"]
    ).str.strip()
    keep = ["id", "name", "minutes", "n_steps", "n_ingredients", "calories",
            "total_fat_g", "sugar_g", "sodium_mg", "protein_g",
            "saturated_fat_g", "carbohydrates_g", "health_index",
            "ingredients_txt", "tags_txt", "content_txt"]
    return df[keep].rename(columns={"id": "recipe_id"})


def prepare_interactions(interactions: pd.DataFrame) -> pd.DataFrame:
    df = interactions.drop_duplicates(subset=["user_id", "recipe_id", "date"]).copy()
    if config.DROP_ZERO_RATINGS:
        df = df[df["rating"] > 0]
    df = df[df["rating"] >= config.POSITIVE_RATING_THRESHOLD]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])[["user_id", "recipe_id", "rating", "date"]]


def apply_kcore(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra iterativamente usuarios e itens com poucas interacoes."""
    prev = -1
    while len(df) != prev:
        prev = len(df)
        uc = df["user_id"].value_counts()
        df = df[df["user_id"].isin(uc[uc >= config.MIN_USER_INTERACTIONS].index)]
        ic = df["recipe_id"].value_counts()
        df = df[df["recipe_id"].isin(ic[ic >= config.MIN_ITEM_INTERACTIONS].index)]
    return df


def temporal_leave_one_out(df: pd.DataFrame):
    """Ultima interacao de cada usuario vai para teste; penultima para validacao."""
    df = df.sort_values(["user_id", "date"])
    rank = df.groupby("user_id").cumcount(ascending=False)
    test = df[rank == 0]
    valid = df[rank == 1]
    train = df[rank >= 2]
    train_users = set(train["user_id"])
    train_items = set(train["recipe_id"])
    test = test[test["user_id"].isin(train_users) & test["recipe_id"].isin(train_items)]
    valid = valid[valid["user_id"].isin(train_users) & valid["recipe_id"].isin(train_items)]
    return train, valid, test


def build_dataset(save: bool = True):
    recipes, interactions = load_raw()
    rec = prepare_recipes(recipes)
    inter = prepare_interactions(interactions)
    inter = inter[inter["recipe_id"].isin(set(rec["recipe_id"]))]
    inter = apply_kcore(inter)
    rec = rec[rec["recipe_id"].isin(set(inter["recipe_id"]))]
    train, valid, test = temporal_leave_one_out(inter)
    if save:
        rec.to_csv(config.PROC_DIR / "recipes.csv", index=False)
        train.to_csv(config.PROC_DIR / "train.csv", index=False)
        valid.to_csv(config.PROC_DIR / "valid.csv", index=False)
        test.to_csv(config.PROC_DIR / "test.csv", index=False)
    return rec, train, valid, test


def describe(rec, train, valid, test) -> dict:
    n_users = train["user_id"].nunique()
    n_items = train["recipe_id"].nunique()
    density = len(train) / (n_users * n_items) if n_users and n_items else 0.0
    return {
        "receitas_no_catalogo": int(len(rec)),
        "usuarios": int(n_users),
        "itens_com_interacao": int(n_items),
        "interacoes_treino": int(len(train)),
        "interacoes_validacao": int(len(valid)),
        "interacoes_teste": int(len(test)),
        "densidade_matriz_pct": round(density * 100, 6),
        "esparsidade_pct": round((1 - density) * 100, 6),
        "interacoes_por_usuario_media": round(len(train) / n_users, 2) if n_users else 0,
        "indice_nutricional_medio_catalogo": round(float(rec["health_index"].mean()), 4),
    }


if __name__ == "__main__":
    rec, tr, va, te = build_dataset()
    for k, v in describe(rec, tr, va, te).items():
        print(f"{k}: {v}")
