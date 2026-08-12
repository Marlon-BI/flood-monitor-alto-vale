from datetime import datetime, timezone

from src.coleta.asthon import cliente, modelos

STATION_ID_DOM_TITO_BUSS = "f6360951-219f-4859-935f-b2e2d13962f1"


def coletar_dados(ultima_leitura_local=None, agora_utc=None):
    """Busca a série granular (~2 min) de station-history e retorna apenas a
    leitura mais recente, pronta para hidro_leituras_rio.

    A Asthon devolve uma série granular, mas a Camada 1 desta restauração
    persiste somente o último ponto de cada execução: hidro_leituras_rio e a
    view de cm_por_hora foram desenhadas para uma cadência aproximada de uma
    leitura por hora (a cadência real é garantida pela execução horária do
    pipeline, não por agrupamento aqui). Persistir todos os pontos de ~2 min
    introduziria ruído no cálculo de cm_por_hora entre registros consecutivos:
    leituras em intervalos muito curtos podem amplificar ruídos do sensor
    quando a taxa é calculada entre dois registros consecutivos. O backfill do
    histórico granular perdido é tratado à parte, em um processo separado e
    controlado — não é feito aqui.
    """
    agora_utc = agora_utc or datetime.now(timezone.utc)

    start, end = modelos.calcular_janela_incremental(ultima_leitura_local, agora_utc)
    payload = cliente.buscar_historico_nivel(STATION_ID_DOM_TITO_BUSS, start, end)
    leituras = modelos.normalizar_leituras_nivel(payload)

    if not leituras:
        return []

    ultima = leituras[-1]
    return [
        {
            "data_hora": ultima.data_hora,
            "nivel_metros": ultima.nivel_metros,
            "variacao": None,
            "chuva_mm": None,
        }
    ]


def main():
    dados = coletar_dados()

    print("\n=== DADOS TRATADOS ===\n")

    for d in dados[:5]:
        print(d)


if __name__ == "__main__":
    main()
