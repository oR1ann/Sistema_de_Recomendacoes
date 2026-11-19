"""Etapa 4: resultados finais com a configuração ajustada (src/config.py).

Responde às pendências registradas na Etapa 3:
  1. robustez ao protocolo: além de 1 positivo + 99 negativos uniformes, avalia com
     99 negativos amostrados por popularidade e com o ranking completo do catálogo;
  2. teste estatístico da diferença entre o híbrido e a popularidade (bootstrap pareado
     e Wilcoxon sobre o NDCG@10 por usuário);
  3. transferência de lambda para o catálogo inteiro (curva no ranking completo);
  4. desempenho por faixa de atividade do usuário e um exemplo qualitativo de lista.
Tudo é calculado no conjunto de TESTE com os parâmetros já escolhidos na validação.
"""
import json
import time

import numpy as np
import pandas as pd
from scipy import stats

from src import config
from src.data_preparation import build_dataset
from src.evaluate import _sample_candidates
from src.recommenders import (ContentTFIDFRecommender, Dataset,
                              ItemKNNRecommender, PopularityRecommender,
                              SVDRecommender)
from src.tuning import build_eval_set, hybrid_scores, metrics, score_matrix

K = config.TOP_K
LAMBDA_GRID = [round(x, 2) for x in np.arange(0.0, 0.65, 0.05)]
BATCH = 250
N_BOOT = 2000
OUT = config.PROC_DIR
NOMES = {"pop": "Popularidade", "itemknn": f"ItemKNN ({config.ITEMKNN_NEIGHBORS} viz.)",
         "svd": f"SVD ({config.SVD_FACTORS} fatores)", "content": "Conteudo (TF-IDF)",
         "hyb0": "Hibrido (lambda=0)", "hyb": f"Hibrido (lambda={config.HEALTH_LAMBDA})"}


# ---------------------------------------------------------------- protocolos amostrados
def build_pop_eval_set(ds, df, n_cand=None, seed=None):
    """1 positivo + (n-1) negativos sorteados proporcionalmente à popularidade, sem reposição."""
    n_cand = n_cand or config.CANDIDATE_SAMPLE
    rng = np.random.default_rng((seed or config.RANDOM_STATE) + 1)
    p = ds.popularity / ds.popularity.sum()
    users, cands, pos = [], [], []
    for uid, iid in zip(df["user_id"], df["recipe_id"]):
        u, i = ds.u2i.get(uid), ds.i2i.get(iid)
        if u is None or i is None:
            continue
        seen, neg = ds.seen[u], []
        chosen = set()
        while len(neg) < n_cand - 1:
            for d in rng.choice(len(p), size=4 * n_cand, p=p):
                d = int(d)
                if d != i and d not in seen and d not in chosen:
                    neg.append(d); chosen.add(d)
                    if len(neg) == n_cand - 1:
                        break
        c = rng.permutation(np.array([i] + neg, dtype=np.int64))
        users.append(u); cands.append(c); pos.append(int(np.where(c == i)[0][0]))
    return np.array(users), np.vstack(cands), np.array(pos)


def per_user(scores, pos, k=K):
    """HitRate e NDCG por caso, para os testes estatísticos."""
    order = np.argsort(-scores, axis=1, kind="stable")[:, :k]
    hit_mat = order == pos[:, None]
    hit = hit_mat.any(1)
    rank = hit_mat.argmax(1) + 1
    return hit.astype(float), np.where(hit, 1.0 / np.log2(rank + 1.0), 0.0)


