"""Etapa 3: ajuste do pipeline na validação e reavaliação no teste.

Os escores de cada modelo são calculados uma única vez sobre os mesmos
candidatos (1 positivo + 99 negativos, posição aleatória) e depois recombinados
de forma vetorizada, o que permite varrer centenas de configurações do híbrido.
Todas as escolhas são feitas no conjunto de VALIDAÇÃO; o TESTE só é usado no fim.
"""
import itertools
import json
import time

import numpy as np
import pandas as pd

from src import config
from src.data_preparation import build_dataset
from src.evaluate import _sample_candidates
from src.recommenders import (ContentTFIDFRecommender, Dataset,
                              ItemKNNRecommender, PopularityRecommender,
                              SVDRecommender)

K = config.TOP_K
SVD_GRID = [32, 64, 128, 256]
KNN_GRID = [50, 100, 200, 500]
LAMBDA_GRID = [round(x, 2) for x in np.arange(0.0, 0.65, 0.05)]
MAX_NDCG_LOSS = 0.10   # perda relativa máxima de NDCG aceita ao reordenar por saúde
OUT = config.PROC_DIR


# ---------------------------------------------------------------- utilitários
def build_eval_set(ds, df, n_cand=None, seed=None):
    n_cand = n_cand or config.CANDIDATE_SAMPLE
    rng = np.random.default_rng(seed or config.RANDOM_STATE)
    users, cands, pos = [], [], []
    for uid, iid in zip(df["user_id"], df["recipe_id"]):
        u, i = ds.u2i.get(uid), ds.i2i.get(iid)
        if u is None or i is None:
            continue
        c = rng.permutation(_sample_candidates(rng, ds, u, i, n_cand))
        users.append(u); cands.append(c); pos.append(int(np.where(c == i)[0][0]))
    return np.array(users), np.vstack(cands), np.array(pos)


def score_matrix(model, users, cands):
    return np.vstack([np.asarray(model.score(u, c), dtype=np.float32)
                      for u, c in zip(users, cands)])


def minmax_rows(x):
    lo, hi = x.min(1, keepdims=True), x.max(1, keepdims=True)
    return np.where(hi > lo, (x - lo) / np.where(hi > lo, hi - lo, 1.0), 0.0)


def zscore_rows(x):
    mu, sd = x.mean(1, keepdims=True), x.std(1, keepdims=True)
    return np.where(sd > 0, (x - mu) / np.where(sd > 0, sd, 1.0), 0.0)


def normalize_rows(x, kind):
    return zscore_rows(x) if kind == "zscore" else minmax_rows(x)


def metrics(scores, cands, pos, ds, k=K):
    order = np.argsort(-scores, axis=1, kind="stable")[:, :k]
    top = np.take_along_axis(cands, order, 1)
    hit_mat = order == pos[:, None]
    hit = hit_mat.any(1)
    rank = np.where(hit, hit_mat.argmax(1) + 1, 0)
    ndcg = np.where(hit, 1.0 / np.log2(rank + 1.0), 0.0)
    mrr = np.where(hit, 1.0 / np.maximum(rank, 1), 0.0)
    recommended = np.unique(top)
    pop_all = ds.popularity / max(ds.popularity.sum(), 1)
    novelty = float(np.mean(-np.log2(np.maximum(pop_all[recommended], 1e-12))))
    return {
        f"HitRate@{k}": float(hit.mean()),
        f"Precision@{k}": float(hit.mean() / k),
        f"MAP@{k}": float(mrr.mean()),
        f"NDCG@{k}": float(ndcg.mean()),
        "Cobertura_catalogo": len(recommended) / len(ds.items),
        "Novidade_bits": novelty,
        "Vies_popularidade": float(ds.pop_norm[top].mean(1).mean()),
        f"IndiceNutricional@{k}": float(ds.health[top].mean(1).mean()),
        "n_casos": int(len(hit)),
    }


