"""Protocolo de avaliacao offline e metricas do sistema de recomendacao."""
import numpy as np
import pandas as pd

from src import config
from src.recommenders import Dataset


def _sample_candidates(rng, ds: Dataset, u: int, positive: int, n: int):
    """1 item relevante + (n-1) negativos amostrados fora do historico."""
    seen = ds.seen[u]
    negatives, n_items = [], len(ds.items)
    while len(negatives) < n - 1:
        draw = rng.integers(0, n_items, size=(n - 1 - len(negatives)) * 2)
        for d in draw:
            if d != positive and d not in seen:
                negatives.append(int(d))
                if len(negatives) == n - 1:
                    break
    return np.array([positive] + negatives, dtype=np.int64)


def evaluate(model, ds: Dataset, test: pd.DataFrame, k: int = None,
             n_candidates: int = None, seed: int = None) -> dict:
    k = k or config.TOP_K
    n_candidates = n_candidates or config.CANDIDATE_SAMPLE
    rng = np.random.default_rng(seed or config.RANDOM_STATE)

    hits, ndcgs, aps, precisions, recalls = [], [], [], [], []
    health_at_k, recommended, pop_of_rec = [], set(), []

    for user_id, item_id in zip(test["user_id"], test["recipe_id"]):
        u = ds.u2i.get(user_id)
        i = ds.i2i.get(item_id)
        if u is None or i is None:
            continue
        cands = _sample_candidates(rng, ds, u, i, n_candidates)
        scores = np.asarray(model.score(u, cands), dtype=np.float64)
        order = np.argsort(-scores)[:k]
        topk = cands[order]

        hit = int(i in topk)
        hits.append(hit)
        precisions.append(hit / k)
        recalls.append(float(hit))
        if hit:
            rank = int(np.where(topk == i)[0][0]) + 1
            ndcgs.append(1.0 / np.log2(rank + 1))
            aps.append(1.0 / rank)
        else:
            ndcgs.append(0.0)
            aps.append(0.0)

        health_at_k.append(float(np.mean(ds.health[topk])))
        recommended.update(topk.tolist())
        pop_of_rec.append(float(np.mean(ds.pop_norm[topk])))

    n_items = len(ds.items)
    pop_all = ds.popularity / max(ds.popularity.sum(), 1)
    novelty = float(np.mean([
        -np.log2(max(pop_all[i], 1e-12)) for i in recommended
    ])) if recommended else 0.0

    return {
        "modelo": model.name,
        f"HitRate@{k}": round(float(np.mean(hits)), 4),
        f"Precision@{k}": round(float(np.mean(precisions)), 4),
        f"Recall@{k}": round(float(np.mean(recalls)), 4),
        f"MAP@{k}": round(float(np.mean(aps)), 4),
        f"NDCG@{k}": round(float(np.mean(ndcgs)), 4),
        "Cobertura_catalogo": round(len(recommended) / n_items, 4),
        "Novidade_bits": round(novelty, 3),
        "Vies_popularidade": round(float(np.mean(pop_of_rec)), 4),
        f"IndiceNutricional@{k}": round(float(np.mean(health_at_k)), 4),
        "usuarios_avaliados": len(hits),
    }


def comparison_table(results: list) -> pd.DataFrame:
    return pd.DataFrame(results).set_index("modelo")
