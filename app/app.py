"""Cozinha Consciente: site do protótipo (Streamlit).

Execução local (na raiz do repositório):  streamlit run app/app.py
"""
import html
import re

import streamlit as st

import recomendador as R
from estilo import CSS, icone
from ingredientes_pt import INGREDIENTES

REPO = "https://github.com/oR1ann/Sistema_de_Recomendacoes"
DOCUMENTO = f"{REPO}/blob/main/docs/Projeto_Aplicado_III_Cozinha_Consciente.pdf"
ATALHOS = ["arroz", "feijão", "frango", "ovo", "tomate", "cebola", "alho", "batata",
           "cenoura", "macarrão", "queijo", "banana"]

st.set_page_config(page_title="Cozinha Consciente", page_icon=":material/eco:", layout="centered")
st.html(CSS)


@st.cache_resource(show_spinner="Carregando receitas...")
def catalogo():
    return R.carregar()


def lista(texto):
    return [x.strip() for x in re.split(r"[,;\n]", texto or "") if x.strip()]


def esc(txt):
    return html.escape(str(txt))


def cartao(pos, idx, r, itens, basicos):
    tem, bas, faltam = R.detalhar(cat, idx, itens, basicos)
    nivel, _ = R.semaforo(r["health_index"])
    classe = {"bom": "cc-bom", "médio": "cc-medio", "baixo": "cc-baixo"}[nivel]
    indice = f"{r['health_index']:.2f}".replace(".", ",")
    usados = sorted({dono for _, dono in tem})
    aproveit = int(round(100 * r["n_usuario"] / len(itens)))
    tempo = f"{int(r['minutes'])} min" if r["minutes"] < 600 else "preparo longo"
    motivo = f"Usa {esc(', '.join(usados))}"
    if not faltam:
        motivo += " e não exige compras."
    else:
        motivo += "; falta comprar 1 item." if len(faltam) == 1 else f"; faltam {len(faltam)} itens para comprar."
    chips = "".join(f'<span class="cc-chip cc-tem" title="{esc(d)}">{esc(n)}</span>' for n, d in tem)
    chips += "".join(f'<span class="cc-chip cc-basico">{esc(n)}</span>' for n in bas)
    chips += "".join(f'<span class="cc-chip cc-falta">{esc(n)}</span>' for n in faltam)
    nutri = [("Calorias", f"{r['calories']:.0f} kcal"), ("Proteína", f"{r['protein_g']:.1f} g"),
             ("Gordura", f"{r['total_fat_g']:.1f} g"), ("Gord. saturada", f"{r['saturated_fat_g']:.1f} g"),
             ("Açúcar", f"{r['sugar_g']:.1f} g"), ("Sódio", f"{r['sodium_mg']:.0f} mg")]
    nutri_html = "".join(f"<div>{k}<b>{v.replace('.', ',')}</b></div>" for k, v in nutri)
    link = R.link_foodcom(r["name"], r["recipe_id"])
    return (
        f'<div class="cc-card">'
        f'<div class="cc-top"><span class="cc-rank">{pos:02d}</span>'
        f'<div class="cc-title"><a href="{esc(link)}" target="_blank" rel="noopener">'
        f'{esc(R.nome_bonito(r["name"]))}{icone("seta", 14)}</a></div>'
        f'<span class="cc-badge {classe}">Índice {indice} · {nivel}</span></div>'
        f'<div class="cc-meta"><span>{icone("cesta")} {int(r["n_usuario"])} de {len(itens)} dos seus ingredientes</span>'
        f'<span>{icone("carrinho")} {len(faltam)} para comprar</span>'
        f'<span>{icone("relogio")} {tempo}</span></div>'
        f'<div class="cc-bar" title="Aproveitamento dos seus ingredientes"><div style="width:{aproveit}%"></div></div>'
        f'<p class="cc-why">{motivo}</p>'
        f'<div class="cc-chips">{chips}</div>'
        f'<details><summary>Nutrientes por porção</summary><div class="cc-nutri">{nutri_html}</div></details>'
        f'</div>'
    )


cat = catalogo()

st.html(
    '<div class="cc-hero"><div class="cc-eyebrow">Projeto Aplicado III · Mackenzie</div>'
    '<h1>Cozinha Consciente</h1>'
    '<p>Receitas a partir do que você já tem em casa, ordenadas para aproveitar os seus ingredientes '
    'e favorecer escolhas mais equilibradas.</p></div>'
)

aba_busca, aba_como, aba_sobre = st.tabs([":material/search: Receitas",
                                          ":material/info: Como funciona",
                                          ":material/groups: Sobre"])