def hybrid_scores(mats, weights, norm, lam, health_c):
    total = sum(w * normalize_rows(mats[k_], norm) for k_, w in weights.items() if w > 0)
    if lam > 0:
        total = (1 - lam) * minmax_rows(total) + lam * health_c
    return total


def simplex(keys, step=0.1):
    n = int(round(1 / step))
    for combo in itertools.product(range(n + 1), repeat=len(keys) - 1):
        if sum(combo) <= n:
            vals = list(combo) + [n - sum(combo)]
            yield {k_: v * step for k_, v in zip(keys, vals)}


# ----------------------------------------------------------------- execução
def main():
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:6.0f}s] {m}", flush=True)

    rec, train, valid, test = build_dataset(save=True)
    ds = Dataset(train, rec)
    ev = {"valid": build_eval_set(ds, valid), "test": build_eval_set(ds, test)}
    health_c = {s: ds.health[ev[s][1]] for s in ev}
    log(f"base pronta: {ev['valid'][1].shape[0]} casos de validação, "
        f"{ev['test'][1].shape[0]} de teste")

    M = {s: {} for s in ev}   # M[split][nome] = matriz de escores

    def cache(name, model):
        for s, (u, c, _) in ev.items():
            M[s][name] = score_matrix(model, u, c)

    cache("pop", PopularityRecommender().fit(ds))
    cache("content", ContentTFIDFRecommender().fit(ds))
    log("popularidade e conteúdo prontos")
    for f in SVD_GRID:
        cache(f"svd_{f}", SVDRecommender().fit(ds, factors=f)); log(f"SVD fatores={f}")
    for nb in KNN_GRID:
        cache(f"knn_{nb}", ItemKNNRecommender().fit(ds, neighbors=nb)); log(f"ItemKNN vizinhos={nb}")

    # 1) componentes isolados na validação
    rows = []
    for name in M["valid"]:
        m = metrics(M["valid"][name], ev["valid"][1], ev["valid"][2], ds)
        rows.append({"modelo": name, **{k_: round(v, 4) for k_, v in m.items()}})
    comp = pd.DataFrame(rows).set_index("modelo")
    comp.to_csv(OUT / "tuning_componentes_validacao.csv")
    best_svd = comp.loc[[f"svd_{f}" for f in SVD_GRID], f"NDCG@{K}"].idxmax()
    best_knn = comp.loc[[f"knn_{n}" for n in KNN_GRID], f"NDCG@{K}"].idxmax()
    log(f"melhor SVD: {best_svd} | melhor ItemKNN: {best_knn}")

    # 2) pesos do híbrido (grade) + normalização, na validação
    def hyb_valid(keys, weights, norm, lam=0.0):
        s = hybrid_scores({k_: M["valid"][v] for k_, v in keys.items()}, weights, norm,
                          lam, health_c["valid"])
        return metrics(s, ev["valid"][1], ev["valid"][2], ds)

    keys_best = {"pop": "pop", "itemknn": best_knn, "svd": best_svd, "content": "content"}
    search = []
    for norm in ("minmax", "zscore"):
        for w in simplex(list(keys_best)):
            m = hyb_valid(keys_best, w, norm)
            search.append({"norm": norm, **{f"w_{k_}": round(v, 2) for k_, v in w.items()},
                           f"NDCG@{K}": round(m[f"NDCG@{K}"], 4),
                           f"HitRate@{K}": round(m[f"HitRate@{K}"], 4)})
    search = pd.DataFrame(search).sort_values(f"NDCG@{K}", ascending=False)
    search.to_csv(OUT / "tuning_hibrido_validacao.csv", index=False)
    top = search.iloc[0]
    best_w = {k_: float(top[f"w_{k_}"]) for k_ in keys_best}
    best_norm = top["norm"]
    log(f"melhor híbrido: {best_w} norm={best_norm} NDCG={top[f'NDCG@{K}']}")

    # 3) curva relevância x saudabilidade (lambda) e escolha de lambda na validação
    curve = {}
    for s in ("valid", "test"):
        r = []
        for lam in LAMBDA_GRID:
            sc = hybrid_scores({k_: M[s][v] for k_, v in keys_best.items()}, best_w,
                               best_norm, lam, health_c[s])
            m = metrics(sc, ev[s][1], ev[s][2], ds)
            r.append({"lambda": lam, **{k_: round(v, 4) for k_, v in m.items()}})
        curve[s] = pd.DataFrame(r)
        curve[s].to_csv(OUT / f"tuning_curva_lambda_{s}.csv", index=False)
    cv = curve["valid"]
    base_ndcg = cv.loc[cv["lambda"] == 0, f"NDCG@{K}"].iloc[0]
    ok = cv[cv[f"NDCG@{K}"] >= (1 - MAX_NDCG_LOSS) * base_ndcg]
    best_lam = float(ok["lambda"].max())
    log(f"lambda escolhido (perda de NDCG <= {MAX_NDCG_LOSS:.0%}): {best_lam}")

    # 4) reavaliação final no TESTE: configuração inicial x ajustada
    def test_row(nome, scores):
        m = metrics(scores, ev["test"][1], ev["test"][2], ds)
        return {"modelo": nome, **{k_: round(v, 4) for k_, v in m.items()}}

    T = M["test"]
    init_keys = {"svd": "svd_64", "itemknn": "knn_200", "content": "content"}
    init_w = {"svd": 0.5, "itemknn": 0.3, "content": 0.2}   # pesos iniciais da Etapa 2 (config.py guarda os ajustados)
    mats_init = {k_: T[v] for k_, v in init_keys.items()}
    mats_best = {k_: T[v] for k_, v in keys_best.items()}
    final = [
        test_row("Popularidade", T["pop"]),
        test_row("ItemKNN inicial (200 viz.)", T["knn_200"]),
        test_row(f"ItemKNN ajustado ({best_knn.split('_')[1]} viz.)", T[best_knn]),
        test_row("SVD inicial (64 fatores)", T["svd_64"]),
        test_row(f"SVD ajustado ({best_svd.split('_')[1]} fatores)", T[best_svd]),
        test_row("Conteudo (TF-IDF)", T["content"]),
        test_row("Hibrido inicial (lambda=0)",
                 hybrid_scores(mats_init, init_w, "minmax", 0.0, health_c["test"])),
        test_row("Hibrido inicial (lambda=0.30)",
                 hybrid_scores(mats_init, init_w, "minmax", 0.30, health_c["test"])),
        test_row("Hibrido ajustado (lambda=0)",
                 hybrid_scores(mats_best, best_w, best_norm, 0.0, health_c["test"])),
        test_row(f"Hibrido ajustado (lambda={best_lam})",
                 hybrid_scores(mats_best, best_w, best_norm, best_lam, health_c["test"])),
    ]
    final = pd.DataFrame(final).set_index("modelo")
    final.to_csv(OUT / "tuning_comparacao_teste.csv")

    best_cfg = {"SVD_FACTORS": int(best_svd.split("_")[1]),
                "ITEMKNN_NEIGHBORS": int(best_knn.split("_")[1]),
                "HYBRID_WEIGHTS": {k_: round(v, 2) for k_, v in best_w.items()},
                "HYBRID_NORM": best_norm, "HEALTH_LAMBDA": best_lam,
                "criterio_lambda": f"maior lambda com perda relativa de NDCG@{K} <= {MAX_NDCG_LOSS:.0%} na validação",
                "casos_validacao": int(ev["valid"][1].shape[0]),
                "casos_teste": int(ev["test"][1].shape[0])}
    (OUT / "tuning_melhor_config.json").write_text(
        json.dumps(best_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    log("concluído")
    print(final.to_string())
    print(json.dumps(best_cfg, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
