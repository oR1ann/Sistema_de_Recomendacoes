"""Identidade visual do site: paleta, tipografia, ícones e estilos dos componentes."""
from urllib.parse import quote

PALETA = {
    "verde": "#2F6B4F",       # cor principal (sálvia escura)
    "verde_claro": "#E4EFE7",
    "terracota": "#C8603A",   # destaque
    "terracota_claro": "#F8E6DC",
    "creme": "#FBF8F3",       # fundo
    "areia": "#F2ECE2",       # superfícies
    "borda": "#E5DDD0",
    "texto": "#1F2A24",
    "suave": "#5F6B63",
    "bom": "#2F8F5B",
    "medio": "#C9921A",
    "baixo": "#C0503A",
}

# ícones de linha (24x24, traço) para usar no lugar de emojis
_SVG = {
    "relogio": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "cesta": '<path d="M5 10h14l-1.5 9h-11z"/><path d="M9 10l3-6 3 6"/>',
    "carrinho": '<circle cx="9" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/>'
                '<path d="M3 4h2l2.4 11h10.2L20 8H6.2"/>',
    "folha": '<path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15"/><path d="M5 19l7-7"/>',
    "seta": '<path d="M7 17L17 7"/><path d="M9 7h8v8"/>',
    "lupa": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
    "camadas": '<path d="M12 4l8 4-8 4-8-4z"/><path d="M4 12l8 4 8-4"/><path d="M4 16l8 4 8-4"/>',
    "balanca": '<path d="M12 4v16"/><path d="M5 20h14"/><path d="M4 8h16"/>'
               '<path d="M6 8l-3 6h6z"/><path d="M18 8l-3 6h6z"/>',
}


def icone(nome, tamanho=16):
    """O st.html remove <svg>; o ícone vira uma máscara CSS que herda a cor do texto."""
    return f'<i class="cc-i cc-i-{nome}" style="width:{tamanho}px;height:{tamanho}px" aria-hidden="true"></i>'


def _css_icones():
    regras = [".cc-i { display: inline-block; flex: none; vertical-align: -3px; background-color: currentColor;"
              " -webkit-mask: var(--cc-svg) no-repeat center / contain; mask: var(--cc-svg) no-repeat center / contain; }"]
    for nome, corpo in _SVG.items():
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
               f"stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>{corpo.replace(chr(34), chr(39))}</svg>")
        regras.append(f'.cc-i-{nome} {{ --cc-svg: url("data:image/svg+xml;utf8,{quote(svg)}"); }}')
    return "\n".join(regras)


P = PALETA
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Inter:wght@400;500;600&display=swap');

.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp td, .stApp th {{
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
[data-testid="stIconMaterial"] {{ font-family: 'Material Symbols Rounded' !important; }}
h1, h2, h3, h4, .cc-serif {{ font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.01em; }}
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 4rem; max-width: 860px; }}

