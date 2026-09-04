"""Decomposicao do vetor nutricional do Food.com e calculo do indice nutricional."""
import ast
import numpy as np
import pandas as pd

from src import config

NUTRITION_FIELDS = [
    "calories", "total_fat_pdv", "sugar_pdv", "sodium_pdv",
    "protein_pdv", "saturated_fat_pdv", "carbohydrates_pdv",
]


def parse_nutrition(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma a coluna 'nutrition' (lista em texto) em sete colunas numericas."""
    parsed = df["nutrition"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )
    mat = pd.DataFrame(parsed.tolist(), columns=NUTRITION_FIELDS, index=df.index)
    return pd.concat([df.drop(columns=["nutrition"]), mat], axis=1)


def pdv_to_grams(df: pd.DataFrame) -> pd.DataFrame:
    """Converte percentual do valor diario em quantidade absoluta por porcao."""
    dv = config.DAILY_VALUES
    out = df.copy()
    out["total_fat_g"] = df["total_fat_pdv"] / 100.0 * dv["total_fat_g"]
    out["sugar_g"] = df["sugar_pdv"] / 100.0 * dv["sugar_g"]
    out["sodium_mg"] = df["sodium_pdv"] / 100.0 * dv["sodium_mg"]
    out["protein_g"] = df["protein_pdv"] / 100.0 * dv["protein_g"]
    out["saturated_fat_g"] = df["saturated_fat_pdv"] / 100.0 * dv["saturated_fat_g"]
    out["carbohydrates_g"] = df["carbohydrates_pdv"] / 100.0 * dv["carbohydrates_g"]
    return out


def health_index(df: pd.DataFrame) -> pd.Series:
    """Indice nutricional em [0, 1]; 1 = perfil mais adequado.

    Adaptacao do escore FSA (semaforo nutricional) normalizado por 100 kcal.
    Cada um dos quatro nutrientes criticos recebe 1 (baixo), 2 (medio) ou
    3 (alto); o escore bruto varia de 4 a 12 e e invertido e reescalado.
    """
    kcal = df["calories"].clip(lower=1.0)
    factor = 100.0 / kcal
    score = np.zeros(len(df), dtype=float)
    for col, (low, high) in config.FSA_THRESHOLDS_PER_100KCAL.items():
        per100 = df[col].fillna(0.0) * factor
        pts = np.where(per100 <= low, 1.0, np.where(per100 <= high, 2.0, 3.0))
        score += pts
    return ((12.0 - score) / 8.0).clip(0.0, 1.0)
