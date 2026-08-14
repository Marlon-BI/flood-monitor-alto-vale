import time

import requests

BASE_URL = "https://api-scr.uniparking.com.br/v1"

USER_AGENT = "INLIFT-Sentinel-Coleta/1.0 (+https://github.com/Inlift-Tecnologia/sentinel)"
TIMEOUT_SEGUNDOS = 30
TENTATIVAS = 3
BACKOFF_SEGUNDOS = 2


class UniparkingClienteError(Exception):
    """Erro ao consultar a API pública da Defesa Civil (uniparking/api-scr)."""


def _get(caminho: str, params: dict | None = None):
    url = f"{BASE_URL}{caminho}"
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}

    erro_final = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(
                url, params=params, headers=headers, timeout=TIMEOUT_SEGUNDOS
            )
            resposta.raise_for_status()
            return resposta.json()
        except (requests.RequestException, ValueError) as erro:
            erro_final = erro
            if tentativa < TENTATIVAS:
                time.sleep(BACKOFF_SEGUNDOS * tentativa)

    raise UniparkingClienteError(
        f"Falha ao consultar {url} após {TENTATIVAS} tentativas: {erro_final}"
    ) from erro_final


def buscar_cards(municipio_slug: str) -> dict:
    """GET /v1/{municipio_slug}/dados/cards?v=1 — status atual (montante,
    jusante, comportas, extravasor, chuva)."""
    return _get(f"/{municipio_slug}/dados/cards", params={"v": 1})


def buscar_historico(municipio_slug: str) -> list:
    """GET /v1/{municipio_slug}/dados/historico?v=1 — série horária recente
    (mais nova primeiro), com montante/jusante/comportas por leitura."""
    return _get(f"/{municipio_slug}/dados/historico", params={"v": 1})
