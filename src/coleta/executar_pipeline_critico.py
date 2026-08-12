import sys

from src.coleta.orquestrador import Etapa, executar_etapas

ETAPAS = [
    Etapa("RIO", "src.coleta.salvar_rio", critica=True),
    Etapa(
        "CHUVA_REAL_DC",
        "src.coleta.coletar_chuva_real_defesa_civil_rio_sul",
        critica=True,
    ),
    Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False),
]


def main() -> int:
    _, exit_code = executar_etapas("PIPELINE CRÍTICO", ETAPAS)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
