import time
import subprocess
from datetime import datetime


INTERVALO_MINUTOS = 10


ETAPAS = [
    ("Coletando nível do rio", "src.coleta.salvar_rio"),
    ("Coletando previsão de chuva", "src.coleta.coletar_previsao_chuva"),
    ("Coletando barragens", "src.coleta.coletar_barragens"),
    ("Coletando boletins Defesa Civil SC", "src.coleta.coletar_defesa_civil_sc"),
    ("Salvando snapshot da previsão", "src.coleta.salvar_snapshot_previsao"),
]


def executar_modulo(descricao, modulo):
    print(f"\n[{datetime.now()}] {descricao}...")

    resultado = subprocess.run(
        ["python", "-m", modulo],
        capture_output=True,
        text=True
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(resultado.stderr)

    if resultado.returncode != 0:
        raise Exception(f"Erro ao executar módulo: {modulo}")


def executar_pipeline():
    print(f"\n[{datetime.now()}] Iniciando pipeline completo...")

    for descricao, modulo in ETAPAS:
        try:
            executar_modulo(descricao, modulo)
        except Exception as e:
            print(f"Falha na etapa '{descricao}': {e}")
            print("Continuando para a próxima etapa...")

    print(f"\n[{datetime.now()}] Pipeline finalizado.")


if __name__ == "__main__":
    print("Pipeline automático iniciado.")
    print(f"Intervalo: {INTERVALO_MINUTOS} minutos")

    while True:
        try:
            executar_pipeline()
        except Exception as e:
            print(f"Erro no pipeline: {e}")

        print(f"\nAguardando {INTERVALO_MINUTOS} minutos...")
        time.sleep(INTERVALO_MINUTOS * 60)