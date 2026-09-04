"""Analise exploratoria da base Food.com (Etapa 2)."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config
from src.data_preparation import load_raw, prepare_interactions, prepare_recipes

FIG_DIR = config.PROC_DIR / "figuras"


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    raw_rec, raw_int = load_raw()

    resumo = {
        "receitas_registros": int(len(raw_rec)),
        "receitas_colunas": int(raw_rec.shape[1]),
        "interacoes_registros": int(len(raw_int)),
        "interacoes_colunas": int(raw_int.shape[1]),
        "usuarios_distintos": int(raw_int["user_id"].nunique()),
        "receitas_avaliadas": int(raw_int["recipe_id"].nunique()),
        "notas_zero": int((raw_int["rating"] == 0).sum()),
        "nulos_por_coluna_receitas": raw_rec.isna().sum().to_dict(),
    }

    # distribuicao de notas
    dist = raw_int["rating"].value_counts(normalize=True).sort_index()
    resumo["distribuicao_notas_pct"] = (dist * 100).round(2).to_dict()
    ax = dist.plot(kind="bar", color="#2E5496")
    ax.set_title("Distribuicao das notas"); ax.set_xlabel("nota"); ax.set_ylabel("proporcao")
    plt.tight_layout(); plt.savefig(FIG_DIR / "distribuicao_notas.png", dpi=150); plt.close()

    # cauda longa
    counts = raw_int["recipe_id"].value_counts().to_numpy()
    share = np.cumsum(counts) / counts.sum()
    top1 = int(np.ceil(0.01 * len(counts)))
    resumo["interacoes_no_top_1pct_itens_pct"] = round(float(share[top1 - 1] * 100), 2)
    plt.plot(np.arange(1, len(counts) + 1) / len(counts) * 100, share * 100, color="#2E5496")
    plt.xlabel("% dos itens (ordenados por popularidade)")
    plt.ylabel("% acumulado das interacoes"); plt.title("Curva de cauda longa")
    plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(FIG_DIR / "cauda_longa.png", dpi=150); plt.close()

    # perfil nutricional
    rec = prepare_recipes(raw_rec)
    resumo["indice_nutricional"] = rec["health_index"].describe().round(4).to_dict()
    rec["health_index"].plot(kind="hist", bins=30, color="#2E5496")
    plt.title("Distribuicao do indice nutricional"); plt.xlabel("indice (0-1)")
    plt.tight_layout(); plt.savefig(FIG_DIR / "indice_nutricional.png", dpi=150); plt.close()

    # popularidade x saudabilidade
    pop = raw_int.groupby("recipe_id").size().rename("n_aval")
    merged = rec.set_index("recipe_id").join(pop, how="inner").dropna(subset=["n_aval"])
    if len(merged) > 10:
        resumo["correlacao_popularidade_indice_nutricional"] = round(
            float(np.corrcoef(np.log1p(merged["n_aval"]), merged["health_index"])[0, 1]), 4)

    inter = prepare_interactions(raw_int)
    resumo["interacoes_positivas_apos_filtro"] = int(len(inter))

    out = config.PROC_DIR / "eda_resumo.json"
    out.write_text(json.dumps(resumo, indent=2, ensure_ascii=False, default=str),
                   encoding="utf-8")
    print(json.dumps(resumo, indent=2, ensure_ascii=False, default=str)[:2000])
    print(f"\nfiguras em {FIG_DIR}\nresumo em {out}")


if __name__ == "__main__":
    main()