# ------------------------------------------------------------------------ busca
with aba_busca:
    with st.form("busca"):
        texto = st.text_input("O que você tem em casa?", placeholder="Ex.: frango, arroz, tomate, cebola, alho",
                              help="Separe os ingredientes por vírgula. Use português; ingredientes fora da "
                                   "lista podem ser escritos em inglês.")
        atalhos = st.pills("Ou toque para adicionar", ATALHOS, selection_mode="multi")
        c1, c2 = st.columns(2)
        restricoes = c1.multiselect("Restrições alimentares", list(R.RESTRICOES), placeholder="Nenhuma")
        tempo = c2.select_slider("Tempo máximo de preparo", options=[15, 30, 45, 60, 90, 120, "sem limite"],
                                 value="sem limite",
                                 format_func=lambda v: v if isinstance(v, str) else f"{v} min")
        with st.expander("Mais opções"):
            lam = st.slider("Prioridade para alimentação saudável", 0.0, 0.6, 0.35, 0.05,
                            help="0 ordena só pelo aproveitamento dos seus ingredientes. Valores maiores dão "
                                 "mais peso ao índice nutricional da receita.")
            max_falt = st.select_slider("Ingredientes que podem faltar", options=[0, 1, 2, 3, 4, 5, "qualquer"],
                                        value="qualquer")
            excluir = lista(st.text_input("Não quero receitas com", placeholder="Ex.: amendoim, leite",
                                          help="Alergias ou ingredientes que você não come."))
            basicos = st.checkbox("Tenho os básicos (sal, pimenta-do-reino, água, óleo e açúcar)", value=True)
            k = st.slider("Quantidade de receitas", 5, 20, 10)
        st.form_submit_button("Buscar receitas", icon=":material/search:")

    itens = list(dict.fromkeys(lista(texto) + list(atalhos or [])))
    if not itens:
        st.html(f'<div class="cc-formula">{icone("lupa")} Digite ou toque nos ingredientes que você tem e '
                f'clique em <b>Buscar receitas</b>. O site procura entre 37.851 receitas avaliadas.</div>')
    else:
        desconhecidos = [i for i in itens if not R.conhecido(i)]
        if desconhecidos:
            st.caption("Buscados como escritos, em inglês, por não estarem na lista em português: "
                       + ", ".join(desconhecidos))
        res = R.recomendar(cat, itens, considerar_basicos=basicos, restricoes=restricoes,
                           tempo_max=None if tempo == "sem limite" else tempo,
                           max_faltando=None if max_falt == "qualquer" else max_falt,
                           excluir=excluir, lam=lam, k=k)
        if res.empty:
            st.warning("Nenhuma receita atende a todos os filtros. Tente permitir mais ingredientes faltando, "
                       "aumentar o tempo de preparo ou remover alguma restrição.")
        else:
            st.html(f'<div class="cc-resumo"><h3>{len(res)} sugestões</h3>'
                    f'<span>com {esc(", ".join(itens))}</span></div>'
                    '<div class="cc-legenda"><span class="cc-chip cc-tem">você tem</span>'
                    '<span class="cc-chip cc-basico">básico de despensa</span>'
                    '<span class="cc-chip cc-falta">falta comprar</span></div>')
            st.html("".join(cartao(p, idx, r, itens, basicos) for p, (idx, r) in enumerate(res.iterrows(), 1)))

