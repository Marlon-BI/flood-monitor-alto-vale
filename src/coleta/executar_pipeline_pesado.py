import sys

from src.coleta.orquestrador import Etapa, executar_etapas

ETAPAS = [
    Etapa("PREVISAO_CHUVA", "src.coleta.coletar_previsao_chuva", critica=False),
    Etapa("EPAGRI_OBSERVADA", "src.coleta.coletar_chuva_epagri_ciram", critica=False),
    Etapa("EPAGRI_PREVISAO", "src.coleta.coletar_previsao_epagri_banner", critica=False),
    Etapa(
        "BARRAGENS_DC",
        "src.coleta.coletar_barragens_defesa_civil_rio_sul",
        critica=False,
    ),
    Etapa("BOLETINS_DC", "src.coleta.coletar_defesa_civil_sc", critica=False),
    Etapa("SNAPSHOT_PREVISAO", "src.coleta.salvar_snapshot_previsao", critica=False),
    Etapa(
        "APRENDIZADO_SALVAR",
        "src.coleta.salvar_aprendizado_hidrologico",
        critica=False,
    ),
    Etapa(
        "APRENDIZADO_ATUALIZAR",
        "src.coleta.atualizar_aprendizado_hidrologico",
        critica=False,
    ),
    Etapa(
        "VALIDAR_PREVISOES",
        "src.coleta.validar_previsoes_hidrologicas",
        critica=False,
    ),
    Etapa(
        "APRENDIZADO_ATUALIZAR",
        "src.coleta.atualizar_aprendizado_hidrologico",
        critica=False,
    ),
]


def main() -> int:
    _, exit_code = executar_etapas("PIPELINE PESADO", ETAPAS)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
