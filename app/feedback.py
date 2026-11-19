"""Envio das avaliações do site para o Google Forms do grupo (as respostas caem na planilha do formulário).

O formulário não exige login nem chave: cada resposta é um POST para o endereço público
formResponse, com um campo "entry.<id>" por pergunta. Todas as perguntas do Google Forms
são do tipo "Resposta curta" ou "Parágrafo" e nenhuma é obrigatória, para que a avaliação
rápida (que preenche só parte delas) também seja aceita.
"""
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# preenchidos a partir do link do Google Forms do grupo
FORM_ID = ""
CAMPOS = {
    "tipo": "",          # Tipo de resposta
    "ingredientes": "",  # Ingredientes buscados
    "sentido": "",       # As receitas fizeram sentido? (1 a 5)
    "nota": "",          # Nota geral do site (0 a 5)
    "facilidade": "",    # Foi fácil usar o site? (1 a 5)
    "utilidade": "",     # As informações das receitas foram úteis? (1 a 5)
    "usaria": "",        # Você usaria o site para decidir o que cozinhar?
    "indicaria": "",     # Você indicaria o site para alguém?
    "origem": "",        # Como você conheceu o site?
    "comentario": "",    # Comentários e sugestões
}


def configurado() -> bool:
    return bool(FORM_ID) and all(CAMPOS.values())


def enviar(respostas: dict) -> bool:
    """Envia as respostas preenchidas; devolve True se o Google Forms aceitou."""
    if not configurado():
        return False
    dados = {CAMPOS[k]: str(v) for k, v in respostas.items() if k in CAMPOS and v not in (None, "")}
    url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
    req = Request(url, data=urlencode(dados).encode(), method="POST",
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (URLError, TimeoutError):
        return False
