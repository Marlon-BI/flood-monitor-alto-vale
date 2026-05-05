import time
import requests
from datetime import datetime
from src.database.conexao import get_connection


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SEGUNDOS = 90
PAUSA_ENTRE_CIDADES_SEGUNDOS = 2


def buscar_cidades_ativas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, cidade, latitude, longitude
        FROM cidades_bacia
        WHERE ativo = TRUE
        ORDER BY cidade;
    """)

    cidades = cursor.fetchall()

    cursor.close()
    conn.close()

    return cidades


def coletar_previsao_open_meteo(latitude, longitude):
    params = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "hourly": "precipitation",
        "forecast_days": 7,
        "timezone": "America/Sao_Paulo",
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=TIMEOUT_SEGUNDOS,
    )
    response.raise_for_status()

    return response.json()


def inserir_previsoes(cursor, cidade_id, cidade, horarios, chuvas, fonte):
    inseridos = 0

    for horario, chuva in zip(horarios, chuvas):
        data_hora = datetime.fromisoformat(horario)

        cursor.execute("""
            INSERT INTO previsao_chuva (
                cidade_id,
                cidade,
                data_hora_previsao,
                chuva_prevista_mm,
                fonte
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cidade, data_hora_previsao, fonte) DO UPDATE SET
                chuva_prevista_mm = EXCLUDED.chuva_prevista_mm,
                coletado_em = NOW();
        """, (
            cidade_id,
            cidade,
            data_hora,
            chuva,
            fonte,
        ))

        inseridos += cursor.rowcount

    return inseridos


def salvar_previsao_chuva():
    cidades = buscar_cidades_ativas()

    total_processados = 0
    cidades_sucesso = 0
    cidades_falha = 0

    for cidade_id, cidade, latitude, longitude in cidades:
        print(f"Coletando previsão para {cidade}...")

        try:
            dados = coletar_previsao_open_meteo(latitude, longitude)

            horarios = dados["hourly"]["time"]
            chuvas = dados["hourly"]["precipitation"]

            conn = get_connection()
            cursor = conn.cursor()

            processados = inserir_previsoes(
                cursor=cursor,
                cidade_id=cidade_id,
                cidade=cidade,
                horarios=horarios,
                chuvas=chuvas,
                fonte="Open-Meteo",
            )

            conn.commit()
            cursor.close()
            conn.close()

            cidades_sucesso += 1
            total_processados += processados

            print(f"{cidade}: {processados} previsões salvas/atualizadas.")

        except requests.exceptions.RequestException as e:
            cidades_falha += 1
            print(f"Erro de rede/API ao coletar previsão para {cidade}: {e}")
            print("Pulando esta cidade e continuando...")

        except Exception as e:
            cidades_falha += 1
            print(f"Erro inesperado ao processar {cidade}: {e}")
            print("Pulando esta cidade e continuando...")

        time.sleep(PAUSA_ENTRE_CIDADES_SEGUNDOS)

    print("Processo finalizado.")
    print(f"Cidades com sucesso: {cidades_sucesso}")
    print(f"Cidades com falha: {cidades_falha}")
    print(f"Previsões salvas/atualizadas: {total_processados}")


if __name__ == "__main__":
    salvar_previsao_chuva()