def sampled_protocol(ds, models, ev, nome_protocolo):
    users, cands, pos = ev
    mats = {k_: score_matrix(m, users, cands) for k_, m in models.items()}
    health_c = ds.health[cands]
    W = config.HYBRID_WEIGHTS
    mats["hyb0"] = hybrid_scores(mats, W, config.HYBRID_NORM, 0.0, health_c)
    mats["hyb"] = hybrid_scores({k_: mats[k_] for k_ in W}, W, config.HYBRID_NORM,
                                config.HEALTH_LAMBDA, health_c)
    rows, pu = [], {}
    for k_, s in mats.items():
        m = metrics(s, cands, pos, ds)
        rows.append({"protocolo": nome_protocolo, "modelo": NOMES[k_],
                     **{a: round(b, 4) for a, b in m.items()}})
        pu[k_] = per_user(s, pos)
    return rows, pu


# ---------------------------------------------------------------- ranking completo
def _row_norm(x, kind):
    """Normalização por usuário ignorando itens já vistos (NaN)."""
    if kind == "zscore":
        mu, sd = np.nanmean(x, 1, keepdims=True), np.nanstd(x, 1, keepdims=True)
        return np.where(sd > 0, (x - mu) / np.where(sd > 0, sd, 1.0), 0.0)
    return _row_minmax(x)


def _row_minmax(x):
    lo, hi = np.nanmin(x, 1, keepdims=True), np.nanmax(x, 1, keepdims=True)
    return np.where(hi > lo, (x - lo) / np.where(hi > lo, hi - lo, 1.0), 0.0)


def full_ranking(ds, models, test, valid, rng):
    """Ordena todas as receitas não vistas no treino (e sem o item de validação)."""
    t_u = test["user_id"].map(ds.u2i)
    t_i = test["recipe_id"].map(ds.i2i)
    ok = t_u.notna() & t_i.notna()
    users = t_u[ok].astype(int).to_numpy()
    items = t_i[ok].astype(int).to_numpy()
    vmap = {ds.u2i[u]: ds.i2i[i] for u, i in zip(valid["user_id"], valid["recipe_id"])
            if u in ds.u2i and i in ds.i2i}
    W = config.HYBRID_WEIGHTS
    keys = list(models) + ["hyb0", "hyb"]
    acc = {k_: {"hit": [], "ndcg": [], "rec": set(), "pop": [], "health": []} for k_ in keys}
    lam_acc = {lam: {"hit": [], "ndcg": [], "rec": set(), "health": []} for lam in LAMBDA_GRID}
    all_items = np.arange(len(ds.items))

    def record(a, s, b_items):
        # posição do item relevante com desempate aleatório entre escores iguais
        sp = s[np.arange(len(s)), b_items][:, None]
        greater = (s > sp).sum(1)
        equal = (s == sp).sum(1) - 1
        rank = 1 + greater + np.floor(rng.random(len(s)) * (equal + 1)).astype(int)
        hit = rank <= K
        a["hit"].append(hit.astype(float))
        a["ndcg"].append(np.where(hit, 1.0 / np.log2(rank + 1.0), 0.0))
        top = np.argpartition(-s, K, axis=1)[:, :K]
        a["rec"].update(np.unique(top).tolist())
        a["health"].append(ds.health[top].mean(1))
        if "pop" in a:
            a["pop"].append(ds.pop_norm[top].mean(1))

    for b in range(0, len(users), BATCH):
        bu, bi = users[b:b + BATCH], items[b:b + BATCH]
        mask = np.zeros((len(bu), len(ds.items)), dtype=bool)
        for r, u in enumerate(bu):
            mask[r, list(ds.seen[u])] = True
            if u in vmap and vmap[u] != bi[r]:
                mask[r, vmap[u]] = True
        mats = {}
        for k_, m in models.items():
            s = np.vstack([np.asarray(m.score(u, all_items), dtype=np.float32) for u in bu]) \
                if k_ in ("pop", "svd") else _batch_scores(m, k_, bu)
            mats[k_] = np.where(mask, np.nan, s)
        fused = sum(w * _row_norm(mats[k_], config.HYBRID_NORM) for k_, w in W.items() if w > 0)
        fused = np.where(mask, np.nan, fused)
        health = np.broadcast_to(ds.health, fused.shape)
        mats["hyb0"] = fused
        mats["hyb"] = (1 - config.HEALTH_LAMBDA) * _row_minmax(fused) + config.HEALTH_LAMBDA * health
        for k_ in keys:
            record(acc[k_], np.where(mask, -np.inf, np.nan_to_num(mats[k_], nan=-np.inf)), bi)
        fm = _row_minmax(fused)
        for lam in LAMBDA_GRID:
            s = (1 - lam) * fm + lam * health
            record(lam_acc[lam], np.where(mask, -np.inf, s), bi)

    pop_all = ds.popularity / max(ds.popularity.sum(), 1)

    def summarize(a):
        rec = np.array(sorted(a["rec"]))
        out = {f"HitRate@{K}": float(np.concatenate(a["hit"]).mean()),
               f"NDCG@{K}": float(np.concatenate(a["ndcg"]).mean()),
               "Cobertura_catalogo": len(rec) / len(ds.items),
               "Novidade_bits": float(np.mean(-np.log2(np.maximum(pop_all[rec], 1e-12)))),
               f"IndiceNutricional@{K}": float(np.concatenate(a["health"]).mean())}
        if a.get("pop"):
            out["Vies_popularidade"] = float(np.concatenate(a["pop"]).mean())
        return out

    rows = [{"protocolo": "ranking completo", "modelo": NOMES[k_],
             **{a: round(b, 4) for a, b in summarize(acc[k_]).items()}} for k_ in keys]
    curve = pd.DataFrame([{"lambda": lam, **{a: round(b, 4) for a, b in summarize(lam_acc[lam]).items()}}
                          for lam in LAMBDA_GRID])
    pu = {k_: (np.concatenate(acc[k_]["hit"]), np.concatenate(acc[k_]["ndcg"])) for k_ in keys}
    return rows, curve, pu, users