/* topo */
.cc-hero {{
  background: linear-gradient(135deg, {P['verde']} 0%, #24543E 100%);
  color: #fff; border-radius: 20px; padding: 2.1rem 2.2rem 2rem; margin-bottom: 1.4rem;
  position: relative; overflow: hidden;
}}
.cc-hero::after {{
  content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px;
  border-radius: 50%; background: {P['terracota']}; opacity: .9;
}}
.cc-hero::before {{
  content: ""; position: absolute; right: 90px; bottom: -90px; width: 170px; height: 170px;
  border-radius: 50%; background: #F2C7A8; opacity: .35;
}}
.cc-eyebrow {{ font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; opacity: .8;
  font-weight: 600; position: relative; z-index: 1; }}
.cc-hero h1 {{ color: #fff; font-size: 2.6rem; line-height: 1.05; margin: .35rem 0 .7rem; padding: 0;
  position: relative; z-index: 1; }}
.cc-hero p {{ font-size: 1.06rem; line-height: 1.55; max-width: 34rem; margin: 0; opacity: .94;
  position: relative; z-index: 1; }}

/* abas */
.stTabs [data-baseweb="tab-list"] {{ gap: .4rem; border-bottom: 1px solid {P['borda']}; }}
.stTabs [data-baseweb="tab"] {{ padding: .55rem .2rem; margin-right: 1rem; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: {P['verde']} !important; }}

/* formulário */
[data-testid="stForm"] {{ background: #fff; border: 1px solid {P['borda']}; border-radius: 16px;
  padding: 1.2rem 1.3rem .6rem; box-shadow: 0 1px 2px rgba(31,42,36,.04); }}
.stFormSubmitButton button {{ background: {P['terracota']} !important; border-color: {P['terracota']} !important;
  color: #fff !important; font-weight: 600; padding: .55rem 1.4rem; border-radius: 999px; }}
.stFormSubmitButton button:hover {{ filter: brightness(.94); }}

/* resumo dos resultados */
.cc-resumo {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: .4rem;
  margin: 1.6rem 0 .8rem; }}
.cc-resumo h3 {{ margin: 0; font-size: 1.45rem; }}
.cc-resumo span {{ color: {P['suave']}; font-size: .9rem; }}
.cc-legenda {{ display: flex; flex-wrap: wrap; gap: .35rem; margin: 0 0 .9rem; }}
[data-testid="InputInstructions"] {{ display: none; }}

/* cartão de receita */
.cc-card {{ background: #fff; border: 1px solid {P['borda']}; border-radius: 16px; padding: 1.15rem 1.25rem 1rem;
  margin-bottom: .9rem; box-shadow: 0 1px 2px rgba(31,42,36,.04); transition: box-shadow .15s, transform .15s; }}
.cc-card:hover {{ box-shadow: 0 6px 18px rgba(31,42,36,.08); transform: translateY(-1px); }}
.cc-top {{ display: flex; gap: .9rem; align-items: flex-start; }}
.cc-rank {{ font-family: 'Fraunces', serif; font-size: 1.5rem; color: {P['terracota']}; line-height: 1.1;
  min-width: 2rem; }}
.cc-title {{ flex: 1; }}
.cc-title a {{ font-family: 'Fraunces', serif; font-size: 1.22rem; font-weight: 650; color: {P['texto']};
  text-decoration: none; line-height: 1.25; }}
.cc-title a:hover {{ color: {P['verde']}; text-decoration: underline; text-underline-offset: 3px; }}
.cc-desc {{ font-size: .95rem; color: {P['texto']}; margin-top: .25rem; line-height: 1.4; }}
.cc-orig {{ font-size: .78rem; color: {P['suave']}; margin-top: .2rem; line-height: 1.35; }}
.cc-title .cc-orig a {{ font-family: 'Inter', sans-serif; font-size: inherit; font-weight: 500;
  color: {P['verde']}; text-decoration: underline; text-underline-offset: 2px; }}
.cc-badge {{ white-space: nowrap; font-size: .78rem; font-weight: 600; padding: .28rem .65rem; border-radius: 999px; }}
.cc-bom {{ background: #E3F2E9; color: {P['bom']}; }}
.cc-medio {{ background: #FBF0D9; color: #97690C; }}
.cc-baixo {{ background: #F8E2DC; color: {P['baixo']}; }}
.cc-meta {{ display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; color: {P['suave']}; font-size: .88rem;
  margin: .7rem 0 .55rem 2.9rem; }}
.cc-meta span {{ display: inline-flex; align-items: center; gap: .35rem; }}
.cc-bar {{ height: 6px; background: {P['areia']}; border-radius: 999px; margin: 0 0 .7rem 2.9rem; overflow: hidden; }}
.cc-bar div {{ height: 100%; background: {P['verde']}; border-radius: 999px; }}
.cc-why {{ margin: 0 0 .65rem 2.9rem; font-size: .95rem; line-height: 1.5; color: {P['texto']}; }}
.cc-chips {{ display: flex; flex-wrap: wrap; gap: .35rem; margin-left: 2.9rem; }}
.cc-chip {{ font-size: .78rem; padding: .22rem .6rem; border-radius: 999px; border: 1px solid transparent; }}
.cc-tem {{ background: {P['verde_claro']}; color: {P['verde']}; }}
.cc-basico {{ background: {P['areia']}; color: {P['suave']}; }}
.cc-falta {{ background: #fff; color: {P['terracota']}; border-color: #EBC2AE; }}
.cc-card details {{ margin: .7rem 0 0 2.9rem; font-size: .86rem; color: {P['suave']}; }}
.cc-card summary {{ cursor: pointer; color: {P['verde']}; font-weight: 500; }}
.cc-nutri {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .4rem .8rem; margin-top: .5rem; }}
.cc-nutri b {{ display: block; color: {P['texto']}; font-weight: 600; }}

/* como funciona / sobre */
.cc-passos {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .9rem; margin: 1rem 0 1.4rem; }}
.cc-passo {{ background: #fff; border: 1px solid {P['borda']}; border-radius: 16px; padding: 1.1rem; }}
.cc-passo .cc-num {{ display: inline-flex; align-items: center; justify-content: center; width: 2.1rem; height: 2.1rem;
  border-radius: 50%; background: {P['verde_claro']}; color: {P['verde']}; margin-bottom: .6rem; }}
.cc-passo h4 {{ font-family: 'Fraunces', serif; margin: 0 0 .35rem; font-size: 1.05rem; }}
.cc-passo p {{ margin: 0; font-size: .9rem; color: {P['suave']}; line-height: 1.5; }}
.cc-formula {{ background: {P['areia']}; border-radius: 12px; padding: .9rem 1.1rem; font-size: .95rem;
  margin: .6rem 0 1rem; line-height: 1.6; }}
.cc-semaforo {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0 1rem; }}
.cc-aviso {{ border-left: 3px solid {P['terracota']}; background: {P['terracota_claro']}; padding: .8rem 1rem;
  border-radius: 0 10px 10px 0; font-size: .9rem; line-height: 1.5; }}
.cc-equipe {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; margin: .6rem 0 1.2rem; }}
.cc-equipe div {{ background: #fff; border: 1px solid {P['borda']}; border-radius: 12px; padding: .7rem .9rem;
  font-size: .92rem; }}
.cc-equipe small {{ display: block; color: {P['suave']}; font-size: .8rem; }}
.cc-ods {{ display: flex; flex-wrap: wrap; gap: .45rem; margin: .4rem 0 1.2rem; }}
.cc-ods span {{ background: {P['verde']}; color: #fff; font-size: .8rem; padding: .3rem .7rem; border-radius: 999px; }}
.cc-rodape {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid {P['borda']}; color: {P['suave']};
  font-size: .8rem; line-height: 1.5; }}
.cc-rodape a {{ color: {P['verde']}; }}

{_css_icones()}
.cc-title a .cc-i {{ margin-left: 5px; opacity: .45; vertical-align: -1px; }}
.cc-passo .cc-num .cc-i, .cc-formula .cc-i {{ vertical-align: -3px; }}

@media (max-width: 640px) {{
  .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  .cc-hero {{ padding: 1.6rem 1.4rem; border-radius: 16px; }}
  .cc-hero h1 {{ font-size: 2rem; }}
  .cc-hero::after {{ width: 140px; height: 140px; right: -50px; top: -50px; }}
  .cc-top {{ flex-wrap: wrap; }}
  .cc-meta, .cc-bar, .cc-why, .cc-chips, .cc-card details {{ margin-left: 0; }}
  .cc-passos, .cc-equipe {{ grid-template-columns: 1fr; }}
  .cc-nutri {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
</style>
"""
