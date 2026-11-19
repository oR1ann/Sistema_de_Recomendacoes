"""Cozinha Consciente: site do protótipo (Streamlit).

Execução local (na raiz do repositório):  streamlit run app/app.py
"""
import html
from pathlib import Path
import re

import streamlit as st

import feedback as FB
import recomendador as R
from estilo import CSS, icone
from ingredientes_pt import INGREDIENTES

REPO = "https://github.com/oR1ann/Sistema_de_Recomendacoes"
DOCUMENTO = f"{REPO}/blob/main/docs/Projeto_Aplicado_III_Cozinha_Consciente.pdf"
ATALHOS = ["arroz", "feijão", "frango", "ovo", "tomate", "cebola", "alho", "batata",
           "cenoura", "macarrão", "queijo", "banana"]

st.set_page_config(page_title="Cozinha Consciente", page_icon=":material/eco:", layout="centered")
st.html(CSS)


def versao_dos_dados():
    """Muda sempre que o código do recomendador ou os arquivos de dados mudam."""
    pasta = Path(__file__).parent
    arquivos = [pasta / "recomendador.py", *sorted((pasta / "dados").glob("*.parquet"))]
    return tuple((a.name, a.stat().st_size, a.stat().st_mtime_ns) for a in arquivos)


@st.cache_resource(show_spinner="Carregando receitas...", max_entries=1)
def catalogo(versao):
    # "versao" entra na chave do cache: após uma atualização no servidor, o catálogo é recarregado
    # em vez de reaproveitar um objeto criado pela versão anterior do código
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
    pt = cat.em_portugues
    chips = "".join(f'<span class="cc-chip cc-tem" title="{esc(n)}">{esc(pt(n))}</span>' for n, _ in tem)
    chips += "".join(f'<span class="cc-chip cc-basico" title="{esc(n)}">{esc(pt(n))}</span>' for n in bas)
    chips += "".join(f'<span class="cc-chip cc-falta" title="{esc(n)}">{esc(pt(n))}</span>' for n in faltam)
    nutri = [("Calorias", f"{r['calories']:.0f} kcal"), ("Proteína", f"{r['protein_g']:.1f} g"),
             ("Gordura", f"{r['total_fat_g']:.1f} g"), ("Gord. saturada", f"{r['saturated_fat_g']:.1f} g"),
             ("Açúcar", f"{r['sugar_g']:.1f} g"), ("Sódio", f"{r['sodium_mg']:.0f} mg")]
    nutri_html = "".join(f"<div>{k}<b>{v.replace('.', ',')}</b></div>" for k, v in nutri)
    original = R.nome_bonito(r["name"])
    nome = r["nome_pt"] if isinstance(r["nome_pt"], str) and r["nome_pt"] else original
    link_pt = R.link_traduzido(r["name"], r["recipe_id"])
    link_en = R.link_foodcom(r["name"], r["recipe_id"])
    sub = (f'<div class="cc-orig">Nome original: {esc(original)} · '
           f'<a href="{esc(link_en)}" target="_blank" rel="noopener">receita em inglês</a></div>'
           if nome != original else "")
    return (
        f'<div class="cc-card">'
        f'<div class="cc-top"><span class="cc-rank">{pos:02d}</span>'
        f'<div class="cc-title"><a href="{esc(link_pt)}" target="_blank" rel="noopener" '
        f'title="Abrir o modo de preparo em português">{esc(nome)}{icone("seta", 14)}</a>{sub}</div>'
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


def avaliacao_rapida(consulta):
    """Estrelas logo abaixo dos resultados; envia uma vez por busca."""
    if not FB.configurado():
        return
    with st.container(border=True):
        st.markdown("**Essas sugestões fizeram sentido para você?**")
        estrelas = st.feedback("stars", key=f"rapida::{consulta}")
        enviado = st.session_state.setdefault("rapidas_enviadas", {})
        if estrelas is not None and consulta not in enviado:
            enviado[consulta] = FB.enviar({"tipo": "avaliação rápida", "ingredientes": consulta,
                                           "sentido": estrelas + 1})
        if consulta in enviado:
            if enviado[consulta]:
                st.caption("Obrigado! Para contar mais, use a aba Avaliar.")
            else:
                st.caption("Não foi possível registrar agora. Tente pela aba Avaliar.")


cat = catalogo(versao_dos_dados())

st.html(
    '<div class="cc-hero"><div class="cc-eyebrow">Projeto Aplicado III · Mackenzie</div>'
    '<h1>Cozinha Consciente</h1>'
    '<p>Receitas a partir do que você já tem em casa, ordenadas para aproveitar os seus ingredientes '
    'e favorecer escolhas mais equilibradas.</p></div>'
)

aba_busca, aba_como, aba_aval, aba_sobre = st.tabs([":material/search: Receitas",
                                                    ":material/info: Como funciona",
                                                    ":material/rate_review: Avaliar",
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
            avaliacao_rapida(", ".join(itens))

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
            'a População Brasileira. As receitas vêm da base pública Food.com, escrita em inglês: os nomes e os '
            'ingredientes foram traduzidos por tradução automática (o nome original aparece abaixo de cada '
            'receita), e o link abre o modo de preparo traduzido pelo Google Tradutor, com a opção de ver o '
            'original.</div>')

# ------------------------------------------------------------------------ avaliar
with aba_aval:
    st.markdown("### Conte o que achou")
    st.markdown("Leva menos de um minuto. As respostas são anônimas e ajudam a equipe a avaliar o projeto.")
    escala = ["1", "2", "3", "4", "5"]
    with st.form("avaliacao", clear_on_submit=True):
        sentido = st.radio("As receitas sugeridas fizeram sentido com os ingredientes que você informou? "
                           ":gray[(1 = nenhum sentido, 5 = total sentido)]", escala, horizontal=True, index=None)
        nota = st.radio("Que nota você dá para o site? :gray[(1 = muito ruim, 5 = excelente)]",
                        escala, horizontal=True, index=None)
        facilidade = st.radio("Foi fácil usar e navegar no site? :gray[(1 = muito difícil, 5 = muito fácil)]",
                              escala, horizontal=True, index=None)
        utilidade = st.radio("As informações das receitas (índice nutricional, o que falta comprar, tempo de "
                             "preparo) foram úteis? :gray[(1 = nada úteis, 5 = muito úteis)]",
                             escala, horizontal=True, index=None)
        usaria = st.radio("Você usaria o site para decidir o que cozinhar? "
                          ":gray[(1 = de jeito nenhum, 5 = com certeza)]", escala, horizontal=True, index=None)
        indicaria = st.radio("Você indicaria o site para alguém? :gray[(1 = de jeito nenhum, 5 = com certeza)]",
                             escala, horizontal=True, index=None)
        origem = st.selectbox("Como você conheceu o site?", ["Oficina ou ação na comunidade",
                                                              "Equipe do projeto", "Outro"],
                              index=None, placeholder="Escolha uma opção")
        comentario = st.text_area("Comentários ou sugestões (opcional)",
                                  placeholder="O que você mudaria? Faltou alguma receita ou ingrediente?")
        enviar = st.form_submit_button("Enviar avaliação", icon=":material/send:")
    if enviar:
        respostas = {"tipo": "formulário completo", "sentido": sentido, "nota": nota,
                     "facilidade": facilidade, "utilidade": utilidade, "usaria": usaria,
                     "indicaria": indicaria, "origem": origem, "comentario": comentario.strip()}
        if all(v in (None, "") for k, v in respostas.items() if k != "tipo"):
            st.warning("Responda pelo menos uma pergunta antes de enviar.")
        elif FB.enviar(respostas):
            st.success("Obrigado! Sua avaliação foi registrada.")
        else:
            st.error("Não foi possível registrar a avaliação agora. Tente novamente em alguns minutos.")

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
