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
    # BARRAGEM_TAIO/BARRAGEM_ITUPORANGA movidas do pipeline pesado (6x/dia)
    # para o crítico (1x/h): a auditoria hidrológica mostrou resposta do
    # rio em Rio do Sul ~2-3h após retenção forte, e Taió publica dados
    # com cadência aproximadamente horária — rodar só 6x/dia deixaria a
    # janela de detecção grande demais para o efeito que estamos tentando
    # capturar. Não críticas por enquanto: fontes municipais novas, ainda
    # em estabilização. Promover a crítica depois de alguns dias sem falha.
    Etapa("BARRAGEM_TAIO", "src.coleta.salvar_barragem_taio", critica=False),
    Etapa(
        "BARRAGEM_ITUPORANGA",
        "src.coleta.salvar_barragem_ituporanga",
        critica=False,
    ),
]


def main() -> int:
    _, exit_code = executar_etapas("PIPELINE CRÍTICO", ETAPAS)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
