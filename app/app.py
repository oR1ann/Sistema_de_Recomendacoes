"""Cozinha Consciente: site do protótipo (Streamlit).

Execução local:  streamlit run app/app.py
"""
import re

import streamlit as st

import recomendador as R
from ingredientes_pt import INGREDIENTES

st.set_page_config(page_title="Cozinha Consciente", page_icon="🥕", layout="centered")


@st.cache_resource(show_spinner="Carregando receitas...")
def catalogo():
    return R.carregar()


def lista(texto):
    return [x.strip() for x in re.split(r"[,;\n]", texto or "") if x.strip()]


cat = catalogo()

st.title("🥕 Cozinha Consciente")
st.write("Diga o que você tem em casa e receba receitas que **aproveitam esses ingredientes** "
         "e priorizam um **perfil nutricional mais equilibrado**.")

itens = lista(st.text_input("Ingredientes que você tem, separados por vírgula",
                            placeholder="Ex.: frango, arroz, tomate, cebola, alho"))

with st.expander("Filtros e preferências"):
    lam = st.slider("Prioridade para alimentação saudável", 0.0, 0.6, 0.35, 0.05,
                    help="0 = ordena só pelo aproveitamento dos seus ingredientes. Valores maiores "
                         "dão mais peso ao índice nutricional da receita.")
    restricoes = st.multiselect("Restrições alimentares", list(R.RESTRICOES))
    tempo = st.select_slider("Tempo máximo de preparo",
                             options=[15, 30, 45, 60, 90, 120, "sem limite"], value="sem limite",
                             format_func=lambda v: v if isinstance(v, str) else f"{v} min")
    max_falt = st.select_slider("Ingredientes que podem faltar",
                                options=[0, 1, 2, 3, 4, 5, "qualquer"], value="qualquer")
    basicos = st.checkbox("Tenho os básicos (sal, pimenta-do-reino, água, óleo, açúcar)", value=True)
    excluir = lista(st.text_input("Não quero receitas com", placeholder="Ex.: amendoim, leite",
                                  help="Alergias ou ingredientes que você não come, separados por vírgula."))
    k = st.slider("Quantidade de receitas", 5, 20, 10)

with st.expander("Ingredientes que o site reconhece em português"):
    st.write(", ".join(sorted(INGREDIENTES)) + ". Outros ingredientes podem ser digitados em inglês.")

if not itens:
    st.info("Digite pelo menos um ingrediente para começar.")
    st.stop()

desconhecidos = [i for i in itens if not R.conhecido(i)]
if desconhecidos:
    st.caption("Não estão na lista em português e foram buscados como escritos (em inglês): "
               + ", ".join(desconhecidos))

res = R.recomendar(cat, itens, considerar_basicos=basicos, restricoes=restricoes,
                   tempo_max=None if tempo == "sem limite" else tempo,
                   max_faltando=None if max_falt == "qualquer" else max_falt,
                   excluir=excluir, lam=lam, k=k)

if res.empty:
    st.warning("Nenhuma receita atende a todos os filtros. Tente permitir mais ingredientes faltando, "
               "aumentar o tempo de preparo ou remover alguma restrição.")
    st.stop()

st.subheader(f"{len(res)} sugestões")
for pos, (idx, r) in enumerate(res.iterrows(), 1):
    tem, bas, faltam = R.detalhar(cat, idx, itens, basicos)
    nivel, cor = R.semaforo(r["health_index"])
    with st.container(border=True):
        st.markdown(f"**{pos}. [{R.nome_bonito(r['name'])}]({R.link_foodcom(r['name'], r['recipe_id'])})**")
        indice = f"{r['health_index']:.2f}".replace(".", ",")
        st.markdown(f"🧺 **{int(r['n_usuario'])} de {len(itens)}** dos seus ingredientes · "
                    f"🛒 **{len(faltam)}** faltando · {cor} índice nutricional **{indice}** ({nivel})")
        usados = sorted({dono for _, dono in tem})
        motivo = f"Usa **{', '.join(usados)}**"
        motivo += f", fica pronta em cerca de **{int(r['minutes'])} min**" if r["minutes"] < 600 else ""
        motivo += f" e tem índice nutricional **{nivel}**."
        st.markdown(motivo)
        if faltam:
            st.markdown("Faltam: " + ", ".join(faltam))
        with st.expander("Ingredientes e nutrientes por porção"):
            st.markdown("**Você tem:** " + ", ".join(f"{n} ({d})" for n, d in tem))
            if bas:
                st.markdown("**Básicos:** " + ", ".join(bas))
            if faltam:
                st.markdown("**Faltam:** " + ", ".join(faltam))
            st.markdown(f"{r['calories']:.0f} kcal · gordura {r['total_fat_g']:.1f} g · "
                        f"gordura saturada {r['saturated_fat_g']:.1f} g · açúcar {r['sugar_g']:.1f} g · "
                        f"sódio {r['sodium_mg']:.0f} mg · proteína {r['protein_g']:.1f} g")

st.divider()
st.caption("As receitas vêm da base pública Food.com (em inglês); o link leva ao modo de preparo original. "
           "O índice nutricional (0 a 1) é uma aproximação baseada no semáforo nutricional, calculada por "
           "100 kcal, e não substitui a orientação de um profissional nem o Guia Alimentar para a "
           "População Brasileira. Projeto Aplicado III, Universidade Presbiteriana Mackenzie, 2026. "
           "[Código no GitHub](https://github.com/oR1ann/Sistema_de_Recomendacoes)")
