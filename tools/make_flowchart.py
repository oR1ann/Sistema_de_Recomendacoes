"""Fluxograma da metodologia (Figura 1 do documento)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H, GAP = 2.9, 1.08, 0.36
COLS = {"A": 0.3, "B": 3.95, "C": 7.6}
TOP = 8.55
COLOR = {"A": "#DCE6F2", "B": "#E2F0D9", "C": "#FCE4D6"}
EDGE = {"A": "#2E5496", "B": "#548235", "C": "#C55A11"}
HEAD = {"A": "DADOS", "B": "MODELAGEM", "C": "AVALIAÇÃO E ANÁLISE"}

nodes = {
 "A": [("3.3  Aquisição da base", "Food.com (Kaggle):\nreceitas e interações"),
       ("3.4  Análise exploratória", "volume, notas, cauda longa,\nperfil nutricional"),
       ("3.5  Limpeza e preparação", "duplicatas, nota 0, nota ≥ 4,\nk-core 5/5, texto"),
       ("3.6  Índice nutricional", "vetor nutrition → índice\nde 0 a 1 (semáforo FSA)"),
       ("3.7  Divisão temporal", "leave-one-out: treino,\nvalidação e teste")],
 "B": [("3.8  Representações", "matriz usuário-item esparsa;\nTF-IDF das receitas"),
       ("3.9  Modelos base", "popularidade, ItemKNN,\nSVD e conteúdo"),
       ("3.10  Ajuste na validação", "fatores, vizinhos, pesos e\nnormalização (iterativo)"),
       ("3.11  Híbrido e reordenação", "fusão ponderada +\nλ · índice nutricional")],
 "C": [("3.12  Avaliação offline (teste)", "1 positivo + 99 negativos;\nmétricas @10"),
       ("3.13  Análise dos resultados", "inicial × ajustado;\nrelevância × saudabilidade"),
       ("3.14  Protótipo e extensão", "Etapa 4 (planejado)")],
}

fig, ax = plt.subplots(figsize=(11, 8.1))
ax.set_xlim(0, 11.0); ax.set_ylim(1.3, 9.4); ax.axis("off")
pos = {}
for c, items in nodes.items():
    x = COLS[c]
    ax.text(x + W / 2, TOP + 0.62, HEAD[c], ha="center", va="center", fontsize=11,
            fontweight="bold", color=EDGE[c])
    for i, (t, d) in enumerate(items):
        row = {"A": i, "B": 4 - i, "C": 1 + i}[c]
        y = TOP - row * (H + GAP) - H
        planned = t.startswith("3.14")
        ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.02,rounding_size=0.08",
                     fc="#F2F2F2" if planned else COLOR[c], ec="#7F7F7F" if planned else EDGE[c],
                     lw=1.6, ls="--" if planned else "-"))
        ax.text(x + W / 2, y + H - 0.27, t, ha="center", va="center", fontsize=9.2, fontweight="bold")
        ax.text(x + W / 2, y + 0.38, d, ha="center", va="center", fontsize=8.6, linespacing=1.25)
        pos[(c, i)] = (x, y)

def arrow(p, q, **kw):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.5, color="#404040", **kw))

for c, items in nodes.items():
    for i in range(len(items) - 1):
        x, y = pos[(c, i)]; _, y2 = pos[(c, i + 1)]
        if c == "B":   # fluxo de baixo para cima
            arrow((x + W / 2, y + H), (x + W / 2, y2))
        else:
            arrow((x + W / 2, y), (x + W / 2, y2 + H))
for a, ia, b, ib in (("A", 4, "B", 0), ("B", 3, "C", 0)):
    xa, ya = pos[(a, ia)]; xb, yb = pos[(b, ib)]
    arrow((xa + W, ya + H / 2), (xb, yb + H / 2))

# retroalimentação: a análise dos resultados (3.13) leva à revisão do pipeline (3.10)
xc, yc = pos[("C", 1)]; xb, yb = pos[("B", 2)]
ax.add_patch(FancyArrowPatch((xc, yc + H / 2), (xb + W, yb + H / 2), arrowstyle="-|>",
             mutation_scale=14, lw=1.5, color="#C55A11", linestyle="--"))
ax.text((xc + xb + W) / 2, yc + H / 2 + 0.12, "revisão", ha="center", va="bottom",
        fontsize=8, color="#C55A11")

plt.savefig("docs/fluxograma_metodologia.png", dpi=200, bbox_inches="tight", facecolor="white")
print("ok")
