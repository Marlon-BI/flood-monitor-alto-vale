"""Coleta de dados operacionais da Barragem Oeste (Taió) — fonte atual.

Descoberta (ago/2026): a Defesa Civil de Taió publica um site com
monitoramento "em tempo real" (defesacivil.taio.sc.gov.br) cujo widget
consome uma API JSON pública de terceiros (api-scr.uniparking.com.br),
sem autenticação. Essa API tem granularidade horária e devolve
comportas abertas/fechadas separadamente — dado que a API antiga usada
por coletar_barragens_defesa_civil_rio_sul.py deixou de existir (fonte
morta desde 27/07/2026).

Esta é a fonte primária de comportas/extravasor para a Barragem Oeste.
Continua existindo em paralelo a coletar_barragens.py (Defesa Civil SC
GraphQL/Qualle), que fornece montante/jusante/percentual mas nunca teve
comportas nessa API.
"""

from datetime import datetime

from src.coleta.uniparking import cliente

MUNICIPIO_SLUG = "defesa-civil-taio"
BARRAGEM_ID = 2  # Barragem Oeste / Taió (mesmo id usado em coletar_barragens.py)
CODIGO_ESTACAO = "TAIO-DC-API"


def _parse_data_hora(valor: str | None) -> datetime | None:
    """Formato ISO local (America/Sao_Paulo), sem tzinfo — ex: '2026-08-14T07:01:28'.

    Confirmado ao vivo: o timestamp devolvido bate com o horário local de
    Brasília no momento da coleta (não é UTC).
    """
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


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


def _normalizar_registro(bruto: dict) -> dict | None:
    data_hora = _parse_data_hora(bruto.get("data"))
    if data_hora is None:
        return None

    return {
        "barragem_id": BARRAGEM_ID,
        "codigo_estacao": CODIGO_ESTACAO,
        "data_hora": data_hora,
        "montante_m": _parse_numero(bruto.get("montante")),
        "jusante_m": _parse_numero(bruto.get("jusante")),
        "comportas_abertas": _parse_inteiro(bruto.get("comportaAberta")),
        "comportas_fechadas": _parse_inteiro(bruto.get("comportaFechada")),
        "chuva_mm": _parse_numero(bruto.get("chuva")),
        "extravasor_m": None,
        "nivel_percentual": None,
        "nivel_vertido_m": None,
    }


def coletar_dados(ultima_leitura_local: datetime | None = None) -> list[dict]:
    """Busca o histórico horário recente (últimas 24h, API não oferece mais)
    e devolve apenas os registros mais novos que `ultima_leitura_local`,
    ordenados ascendente — prontos para hidro_leituras_barragens.

    Sem leitura anterior (carga inicial), devolve toda a janela disponível
    (até 24 registros).
    """
    bruto = cliente.buscar_historico(MUNICIPIO_SLUG)

    registros = []
    for item in bruto:
        normalizado = _normalizar_registro(item)
        if normalizado is None:
            continue
        if ultima_leitura_local is not None and normalizado["data_hora"] <= ultima_leitura_local:
            continue
        registros.append(normalizado)

    registros.sort(key=lambda r: r["data_hora"])
    return registros


def main():
    dados = coletar_dados()

    print("\n=== BARRAGEM OESTE / TAIÓ — DADOS TRATADOS (dry-run, sem gravar) ===\n")
    for d in dados:
        print(d)
    print(f"\nTotal de registros novos: {len(dados)}")


if __name__ == "__main__":
    main()
