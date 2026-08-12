"""Executa o pipeline completo (crítico + pesado) em uma única chamada.

Uso: workflow_dispatch manual/agregador. Os pipelines em produção rodam
separados — ver executar_pipeline_critico.py (1x/h) e
executar_pipeline_pesado.py (6x/dia).
"""

import sys

from src.coleta.executar_pipeline_critico import ETAPAS as ETAPAS_CRITICAS
from src.coleta.executar_pipeline_pesado import ETAPAS as ETAPAS_PESADAS
from src.coleta.orquestrador import executar_etapas


def main() -> int:
    _, exit_critico = executar_etapas("PIPELINE CRÍTICO", ETAPAS_CRITICAS)
    _, exit_pesado = executar_etapas("PIPELINE PESADO", ETAPAS_PESADAS)

    print("\nPipeline completo finalizado.")

    return exit_critico or exit_pesado


if __name__ == "__main__":
    sys.exit(main())
