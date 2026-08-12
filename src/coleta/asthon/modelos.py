from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil import parser as dateutil_parser

FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")

OVERLAP_PADRAO_MINUTOS = 10
BACKFILL_INICIAL_HORAS = 48


def parse_timestamp_asthon(valor: str) -> datetime:
    """Converte um timestamp Asthon (UTC) para datetime timezone-aware em UTC.

    A API devolve dois formatos distintos conforme o endpoint: estilo Postgres
    com offset sem dois-pontos (stations/live) e ISO 8601 com 'Z' (panel,
    station-history). dateutil.parser.isoparse cobre os dois.
    """
    dt = dateutil_parser.isoparse(valor)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_para_local_naive(dt_utc: datetime) -> datetime:
    """Converte um datetime UTC para horário local (America/Sao_Paulo) sem
    tzinfo, preservando a convenção já usada pelos extratores antigos."""
    return dt_utc.astimezone(FUSO_LOCAL).replace(tzinfo=None)


def local_naive_para_utc(dt_local_naive: datetime) -> datetime:
    """Interpreta um datetime naive como horário local (America/Sao_Paulo) e
    devolve o equivalente em UTC (timezone-aware)."""
    return dt_local_naive.replace(tzinfo=FUSO_LOCAL).astimezone(timezone.utc)


@dataclass(frozen=True)
class LeituraNivelRio:
    data_hora: datetime
    nivel_metros: float


def normalizar_leituras_nivel(payload_historico: dict) -> list[LeituraNivelRio]:
    """Converte o payload de station-history (fields=level) em leituras
    prontas para hidro_leituras_rio, ordenadas por data_hora ascendente."""
    pontos = payload_historico.get("level") or []
    leituras = []

    for ponto in pontos:
        timestamp = ponto.get("timestamp")
        valor = ponto.get("value")

        if timestamp is None or valor is None:
            continue

        data_hora_utc = parse_timestamp_asthon(timestamp)
        leituras.append(
            LeituraNivelRio(
                data_hora=utc_para_local_naive(data_hora_utc),
                nivel_metros=float(valor),
            )
        )

    leituras.sort(key=lambda leitura: leitura.data_hora)
    return leituras


def calcular_janela_incremental(
    ultima_leitura_local: datetime | None,
    agora_utc: datetime,
    overlap_minutos: int = OVERLAP_PADRAO_MINUTOS,
    backfill_horas: int = BACKFILL_INICIAL_HORAS,
) -> tuple[datetime, datetime]:
    """Calcula a janela [start, end] em UTC para consultar station-history.

    Sem leitura anterior (carga inicial): janela limitada a `backfill_horas`.
    Com leitura anterior: começa `overlap_minutos` antes da última leitura já
    salva, confiando no UNIQUE/ON CONFLICT da tabela para a sobreposição — não
    volta a buscar a janela inteira a cada execução.

    Em qualquer caso, `start` nunca fica mais antigo que `agora_utc -
    backfill_horas`: mesmo com uma `ultima_leitura_local` muito antiga (após
    uma interrupção prolongada do pipeline), a consulta a station-history
    continua limitada a `backfill_horas`, evitando janelas excessivamente
    grandes. O preenchimento do histórico granular perdido nesse intervalo é
    tratado à parte, em um processo de backfill controlado (ver
    `coletar_rio.coletar_dados`).
    """
    limite_backfill = agora_utc - timedelta(hours=backfill_horas)

    if ultima_leitura_local is None:
        start = limite_backfill
    else:
        start = max(
            local_naive_para_utc(ultima_leitura_local) - timedelta(minutes=overlap_minutos),
            limite_backfill,
        )

    return start, agora_utc


def extrair_estacao_painel(payload_panel: dict, station_id: str) -> dict | None:
    """Localiza a estação pelo station_id dentro do payload de /public/panel."""
    for estacao in payload_panel.get("stations") or []:
        if estacao.get("station_id") == station_id:
            return estacao
    return None


@dataclass(frozen=True)
class LeituraChuvaDefesaCivil:
    data_hora: datetime
    nivel_metros: float
    diferenca_m: float | None = None
    taxa_chuva_mm_h: float | None = None
    chuva_acumulada_dia_mm: float | None = None
    temperatura_c: float | None = None
    tempo_status: str | None = None


def normalizar_leitura_chuva_defesa_civil(
    estacao_panel: dict,
) -> LeituraChuvaDefesaCivil | None:
    """Converte a entrada da Ponte Dom Tito Buss em /public/panel numa leitura
    pronta para hidro_chuva_defesa_civil.

    Decisão da restauração urgente (Camada 1): só nível e timestamp são reais
    nesta fase. Chuva, temperatura, diferença e status ficam None — a Dom Tito
    Buss não tem sensor de chuva/temperatura na Asthon (rainfall_sensor=0), e
    o payload de panel devolve rainfall_1h/24h=0 por padrão mesmo sem sensor,
    o que não pode ser confundido com medição real. A co-localização com uma
    estação de chuva vizinha (SDC-SC Rio do Sul) ainda não foi confirmada
    oficialmente, então nenhum campo de outra estação é usado aqui.
    """
    timestamp = estacao_panel.get("last_reading_at")
    nivel = estacao_panel.get("level_m")

    if timestamp is None or nivel is None:
        return None

    data_hora_utc = parse_timestamp_asthon(timestamp)
    return LeituraChuvaDefesaCivil(
        data_hora=utc_para_local_naive(data_hora_utc),
        nivel_metros=float(nivel),
    )
