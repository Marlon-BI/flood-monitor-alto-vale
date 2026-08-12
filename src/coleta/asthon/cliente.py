import time
from datetime import datetime

import requests

BASE_URL = "https://public.asthon.com.br"
CITY_ID_RIO_DO_SUL = 4214805

USER_AGENT = "INLIFT-Sentinel-Coleta/1.0 (+https://github.com/Inlift-Tecnologia/sentinel)"
TIMEOUT_SEGUNDOS = 30
TENTATIVAS = 3
BACKOFF_SEGUNDOS = 2


class AsthonClienteError(Exception):
    """Erro ao consultar a API pública Asthon."""


def _formatar_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(caminho: str, params: dict | None = None) -> dict:
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

    raise AsthonClienteError(
        f"Falha ao consultar {url} após {TENTATIVAS} tentativas: {erro_final}"
    ) from erro_final


def buscar_panel(city_id: int = CITY_ID_RIO_DO_SUL) -> dict:
    """GET /public/panel?city_id=...&include_geometry=false"""
    return _get(
        "/public/panel",
        params={"city_id": city_id, "include_geometry": "false"},
    )


def buscar_historico_nivel(station_id: str, start: datetime, end: datetime) -> dict:
    """GET /public/station-history?station_id=...&start=...&end=...&fields=level"""
    return _get(
        "/public/station-history",
        params={
            "station_id": station_id,
            "start": _formatar_iso(start),
            "end": _formatar_iso(end),
            "fields": "level",
        },
    )
