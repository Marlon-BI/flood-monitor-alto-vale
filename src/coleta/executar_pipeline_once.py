import subprocess
import sys
from datetime import datetime


def executar_etapa(nome, modulo):
    print(f"\n[{datetime.now()}] {nome}...")

    resultado = subprocess.run(
        [sys.executable, "-m", modulo],
        check=False,
    )

    if resultado.returncode != 0:
        print(f"Falha na etapa '{nome}': Erro ao executar módulo: {modulo}")
        print("Continuando para a próxima etapa...")


def executar_pipeline():
    print("Iniciando pipeline completo...")

    executar_etapa("Coletando nível do rio", "src.coleta.salvar_rio")
    executar_etapa("Coletando chuva real Defesa Civil Rio do Sul", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul")
    executar_etapa("Coletando previsão de chuva", "src.coleta.coletar_previsao_chuva")
    executar_etapa("Coletando barragens", "src.coleta.coletar_barragens")
    executar_etapa("Coletando boletins Defesa Civil SC", "src.coleta.coletar_defesa_civil_sc")
    executar_etapa("Salvando snapshot da previsão", "src.coleta.salvar_snapshot_previsao")
    executar_etapa("Salvando aprendizado hidrológico", "src.coleta.salvar_aprendizado_hidrologico")
    executar_etapa("Atualizando aprendizado hidrológico", "src.coleta.atualizar_aprendizado_hidrologico")

    print("\nPipeline finalizado.")


if __name__ == "__main__":
    executar_pipeline()