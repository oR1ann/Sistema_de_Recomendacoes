"""Modelos de recomendacao usados na prova de conceito."""
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src import config


class Dataset:
    """Mapeia identificadores originais para indices densos e monta a matriz."""

    def __init__(self, train: pd.DataFrame, recipes: pd.DataFrame):
        self.users = np.sort(train["user_id"].unique())
        self.items = np.sort(train["recipe_id"].unique())
        self.u2i = {u: i for i, u in enumerate(self.users)}
        self.i2i = {it: i for i, it in enumerate(self.items)}
        rows = train["user_id"].map(self.u2i).to_numpy()
        cols = train["recipe_id"].map(self.i2i).to_numpy()
        data = np.ones(len(train), dtype=np.float32)
        self.R = sparse.csr_matrix(
            (data, (rows, cols)), shape=(len(self.users), len(self.items))
        )
        self.recipes = recipes.set_index("recipe_id").reindex(self.items)
        self.health = self.recipes["health_index"].fillna(0.5).to_numpy(dtype=np.float32)
        pop = np.asarray(self.R.sum(axis=0)).ravel()
        self.popularity = pop
        self.pop_norm = pop / pop.max() if pop.max() > 0 else pop
        self.seen = {u: set(self.R.indices[self.R.indptr[u]:self.R.indptr[u + 1]])
                     for u in range(len(self.users))}


class PopularityRecommender:
    name = "Popularidade"

    def fit(self, ds: Dataset):
        self.scores = ds.pop_norm.astype(np.float32)
        return self

    def score(self, u: int, candidates: np.ndarray) -> np.ndarray:
        return self.scores[candidates]


class ItemKNNRecommender:
    name = "ItemKNN (cosseno)"

    def fit(self, ds: Dataset):
        X = normalize(ds.R.T.tocsr(), norm="l2", axis=1)
        S = (X @ X.T).tolil()
        S.setdiag(0.0)
        S = S.tocsr()
        S.eliminate_zeros()
        self.S = _keep_topk_per_row(S, config.ITEMKNN_NEIGHBORS)
        self.R = ds.R
        return self

    def score(self, u: int, candidates: np.ndarray) -> np.ndarray:
        profile = self.R[u]
        s = np.asarray((profile @ self.S).todense()).ravel()
        return s[candidates]


class SVDRecommender:
    name = "PureSVD (fatoracao)"

    def fit(self, ds: Dataset):
        k = min(config.SVD_FACTORS, min(ds.R.shape) - 1)
        svd = TruncatedSVD(n_components=k, random_state=config.RANDOM_STATE)
        self.U = svd.fit_transform(ds.R).astype(np.float32)
        self.V = svd.components_.astype(np.float32)
        return self

    def score(self, u: int, candidates: np.ndarray) -> np.ndarray:
        return self.U[u] @ self.V[:, candidates]


class ContentTFIDFRecommender:
    name = "Conteudo (TF-IDF)"

    def fit(self, ds: Dataset):
        corpus = ds.recipes["content_txt"].fillna("").tolist()
        vec = TfidfVectorizer(
            min_df=config.TFIDF_MIN_DF,
            ngram_range=config.TFIDF_NGRAM_RANGE,
            max_features=config.TFIDF_MAX_FEATURES,
        )
        self.M = normalize(vec.fit_transform(corpus).astype(np.float32))
        self.vectorizer = vec
        profiles = ds.R @ self.M
        counts = np.asarray(ds.R.sum(axis=1)).ravel()
        counts[counts == 0] = 1.0
        self.P = normalize(sparse.diags(1.0 / counts) @ profiles)
        return self

    def score(self, u: int, candidates: np.ndarray) -> np.ndarray:
        return np.asarray((self.P[u] @ self.M[candidates].T).todense()).ravel()


class HybridRecommender:
    """Fusao ponderada de escores normalizados, com reordenacao nutricional."""

    def __init__(self, components: dict, weights: dict = None,
                 health_lambda: float = None):
        self.components = components
        self.weights = weights or config.HYBRID_WEIGHTS
        self.health_lambda = (config.HEALTH_LAMBDA if health_lambda is None
                              else health_lambda)
        self.name = (f"Hibrido (lambda={self.health_lambda:.2f})"
                     if self.health_lambda > 0 else "Hibrido (sem reordenacao)")

    def fit(self, ds: Dataset):
        self.ds = ds
        return self

    def score(self, u: int, candidates: np.ndarray) -> np.ndarray:
        total = np.zeros(len(candidates), dtype=np.float32)
        for key, model in self.components.items():
            total += self.weights.get(key, 0.0) * _minmax(model.score(u, candidates))
        if self.health_lambda > 0:
            health = self.ds.health[candidates]
            total = (1 - self.health_lambda) * _minmax(total) + self.health_lambda * health
        return total


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(np.min(x)), float(np.max(x))
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def _keep_topk_per_row(S: sparse.csr_matrix, k: int) -> sparse.csr_matrix:
    S = S.tocsr()
    rows, cols, vals = [], [], []
    for i in range(S.shape[0]):
        start, end = S.indptr[i], S.indptr[i + 1]
        idx, v = S.indices[start:end], S.data[start:end]
        if len(v) > k:
            top = np.argpartition(-v, k)[:k]
            idx, v = idx[top], v[top]
        rows.extend([i] * len(idx)); cols.extend(idx); vals.extend(v)
    return sparse.csr_matrix((vals, (rows, cols)), shape=S.shape, dtype=np.float32)
