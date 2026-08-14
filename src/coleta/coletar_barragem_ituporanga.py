"""Coleta de dados operacionais da Barragem Sul (Ituporanga) — fonte atual.

Descoberta (ago/2026): a Prefeitura de Ituporanga publica uma página
própria (ituporanga.sc.gov.br/nivel-rio) com uma tabela histórica
(Yii2 GridView, renderizada no servidor) contendo montante, jusante,
comportas abertas/fechadas e as lâminas do canal extravasor e do
vertedouro. Não há API JSON exposta para essa página (investigado e
descartado) — HTML é a única fonte disponível aqui, por isso o parser
usa BeautifulSoup, casando colunas pelo texto do cabeçalho (não por
índice fixo) para não quebrar silenciosamente se a ordem mudar.

Cadência observada: ~2 leituras/dia (07:00 e 17:00) — bem mais esparsa
que a Barragem Oeste. É esperado que `idade_barragem_sul_min` fique
maior que o threshold de "fresh" entre atualizações; isso não significa
que a fonte está morta (ver STALE vs fonte morta na auditoria anterior:
a fonte antiga da Defesa Civil de Rio do Sul parou de vez em 27/07, esta
aqui segue tendo leituras novas a cada execução, só que num ritmo menor).
"""

import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

URL = "https://ituporanga.sc.gov.br/nivel-rio"
FONTE_USER_AGENT = "INLIFT-Sentinel-Coleta/1.0 (+https://github.com/Inlift-Tecnologia/sentinel)"
TIMEOUT_SEGUNDOS = 30
TENTATIVAS = 3
BACKOFF_SEGUNDOS = 2

BARRAGEM_ID = 1  # Barragem Sul / Ituporanga (mesmo id usado em coletar_barragens.py)
CODIGO_ESTACAO = "ITUPORANGA-NIVELRIO"

# nome esperado do cabeçalho -> chave normalizada
MAPA_COLUNAS = {
    "data / hora": "data_hora",
    "montante (m)": "montante_m",
    "jusante (m)": "jusante_m",
    "comp. aberta(s)": "comportas_abertas",
    "comp. fechada(s)": "comportas_fechadas",
    "canal extravasor": "canal_extravasor_status",
    "lâmina canal extravasor": "extravasor_m",
    "lâmina vertedouro": "nivel_vertido_m",
}


class ItuporangaColetaError(Exception):
    """Erro ao consultar a página de nível do rio da Prefeitura de Ituporanga."""


def _buscar_html() -> str:
    headers = {"User-Agent": FONTE_USER_AGENT}
    erro_final = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(URL, headers=headers, timeout=TIMEOUT_SEGUNDOS)
            resposta.raise_for_status()
            return resposta.text
        except requests.RequestException as erro:
            erro_final = erro
            if tentativa < TENTATIVAS:
                time.sleep(BACKOFF_SEGUNDOS * tentativa)

    raise ItuporangaColetaError(
        f"Falha ao consultar {URL} após {TENTATIVAS} tentativas: {erro_final}"
    ) from erro_final


def _parse_numero(valor) -> float | None:
    if valor is None:
        return None
    texto = str(valor).strip().replace(",", ".")
    if texto in ("", "-", "–", "NULL", "null", "None"):
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _parse_inteiro(valor) -> int | None:
    numero = _parse_numero(valor)
    return int(numero) if numero is not None else None


def _parse_data_hora(valor: str | None) -> datetime | None:
    """Formato 'DD/MM/AAAA HH:MM', horário local (America/Sao_Paulo), sem tzinfo."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        return None


def _localizar_tabela(soup: BeautifulSoup):
    """Encontra a tabela cujo cabeçalho contém as colunas esperadas
    (identificada pelo conteúdo, não por posição/índice no HTML)."""
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if any("montante" in h for h in headers) and any("jusante" in h for h in headers):
            return table, headers
    return None, []


def extrair_registros(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table, headers_brutos = _localizar_tabela(soup)
    if table is None:
        return []

    indices = {}
    for i, h in enumerate(headers_brutos):
        chave = MAPA_COLUNAS.get(h)
        if chave:
            indices[chave] = i

    if "data_hora" not in indices:
        return []

    registros = []
    linhas = table.find_all("tr")
    for linha in linhas:
        celulas = linha.find_all("td")
        if not celulas:
            continue
        valores = [c.get_text(" ", strip=True) for c in celulas]

        def pegar(chave):
            idx = indices.get(chave)
            return valores[idx] if idx is not None and idx < len(valores) else None

        data_hora = _parse_data_hora(pegar("data_hora"))
        if data_hora is None:
            continue

        registros.append({
            "barragem_id": BARRAGEM_ID,
            "codigo_estacao": CODIGO_ESTACAO,
            "data_hora": data_hora,
            "montante_m": _parse_numero(pegar("montante_m")),
            "jusante_m": _parse_numero(pegar("jusante_m")),
            "comportas_abertas": _parse_inteiro(pegar("comportas_abertas")),
            "comportas_fechadas": _parse_inteiro(pegar("comportas_fechadas")),
            "extravasor_m": _parse_numero(pegar("extravasor_m")),
            "nivel_vertido_m": _parse_numero(pegar("nivel_vertido_m")),
            "nivel_percentual": None,
            "chuva_mm": None,
        })

    return registros


def coletar_dados(ultima_leitura_local: datetime | None = None) -> list[dict]:
    """Busca a tabela de nível/barragem publicada pela Prefeitura de
    Ituporanga e devolve apenas registros mais novos que
    `ultima_leitura_local`, ordenados ascendente.

    Sem leitura anterior, devolve toda a página disponível (a tabela é
    paginada pelo Yii2 GridView; a primeira página basta para uso
    incremental normal — backfill mais profundo, se necessário, é tratado
    à parte, como já é convenção neste pipeline para outras fontes)."""
    html = _buscar_html()
    registros = extrair_registros(html)

    if ultima_leitura_local is not None:
        registros = [r for r in registros if r["data_hora"] > ultima_leitura_local]

    registros.sort(key=lambda r: r["data_hora"])
    return registros


def main():
    dados = coletar_dados()

    print("\n=== BARRAGEM SUL / ITUPORANGA — DADOS TRATADOS (dry-run, sem gravar) ===\n")
    for d in dados:
        print(d)
    print(f"\nTotal de registros novos: {len(dados)}")


if __name__ == "__main__":
    main()
