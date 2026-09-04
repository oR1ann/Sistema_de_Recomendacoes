"""Gera uma amostra sintetica com o MESMO esquema do Food.com.
"""
import numpy as np
import pandas as pd

from src import config

rng = np.random.default_rng(42)
N_REC, N_USR, N_INT = 3000, 1200, 45000

INGR = ["arroz", "feijao", "frango", "tomate", "cebola", "alho", "batata",
        "cenoura", "ovo", "leite", "queijo", "farinha", "acucar", "manteiga",
        "azeite", "sal", "pimenta", "aveia", "banana", "espinafre", "atum",
        "lentilha", "iogurte", "abobrinha", "couve"]
TAGS = ["30-minutes-or-less", "vegetarian", "low-sodium", "dessert", "healthy",
        "main-dish", "soup", "salad", "breakfast", "high-protein", "low-fat"]


def main():
    ids = np.arange(1, N_REC + 1)
    rows = []
    for rid in ids:
        k = rng.integers(3, 9)
        ing = rng.choice(INGR, size=k, replace=False).tolist()
        tg = rng.choice(TAGS, size=rng.integers(2, 5), replace=False).tolist()
        cal = float(rng.gamma(4.0, 90.0) + 40)
        rows.append({
            "name": f"receita {rid} de {ing[0]}",
            "id": int(rid),
            "minutes": int(rng.integers(5, 120)),
            "contributor_id": int(rng.integers(1, 500)),
            "submitted": "2015-01-01",
            "tags": str(tg),
            "nutrition": str([round(cal, 1)] + [float(round(rng.uniform(0, 90), 1))
                                                for _ in range(6)]),
            "n_steps": int(rng.integers(2, 15)),
            "steps": "['misture', 'cozinhe']",
            "description": "amostra sintetica",
            "ingredients": str(ing),
            "n_ingredients": int(k),
        })
    recipes = pd.DataFrame(rows)

    pop = rng.pareto(0.8, N_REC) + 1
    prob = pop / pop.sum()
    users = rng.integers(1, N_USR + 1, N_INT)
    items = rng.choice(ids, size=N_INT, p=prob)
    dates = pd.to_datetime("2016-01-01") + pd.to_timedelta(
        rng.integers(0, 900, N_INT), unit="D")
    inter = pd.DataFrame({
        "user_id": users, "recipe_id": items,
        "date": dates.strftime("%Y-%m-%d"),
        "rating": rng.choice([0, 3, 4, 5], size=N_INT, p=[.05, .15, .3, .5]),
        "review": "texto",
    })

    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    recipes.to_csv(config.RECIPES_CSV, index=False)
    inter.to_csv(config.INTERACTIONS_CSV, index=False)
    print(f"amostra sintetica gravada em {config.RAW_DIR}")


if __name__ == "__main__":
    main()
