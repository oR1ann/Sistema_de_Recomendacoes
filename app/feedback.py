"""Envio das avaliações do site para o Google Forms do grupo (as respostas caem na planilha do formulário).

O formulário não exige login nem chave: cada resposta é um POST para o endereço público
formResponse, com um campo "entry.<id>" por pergunta. Nenhuma pergunta é obrigatória, para
que a avaliação rápida (que preenche só parte delas) também seja aceita. As perguntas de
escala são do tipo "Classificação" (estrelas de 1 a 5) e recebem o número como texto.
"""
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Google Forms "Avaliação – Cozinha Consciente"
FORM_ID = "1FAIpQLSfzcXqGQe_KK0zxtsBmJqk3lN4heMmGD-SaEHvLaNIcpTVkfQ"
CAMPOS = {
    "sentido": "entry.1550835393",     # As receitas fizeram sentido? (1 a 5)
    "nota": "entry.1744402730",        # Nota geral do site (1 a 5)
    "facilidade": "entry.386833065",   # Foi fácil usar o site? (1 a 5)
    "utilidade": "entry.532541586",    # As informações das receitas foram úteis? (1 a 5)
    "usaria": "entry.873637635",       # Você usaria o site para decidir o que cozinhar? (1 a 5)
    "indicaria": "entry.186922836",    # Você indicaria o site para alguém? (1 a 5)
    "origem": "entry.242131134",       # Como você conheceu o site?
    "comentario": "entry.1328732442",  # Comentários e sugestões
    # opcionais: se o formulário ganhar estas perguntas (resposta curta), basta preencher o entry
    "tipo": None,                      # Tipo de resposta (avaliação rápida ou formulário completo)
    "ingredientes": None,              # Ingredientes buscados
}


def configurado() -> bool:
    return bool(FORM_ID) and bool(CAMPOS["sentido"])


def enviar(respostas: dict) -> bool:
    """Envia as respostas preenchidas; devolve True se o Google Forms aceitou."""
    if not configurado():
        return False
    dados = {CAMPOS[k]: str(v) for k, v in respostas.items()
             if CAMPOS.get(k) and v not in (None, "")}
    url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
    req = Request(url, data=urlencode(dados).encode(), method="POST",
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (URLError, TimeoutError):
        return False
