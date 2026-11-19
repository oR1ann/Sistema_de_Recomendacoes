"""Abre o site publicado num navegador e o acorda se o Streamlit Cloud o tiver colocado para dormir.

Usado pela rotina .github/workflows/manter-site-ativo.yml. Termina com erro se o site não
carregar, para que a falha apareça na aba Actions do GitHub.

Uso:  python tools/acordar_site.py [URL]
"""
import re
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://cozinha-consciente.streamlit.app/"
MARCA = "Cozinha Consciente"   # texto que só aparece quando o app carregou


def carregou(page) -> bool:
    for frame in page.frames:
        try:
            if MARCA in frame.inner_text("body", timeout=2000):
                return True
        except Exception:
            pass
    return False


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        acordar = page.get_by_role("button", name=re.compile(r"get this app back up", re.I))
        for _ in range(60):   # até ~3 min: tempo de acordar e carregar o catálogo
            if acordar.count():
                print("site dormindo: clicando para acordar")
                acordar.first.click()
            if carregou(page):
                print(f"site ativo: {URL}")
                nav.close()
                return
            page.wait_for_timeout(3000)
        nav.close()
    sys.exit(f"o site não carregou em 3 minutos: {URL}")


if __name__ == "__main__":
    main()
