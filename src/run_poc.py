"""Pipeline completo: treina e compara os modelos com os parametros de src/config.py.

O config guarda a configuracao AJUSTADA na Etapa 3 (src/tuning.py). A prova de conceito
com os parametros iniciais da Etapa 2 esta em notebooks/02_poc_modelos.ipynb.
"""
import json
import time

import pandas as pd

from src import config
from src.data_preparation import build_dataset, describe
from src.evaluate import comparison_table, evaluate
from src.recommenders import (ContentTFIDFRecommender, Dataset,
                              HybridRecommender, ItemKNNRecommender,
                              PopularityRecommender, SVDRecommender)


def main():
    t0 = time.time()
    print(">> preparando a base ...")
    rec, train, valid, test = build_dataset()
    stats = describe(rec, train, valid, test)
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    ds = Dataset(train, rec)
    print(">> treinando modelos ...")
    pop = PopularityRecommender().fit(ds)
    knn = ItemKNNRecommender().fit(ds)
    svd = SVDRecommender().fit(ds)
    cnt = ContentTFIDFRecommender().fit(ds)
    comps = {"pop": pop, "itemknn": knn, "svd": svd, "content": cnt}
    hyb = HybridRecommender(comps, health_lambda=0.0).fit(ds)
    hyb_h = HybridRecommender(comps, health_lambda=config.HEALTH_LAMBDA).fit(ds)

    print(">> avaliando ...")
    results = [evaluate(m, ds, test) for m in (pop, knn, svd, cnt, hyb, hyb_h)]
    table = comparison_table(results)
    print(table.to_string())

    (config.PROC_DIR / "poc_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    table.to_csv(config.PROC_DIR / "poc_metrics.csv")
    print(f"\nconcluido em {time.time() - t0:.1f}s")
    print(f"arquivos gerados em {config.PROC_DIR}")
    return table


if __name__ == "__main__":
    main()
