"""Figuras da seção 4 (Resultados) a partir das tabelas de src/etapa4.py e src/tuning.py."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config

RES3 = config.BASE_DIR / "docs" / "resultados_etapa3"
RES4 = config.BASE_DIR / "docs" / "resultados_etapa4"
FIG = RES4 / "figuras"
FIG.mkdir(parents=True, exist_ok=True)

AZUL, LARANJA, CINZA = "#2E5496", "#C55A11", "#7F7F7F"
CORES = ["#7F7F7F", "#A9C4E8", "#5B8BD0", "#9DC183", "#2E5496", "#C55A11"]
CURTO = {"Popularidade": "Popularidade", "ItemKNN": "ItemKNN", "SVD": "SVD",
         "Conteudo": "Conteúdo", "Hibrido (lambda=0)": "Híbrido λ=0",
         "Hibrido (lambda=0.35)": "Híbrido λ=0,35"}


def curto(nome):
    for k, v in CURTO.items():
        if nome.startswith(k):
            return v
    return nome


def fig_protocolos(tab):
    prot = ["99 negativos uniformes", "99 negativos por popularidade", "ranking completo"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, p in zip(axes, prot):
        t = tab[tab["protocolo"] == p]
        nomes = [curto(m) for m in t["modelo"]]
        ax.barh(nomes, t["NDCG@10"], color=CORES)
        ax.invert_yaxis()
        ax.set_title(p, fontsize=10)
        ax.set_xlabel("NDCG@10")
        ax.grid(axis="x", alpha=.3)
        casas = 4 if t["NDCG@10"].max() < 0.05 else 3
        for y, v in enumerate(t["NDCG@10"]):
            ax.text(v, y, f" {v:.{casas}f}".replace(".", ","), va="center", fontsize=8)
        ax.set_xlim(0, t["NDCG@10"].max() * 1.25)
        if p != prot[0]:
            ax.set_yticklabels([])
    plt.tight_layout()
    plt.savefig(FIG / "ndcg_por_protocolo.png", dpi=150)
    plt.close()


def fig_alem_acuracia(tab):
    t = tab[tab["protocolo"] == "99 negativos uniformes"]
    nomes = [curto(m) for m in t["modelo"]]
    cols = [("Cobertura_catalogo", "Cobertura de catálogo"),
            ("Vies_popularidade", "Viés de popularidade"),
            ("IndiceNutricional@10", "Índice nutricional@10")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, (c, titulo) in zip(axes, cols):
        ax.barh(nomes, t[c], color=CORES)
        ax.invert_yaxis()
        ax.set_title(titulo, fontsize=10)
        ax.grid(axis="x", alpha=.3)
        for y, v in enumerate(t[c]):
            ax.text(v, y, f" {v:.3f}".replace(".", ","), va="center", fontsize=8)
        ax.set_xlim(0, t[c].max() * 1.3)
        if c != cols[0][0]:
            ax.set_yticklabels([])
    plt.tight_layout()
    plt.savefig(FIG / "metricas_alem_acuracia.png", dpi=150)
    plt.close()


def fig_lambda(curva_amostrada, curva_completa):
    fig, ax = plt.subplots(figsize=(6.8, 4))
    for c, nome, cor, mk in ((curva_amostrada, "99 negativos uniformes (teste)", AZUL, "o"),
                              (curva_completa, "ranking completo (teste)", LARANJA, "s")):
        rel = c["NDCG@10"] / c.loc[c["lambda"] == 0, "NDCG@10"].iloc[0]
        ax.plot(c["IndiceNutricional@10"], rel, marker=mk, color=cor, label=nome)
        sel = c["lambda"] == config.HEALTH_LAMBDA
        ax.scatter(c.loc[sel, "IndiceNutricional@10"], rel[sel], s=160, facecolors="none",
                   edgecolors="black")
    ax.axhline(0.9, color=CINZA, ls="--", lw=1)
    ax.text(ax.get_xlim()[0], 0.905, " perda de 10% (critério da validação)", fontsize=8, color=CINZA)
    ax.set_xlabel("índice nutricional médio das listas")
    ax.set_ylabel("NDCG@10 relativo a λ = 0")
    ax.set_title("Compromisso relevância × saudabilidade por protocolo")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, title="círculo: λ = 0,35", title_fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "curva_lambda_protocolos.png", dpi=150)
    plt.close()


def fig_faixas(seg):
    fig, ax = plt.subplots(figsize=(7, 4))
    modelos = [c for c in seg.columns if c not in ("faixa_historico", "usuarios")]
    x = np.arange(len(seg))
    for m, cor in zip(modelos, CORES):
        ax.plot(x, seg[m], marker="o", color=cor, label=curto(m), lw=2 if "Hibrido" in m else 1.3)
    ax.set_xticks(x, [f"{f}\n(n={n:,})".replace(",", ".") for f, n in zip(seg["faixa_historico"], seg["usuarios"])])
    ax.set_xlabel("interações positivas do usuário no treino")
    ax.set_ylabel("NDCG@10")
    ax.set_title("NDCG@10 por faixa de atividade (99 negativos uniformes)")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(FIG / "ndcg_por_faixa_atividade.png", dpi=150)
    plt.close()


def main():
    tab = pd.read_csv(RES4 / "etapa4_protocolos.csv")
    fig_protocolos(tab)
    fig_alem_acuracia(tab)
    fig_lambda(pd.read_csv(RES3 / "tuning_curva_lambda_test.csv"),
               pd.read_csv(RES4 / "etapa4_curva_lambda_ranking_completo.csv"))
    fig_faixas(pd.read_csv(RES4 / "etapa4_faixas_atividade.csv"))
    print("figuras em", FIG)


if __name__ == "__main__":
    main()
