"""Recomendação de receitas a partir dos ingredientes disponíveis, com reordenação nutricional.

Usuário do site não tem histórico na base (partida a frio), então a relevância vem da
compatibilidade com os ingredientes informados: a média entre a cobertura (fração da receita
que a pessoa já tem) e o aproveitamento (fração dos itens da pessoa que a receita usa).
A popularidade entra só como desempate leve.
A reordenação é a mesma do documento (seção 3.11):
    escore final = (1 - lambda) * minmax(relevância) + lambda * índice nutricional
"""
import re
import unicodedata
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ingredientes_pt import BASICOS, INGREDIENTES

warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")

DADOS = Path(__file__).parent / "dados" / "receitas.parquet"
PESO_POPULARIDADE = 0.15   # desempate entre receitas com a mesma cobertura
PESO_COBERTURA = 0.4       # o restante (0,6) vai para o aproveitamento dos itens da pessoa

RESTRICOES = {
    "Vegetariana": "vegetarian",
    "Vegana": "vegan",
    "Sem glúten": "gluten-free",
    "Baixo sódio": "low-sodium",
    "Baixo carboidrato": "low-carb",
    "Baixa caloria": "low-calorie",
    "Para diabéticos": "diabetic",
}


def sem_acento(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt.lower().strip())
    return "".join(c for c in txt if not unicodedata.combining(c))


_CHAVES = {sem_acento(k): k for k in INGREDIENTES}


def conhecido(item: str) -> bool:
    return sem_acento(item) in _CHAVES


def padroes(item: str) -> list:
    """Padrões em inglês para um ingrediente digitado (português do dicionário ou inglês livre)."""
    chave = _CHAVES.get(sem_acento(item))
    if chave:
        return INGREDIENTES[chave]
    return [re.escape(sem_acento(item))]


def _regex(pats):
    return re.compile(r"\b(?:" + "|".join(pats) + r")\b")


@dataclass
class Catalogo:
    receitas: pd.DataFrame
    ingredientes: pd.DataFrame = field(init=False)   # uma linha por (receita, ingrediente)

    def __post_init__(self):
        r = self.receitas
        r["pop_norm"] = np.log1p(r["avaliacoes_positivas"]) / np.log1p(r["avaliacoes_positivas"].max())
        r["tags_set"] = r["tags"].str.split("|").apply(set)
        ing = r[["ingredientes"]].assign(ingrediente=r["ingredientes"].str.split("|")).explode("ingrediente")
        ing["ingrediente"] = ing["ingrediente"].str.lower().str.strip()
        ing["basico"] = ing["ingrediente"].str.fullmatch("|".join(f"(?:{p})" for p in BASICOS))
        self.ingredientes = ing[["ingrediente", "basico"]]


def carregar(caminho=DADOS) -> Catalogo:
    return Catalogo(pd.read_parquet(caminho))


def recomendar(cat: Catalogo, itens, considerar_basicos=True, restricoes=(), tempo_max=None,
               max_faltando=None, excluir=(), lam=0.35, k=10) -> pd.DataFrame:
    itens = [i for i in itens if i.strip()]
    if not itens:
        return pd.DataFrame()
    ing = cat.ingredientes
    # um indicador por item do usuário: a receita usa esse item?
    por_item = {i: ing["ingrediente"].str.contains(_regex(padroes(i))) & ~ing["basico"] for i in itens}
    tem = np.logical_or.reduce(list(por_item.values()))
    disponivel = tem | (ing["basico"] if considerar_basicos else False)

    n_itens_usados = sum(s.groupby(level=0).any().astype(int) for s in por_item.values())
    n_disp = disponivel.groupby(level=0).sum()
    n_total = ing.groupby(level=0).size()
    n_nao_basicos = (~ing["basico"]).groupby(level=0).sum()

    r = cat.receitas.assign(n_usuario=n_itens_usados, n_disponiveis=n_disp, n_total=n_total,
                            n_nao_basicos=n_nao_basicos)
    r["faltando"] = r["n_total"] - r["n_disponiveis"]
    r["cobertura"] = r["n_disponiveis"] / r["n_total"]          # quanto da receita já está em casa
    r["aproveitamento"] = r["n_usuario"] / len(itens)          # quanto do que está em casa a receita usa

    filtro = r["n_usuario"] >= 1
    if len(itens) > 1:  # evita "receitas" de um ingrediente só (arroz com água e sal)
        filtro &= r["n_nao_basicos"] >= 2
    for nome in restricoes:
        tag = RESTRICOES[nome]
        filtro &= r["tags_set"].apply(lambda s, t=tag: t in s)
    if tempo_max:
        filtro &= r["minutes"] <= tempo_max
    if max_faltando is not None:
        filtro &= r["faltando"] <= max_faltando
    excluir = [e for e in excluir if e.strip()]
    if excluir:
        proibido = ing["ingrediente"].str.contains(_regex([p for e in excluir for p in padroes(e)]))
        filtro &= ~proibido.groupby(level=0).any()
    r = r[filtro]
    if r.empty:
        return r

    relev = ((1 - PESO_POPULARIDADE) * (PESO_COBERTURA * r["cobertura"]
                                        + (1 - PESO_COBERTURA) * r["aproveitamento"])
             + PESO_POPULARIDADE * r["pop_norm"])
    lo, hi = relev.min(), relev.max()
    relev_n = (relev - lo) / (hi - lo) if hi > lo else relev * 0
    r = r.assign(relevancia=relev_n, escore=(1 - lam) * relev_n + lam * r["health_index"])
    return r.sort_values(["escore", "cobertura"], ascending=False).head(k)


def detalhar(cat: Catalogo, receita_idx, itens, considerar_basicos=True):
    """Separa os ingredientes da receita em: que você tem / básicos / faltam."""
    ing = cat.ingredientes.loc[[receita_idx]]
    tem, basicos, faltam = [], [], []
    for nome, basico in zip(ing["ingrediente"], ing["basico"]):
        dono = next((i for i in itens if _regex(padroes(i)).search(nome)), None)
        if dono:
            tem.append((nome, dono))
        elif basico and considerar_basicos:
            basicos.append(nome)
        else:
            faltam.append(nome)
    return tem, basicos, faltam


def semaforo(indice: float):
    if indice >= 0.75:
        return "bom", "🟢"
    if indice >= 0.5:
        return "médio", "🟡"
    return "baixo", "🔴"


def nome_bonito(nome: str) -> str:
    nome = re.sub(r"\s+", " ", str(nome)).strip()
    nome = re.sub(r"\b(\w+) s\b", r"\1's", nome)
    return nome[:1].upper() + nome[1:]


def link_foodcom(nome: str, recipe_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(nome).lower()).strip("-")
    return f"https://www.food.com/recipe/{slug}-{recipe_id}"