def _batch_scores(model, key, bu):
    if key == "itemknn":
        return np.asarray((model.R[bu] @ model.S).todense(), dtype=np.float32)
    if key == "content":
        return np.asarray((model.P[bu] @ model.M.T).todense(), dtype=np.float32)
    raise KeyError(key)


# ---------------------------------------------------------------- estatística
def paired_test(a, b, rng, n_boot=N_BOOT):
    """Diferença média (a - b), IC 95% por bootstrap pareado e p-valor de Wilcoxon."""
    d = a - b
    boot = np.concatenate([d[rng.integers(0, len(d), size=(200, len(d)))].mean(1)
                           for _ in range(n_boot // 200)])
    nz = d[d != 0]
    p = float(stats.wilcoxon(nz).pvalue) if len(nz) else 1.0
    return {"diferenca_media": round(float(d.mean()), 4),
            "ic95_inf": round(float(np.percentile(boot, 2.5)), 4),
            "ic95_sup": round(float(np.percentile(boot, 97.5)), 4),
            "wilcoxon_p": p}


# ---------------------------------------------------------------- execução
def main():
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:6.0f}s] {m}", flush=True)
    rng = np.random.default_rng(config.RANDOM_STATE)

    rec, train, valid, test = build_dataset(save=False)
    ds = Dataset(train, rec)
    models = {"pop": PopularityRecommender().fit(ds),
              "itemknn": ItemKNNRecommender().fit(ds),
              "svd": SVDRecommender().fit(ds),
              "content": ContentTFIDFRecommender().fit(ds)}
    log("modelos treinados com a configuração ajustada")

    ev_unif = build_eval_set(ds, test)
    ev_pop = build_pop_eval_set(ds, test)
    rows_u, pu_u = sampled_protocol(ds, models, ev_unif, "99 negativos uniformes")
    log("protocolo uniforme")
    rows_p, pu_p = sampled_protocol(ds, models, ev_pop, "99 negativos por popularidade")
    log("protocolo por popularidade")
    rows_f, curve_f, pu_f, users_f = full_ranking(ds, models, test, valid, rng)
    log("ranking completo")

    table = pd.DataFrame(rows_u + rows_p + rows_f)
    table.to_csv(OUT / "etapa4_protocolos.csv", index=False)
    curve_f.to_csv(OUT / "etapa4_curva_lambda_ranking_completo.csv", index=False)

    # testes pareados: híbrido x popularidade e híbrido x melhor componente (SVD)
    tests = []
    for nome, pu in (("99 negativos uniformes", pu_u), ("99 negativos por popularidade", pu_p),
                     ("ranking completo", pu_f)):
        for a, b in (("hyb0", "pop"), ("hyb", "pop"), ("hyb0", "svd"), ("hyb", "hyb0")):
            tests.append({"protocolo": nome, "comparacao": f"{NOMES[a]} - {NOMES[b]}",
                          "metrica": f"NDCG@{K}", **paired_test(pu[a][1], pu[b][1], rng)})
    pd.DataFrame(tests).to_csv(OUT / "etapa4_testes_estatisticos.csv", index=False)
    log("testes estatísticos")

    # desempenho por faixa de atividade (protocolo uniforme)
    n_hist = np.asarray(ds.R.sum(axis=1)).ravel()[ev_unif[0]]
    faixas = pd.cut(n_hist, [0, 5, 10, 20, 50, np.inf], right=False,
                    labels=["3-4", "5-9", "10-19", "20-49", "50+"])
    seg = []
    for f in faixas.categories:
        sel = np.asarray(faixas == f)
        if sel.sum() == 0:
            continue
        seg.append({"faixa_historico": f, "usuarios": int(sel.sum()),
                    **{NOMES[k_]: round(float(pu_u[k_][1][sel].mean()), 4) for k_ in pu_u}})
    pd.DataFrame(seg).to_csv(OUT / "etapa4_faixas_atividade.csv", index=False)

    # exemplo qualitativo: usuário de teste com histórico mediano, ranking completo
    u = int(users_f[np.argsort(np.asarray(ds.R.sum(axis=1)).ravel()[users_f])[len(users_f) // 2]])
    all_items = np.arange(len(ds.items))
    seen = np.array(sorted(ds.seen[u]))
    mats = {k_: np.asarray(m.score(u, all_items), dtype=np.float32)[None, :] for k_, m in models.items()}
    W = config.HYBRID_WEIGHTS
    fused = sum(w * _row_norm(np.where(np.isin(all_items, seen)[None, :], np.nan, mats[k_]),
                              config.HYBRID_NORM) for k_, w in W.items() if w > 0)[0]
    final = (1 - config.HEALTH_LAMBDA) * _row_minmax(fused[None, :])[0] + config.HEALTH_LAMBDA * ds.health
    ex = []
    for nome, s in (("Popularidade", mats["pop"][0]), (NOMES["hyb0"], fused), (NOMES["hyb"], final)):
        s = np.where(np.isin(all_items, seen), -np.inf, np.nan_to_num(s, nan=-np.inf))
        for pos_, i in enumerate(np.argsort(-s)[:5], 1):
            r = ds.recipes.iloc[i]
            ex.append({"lista": nome, "posicao": pos_, "receita": r["name"],
                       "indice_nutricional": round(float(ds.health[i]), 3),
                       "minutos": int(r["minutes"]) if pd.notna(r["minutes"]) else None})
    hist = ds.recipes.iloc[seen]["name"].head(8).tolist()
    pd.DataFrame(ex).to_csv(OUT / "etapa4_exemplo_usuario.csv", index=False)
    (OUT / "etapa4_exemplo_usuario_historico.json").write_text(
        json.dumps({"usuario_indice": u, "receitas_no_historico": int(len(seen)), "amostra": hist},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    log("concluído")
    print(table.to_string())
    print(curve_f.to_string())
    print(pd.DataFrame(tests).to_string())
    print(pd.DataFrame(seg).to_string())
    print(pd.DataFrame(ex).to_string())


if __name__ == "__main__":
    main()
