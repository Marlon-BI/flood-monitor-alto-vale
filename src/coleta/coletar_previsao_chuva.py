from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from src.database.conexao import get_connection


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SEGUNDOS = 20
MAX_WORKERS = 5
FONTE = "Open-Meteo"


def buscar_cidades_ativas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            cidade,
            latitude,
            longitude,
            bacia,
            peso_hidrologico
        FROM cmd_cidades_monitoradas
        WHERE ativa = TRUE
        ORDER BY ordem_coleta;
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
            INSERT INTO hidro_previsao_chuva (
                cidade_id,
                cidade,
                data_hora_previsao,
                chuva_prevista_mm,
                fonte
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cidade, data_hora_previsao, fonte) DO UPDATE SET
                cidade_id = EXCLUDED.cidade_id,
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


def _buscar_previsao_cidade(cidade_info):
    cidade_id, cidade, latitude, longitude, bacia, peso_hidrologico = cidade_info
    dados = coletar_previsao_open_meteo(latitude, longitude)
    return cidade_id, cidade, dados


def salvar_previsao_chuva():
    cidades = buscar_cidades_ativas()

    total_processados = 0
    cidades_sucesso = 0
    cidades_falha = 0

    print(f"Cidades ativas para previsão: {len(cidades)}")

    resultados_por_cidade = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {
            executor.submit(_buscar_previsao_cidade, cidade_info): cidade_info
            for cidade_info in cidades
        }

        for futuro in as_completed(futuros):
            cidade_id, cidade, _, _, bacia, peso_hidrologico = futuros[futuro]

            try:
                _, _, dados = futuro.result()
                resultados_por_cidade[cidade_id] = (cidade, dados)
                print(f"Previsão obtida para {cidade} (bacia={bacia}, peso={peso_hidrologico}).")

            except requests.exceptions.RequestException as e:
                cidades_falha += 1
                print(f"Erro de rede/API ao coletar previsão para {cidade}: {e}")

            except Exception as e:
                cidades_falha += 1
                print(f"Erro inesperado ao coletar previsão para {cidade}: {e}")

    if resultados_por_cidade:
        conn = get_connection()
        cursor = conn.cursor()

        for cidade_id, (cidade, dados) in resultados_por_cidade.items():
            try:
                horarios = dados["hourly"]["time"]
                chuvas = dados["hourly"]["precipitation"]

                processados = inserir_previsoes(
                    cursor=cursor,
                    cidade_id=cidade_id,
                    cidade=cidade,
                    horarios=horarios,
                    chuvas=chuvas,
                    fonte=FONTE,
                )

                conn.commit()

                cidades_sucesso += 1
                total_processados += processados

                print(f"{cidade}: {processados} previsões salvas/atualizadas.")

            except Exception as e:
                cidades_falha += 1
                conn.rollback()
                print(f"Erro ao salvar previsão para {cidade}: {e}")

        cursor.close()
        conn.close()

    print("Processo finalizado.")
    print(f"Cidades com sucesso: {cidades_sucesso}")
    print(f"Cidades com falha: {cidades_falha}")
    print(f"Previsões salvas/atualizadas: {total_processados}")


if __name__ == "__main__":
    salvar_previsao_chuva()
