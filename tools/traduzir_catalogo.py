"""Traduz para português os ingredientes do catálogo do site.

Usa o modelo inglês→português do Argos Translate (código aberto, roda no computador), em lote.
Cada texto vai em minúsculas e com ponto final, o que evita traduções degeneradas do modelo
em textos curtos. Traduções suspeitas (muito curtas ou repetitivas) são descartadas e o site
mostra o original. A busca continua usando os ingredientes em inglês; a tradução é só exibição.

Os nomes das receitas não são traduzidos: escritos livremente pelos usuários do Food.com (siglas,
apelidos, frases soltas), saíam literais demais com este modelo e com o NLLB-200. O site mostra o
nome original com uma descrição em português montada a partir da categoria e dos ingredientes.

Uso:  python -m tools.traduzir_catalogo
Saída: app/dados/traducao_ingredientes.parquet
"""
import pandas as pd

from src import config

DADOS = config.BASE_DIR / "app" / "dados"
PALAVRAS_LIGACAO = {"de", "do", "da", "dos", "das", "e", "com", "em", "a", "o", "ao", "à", "para", "sem"}


def tradutor():
    import argostranslate.package as pkg
    import ctranslate2
    import sentencepiece as spm

    pkg.update_package_index()
    if not any(p.from_code == "en" and p.to_code == "pt" for p in pkg.get_installed_packages()):
        disp = next(p for p in pkg.get_available_packages() if p.from_code == "en" and p.to_code == "pt")
        pkg.install_from_path(disp.download())
    p = next(p for p in pkg.get_installed_packages() if p.from_code == "en" and p.to_code == "pt")
    sp = spm.SentencePieceProcessor(model_file=str(p.package_path / "sentencepiece.model"))
    tr = ctranslate2.Translator(str(p.package_path / "model"), device="cpu", inter_threads=4)

    def traduzir(textos):
        toks = [sp.encode(t.lower().strip() + ".", out_type=str) for t in textos]
        res = tr.translate_batch(toks, beam_size=4, max_decoding_length=64,
                                 batch_type="tokens", max_batch_size=4096)
        return ["".join(r.hypotheses[0]).replace("▁", " ").strip().rstrip(".").strip() for r in res]
    return traduzir


def suspeita(orig: str, trad: str) -> bool:
    po, pt = orig.split(), trad.split()
    if not pt or len(pt) < 0.5 * len(po):
        return True
    conteudo = [w.lower().strip(",;:") for w in pt if w.lower() not in PALAVRAS_LIGACAO]
    return bool(conteudo) and (max(conteudo.count(w) for w in conteudo) >= 3
                               or len(set(conteudo)) < 0.6 * len(conteudo))


def em_blocos(textos, traduzir, nome, tamanho=2000):
    saida = []
    for i in range(0, len(textos), tamanho):
        saida += traduzir(textos[i:i + tamanho])
        print(f"{nome}: {min(i + tamanho, len(textos))}/{len(textos)}", flush=True)
    return saida


def main():
    rec = pd.read_parquet(DADOS / "receitas.parquet")
    traduzir = tradutor()

    ingred = sorted({i.lower().strip() for lst in rec["ingredientes"].str.split("|") for i in lst})
    ing_pt = em_blocos(ingred, traduzir, "ingredientes")
    ti = pd.DataFrame({"ingrediente": ingred, "ingrediente_pt": ing_pt})
    ti.loc[[suspeita(a, b) for a, b in zip(ti["ingrediente"], ti["ingrediente_pt"])], "ingrediente_pt"] = None

    ti.to_parquet(DADOS / "traducao_ingredientes.parquet", index=False, compression="zstd")
    print(f"ingredientes traduzidos: {ti['ingrediente_pt'].notna().sum()}/{len(ti)}")


if __name__ == "__main__":
    main()
