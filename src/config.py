"""Parametros centrais do projeto Cozinha Consciente."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
for _d in (PROC_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

RECIPES_CSV = RAW_DIR / "RAW_recipes.csv"
INTERACTIONS_CSV = RAW_DIR / "RAW_interactions.csv"

RANDOM_STATE = 42

# --- construcao do feedback implicito ---
POSITIVE_RATING_THRESHOLD = 4      # nota >= 4 vira interacao positiva #
MIN_USER_INTERACTIONS = 5          # k-core de usuarios #
MIN_ITEM_INTERACTIONS = 5          # k-core de itens # 
DROP_ZERO_RATINGS = True           # nota 0 = ausencia de avaliacao #

# --- avaliacao --- #
TOP_K = 10
CANDIDATE_SAMPLE = 100             # 1 item positivo + 99 negativos amostrados #

# --- modelos --- #
SVD_FACTORS = 64
ITEMKNN_NEIGHBORS = 200
TFIDF_MIN_DF = 5
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MAX_FEATURES = 50000

# --- hibrido e reordenacao nutricional --- #
HYBRID_WEIGHTS = {"svd": 0.5, "itemknn": 0.3, "content": 0.2}
HEALTH_LAMBDA = 0.30               # peso do indice nutricional na reordenacao #
RERANK_POOL = 50                   # tamanho do pool reordenado antes do top-k #

# --- valores diarios de referencia usados pelo Food.com (PDV -> gramas) --- #
DAILY_VALUES = {
    "total_fat_g": 65.0,
    "sugar_g": 50.0,
    "sodium_mg": 2400.0,
    "protein_g": 50.0,
    "saturated_fat_g": 20.0,
    "carbohydrates_g": 300.0,
}

# limiares FSA/OMS adaptados para 100 kcal (baixo, alto) #
FSA_THRESHOLDS_PER_100KCAL = {
    "total_fat_g": (1.5, 8.0),
    "saturated_fat_g": (0.7, 2.5),
    "sugar_g": (2.5, 11.0),
    "sodium_mg": (60.0, 300.0),
}
