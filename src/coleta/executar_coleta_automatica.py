import time
from datetime import datetime

from src.coleta.salvar_rio import salvar_dados


INTERVALO_SEGUNDOS = 600  # 10 minutos


def executar_loop():
    print("Iniciando coleta automática do nível do rio...")
    print(f"Intervalo configurado: {INTERVALO_SEGUNDOS / 60:.0f} minutos")

    while True:
        try:
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            print(f"\n[{agora}] Executando coleta...")

            salvar_dados()

            print(f"[{agora}] Coleta finalizada com sucesso.")

        except Exception as e:
            print(f"Erro durante a coleta automática: {e}")

        print(f"Aguardando {INTERVALO_SEGUNDOS / 60:.0f} minutos...\n")
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    executar_loop()