# ------------------------------------------------------------------------ como funciona
with aba_como:
    st.markdown("### Como as sugestões são escolhidas")
    st.html(
        '<div class="cc-passos">'
        f'<div class="cc-passo"><span class="cc-num">{icone("cesta", 18)}</span><h4>1. Você informa</h4>'
        '<p>Os ingredientes que tem em casa e, se quiser, restrições, tempo de preparo e o que evitar.</p></div>'
        f'<div class="cc-passo"><span class="cc-num">{icone("camadas", 18)}</span><h4>2. O site compara</h4>'
        '<p>Cada uma das 37.851 receitas é comparada com a sua lista: quanto dela você já tem e quanto dos '
        'seus ingredientes ela aproveita.</p></div>'
        f'<div class="cc-passo"><span class="cc-num">{icone("balanca", 18)}</span><h4>3. E equilibra</h4>'
        '<p>A lista é reordenada pelo índice nutricional, com o peso que você escolher em '
        '"Prioridade para alimentação saudável".</p></div></div>'
    )
    st.markdown("#### A conta por trás da lista")
    st.html(
        '<div class="cc-formula"><b>Relevância</b> = 0,85 × (0,4 × cobertura + 0,6 × aproveitamento) '
        '+ 0,15 × popularidade<br><b>Pontuação final</b> = (1 − λ) × relevância + λ × índice nutricional</div>'
    )
    st.markdown(
        "- **Cobertura:** fração dos ingredientes da receita que você já tem.\n"
        "- **Aproveitamento:** fração dos seus ingredientes que a receita usa. É o que ajuda a evitar desperdício.\n"
        "- **Popularidade:** quantas avaliações positivas a receita recebeu; serve só como desempate.\n"
        "- **λ (lambda):** começa em 0,35, valor escolhido na avaliação do projeto. Em 0, a lista ignora o "
        "índice nutricional; perto de 0,6, a saúde passa a pesar mais que o aproveitamento."
    )
    st.markdown("#### O índice nutricional")
    st.markdown(
        "Inspirado no semáforo nutricional usado em rótulos de alimentos. Quatro nutrientes críticos são "
        "calculados por 100 kcal e recebem 1, 2 ou 3 pontos; a soma é convertida para uma escala de 0 a 1, "
        "em que **1 é o perfil mais equilibrado**."
    )
    st.html('<div class="cc-semaforo"><span class="cc-badge cc-bom">0,75 a 1 · bom</span>'
            '<span class="cc-badge cc-medio">0,50 a 0,74 · médio</span>'
            '<span class="cc-badge cc-baixo">abaixo de 0,50 · baixo</span></div>')
    st.markdown(
        "| Nutriente (por 100 kcal) | Baixo | Médio | Alto |\n|---|---|---|---|\n"
        "| Gordura total | até 1,5 g | até 8 g | acima de 8 g |\n"
        "| Gordura saturada | até 0,7 g | até 2,5 g | acima de 2,5 g |\n"
        "| Açúcar | até 2,5 g | até 11 g | acima de 11 g |\n"
        "| Sódio | até 60 mg | até 300 mg | acima de 300 mg |"
    )
    st.markdown("#### Por que não usar o histórico de avaliações?")
    st.markdown(
        "Na avaliação do projeto, o melhor modelo combinava popularidade, filtragem colaborativa e conteúdo. "
        "Esses modelos precisam do histórico de avaliações da pessoa, que quem visita o site não tem. Além "
        "disso, sobre o catálogo inteiro, a combinação passava a sugerir sempre as mesmas receitas populares. "
        "Por isso, o site ordena pelos ingredientes que você informa e mantém a mesma reordenação nutricional "
        "avaliada no trabalho."
    )
    st.html('<div class="cc-aviso">O índice é uma aproximação para ordenar receitas, não uma avaliação '
            'nutricional. Ele não substitui a orientação de um profissional de saúde nem o Guia Alimentar para '
            'a População Brasileira. As receitas vêm da base pública Food.com, em inglês, e o link de cada uma '
            'leva ao modo de preparo original.</div>')

# ------------------------------------------------------------------------ sobre
with aba_sobre:
    st.markdown("### Sobre o projeto")
    st.markdown(
        "O **Cozinha Consciente** foi desenvolvido no componente Projeto Aplicado III do curso de Tecnologia "
        "em Banco de Dados da Universidade Presbiteriana Mackenzie. A proposta é ajudar famílias e "
        "organizações comunitárias a decidir o que cozinhar com o que já têm, reduzindo o desperdício "
        "doméstico de alimentos e favorecendo refeições mais equilibradas."
    )
    st.markdown("#### Objetivos de Desenvolvimento Sustentável")
    st.html('<div class="cc-ods"><span>ODS 2 · Fome zero</span><span>ODS 3 · Saúde e bem-estar</span>'
            '<span>ODS 4 · Educação de qualidade</span><span>ODS 12 · Consumo responsável</span></div>')
    st.markdown("#### Equipe")
    equipe = [("André Cavina Oliveira", "Base de dados e análise exploratória"),
              ("Guilherme de Araújo Espírito Santo", "Atributos textuais e modelo híbrido"),
              ("Nour Hussein Barakat", "Filtragem colaborativa e avaliação"),
              ("Ryan Rodrigues Pereira", "Protótipo, repositório e índice nutricional")]
    st.html('<div class="cc-equipe">' + "".join(f"<div>{esc(n)}<small>{esc(p)}</small></div>" for n, p in equipe)
            + "</div>")
    st.markdown("Orientação: Profa. Carolina Toledo Ferraz.")
    st.markdown("#### Saiba mais")
    st.markdown(f"- [Documento do projeto (PDF)]({DOCUMENTO})\n- [Código-fonte no GitHub]({REPO})\n"
                "- Base de dados: Food.com Recipes and Interactions (Majumder et al., 2019)")

st.html(f'<div class="cc-rodape">Cozinha Consciente · Projeto Aplicado III · Universidade Presbiteriana '
        f'Mackenzie, 2026 · <a href="{REPO}" target="_blank" rel="noopener">código aberto no GitHub</a></div>')
