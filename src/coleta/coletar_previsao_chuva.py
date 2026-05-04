import requests
from datetime import datetime
from src.database.conexao import get_connection


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
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "hourly": "precipitation",
        "forecast_days": 7,
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()

def salvar_previsao_chuva_multi_fonte():
    cidades = buscar_cidades_ativas()

    fontes = ["Open-Meteo", "Simulado-INMET"]

    total_inseridos = 0

    for cidade_id, cidade, latitude, longitude in cidades:
        print(f"Coletando previsão para {cidade}...")

        dados = coletar_previsao_open_meteo(latitude, longitude)

        horarios = dados["hourly"]["time"]
        chuvas = dados["hourly"]["precipitation"]

        for fonte in fontes:
            conn = get_connection()
            cursor = conn.cursor()

            inseridos_fonte = 0

            for horario, chuva in zip(horarios, chuvas):
                data_hora = datetime.fromisoformat(horario)

                # pequena variação simulando diferença de modelo
                if fonte == "Simulado-INMET":
                    chuva = float(chuva) * 1.1  # +10%

                cursor.execute("""
                    INSERT INTO previsao_chuva (
                        cidade_id,
                        cidade,
                        data_hora_previsao,
                        chuva_prevista_mm,
                        fonte
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (cidade, data_hora_previsao, fonte) DO NOTHING;
                """, (
                    cidade_id,
                    cidade,
                    data_hora,
                    chuva,
                    fonte
                ))

                inseridos_fonte += cursor.rowcount

            conn.commit()
            cursor.close()
            conn.close()

            print(f"{cidade} - {fonte}: {inseridos_fonte} inseridos")
            total_inseridos += inseridos_fonte

    print(f"Total inserido: {total_inseridos}")


def salvar_previsao_chuva():
    cidades = buscar_cidades_ativas()

    conn = get_connection()
    cursor = conn.cursor()

    total_inseridos = 0

    for cidade_id, cidade, latitude, longitude in cidades:
        print(f"Coletando previsão para {cidade}...")

        dados = coletar_previsao_open_meteo(latitude, longitude)

        horarios = dados["hourly"]["time"]
        chuvas = dados["hourly"]["precipitation"]

        for horario, chuva in zip(horarios, chuvas):
            data_hora = datetime.fromisoformat(horario)

            cursor.execute("""
                INSERT INTO previsao_chuva (
                    cidade_id,
                    cidade,
                    data_hora_previsao,
                    chuva_prevista_mm
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (cidade, data_hora_previsao, fonte) DO NOTHING;
            """, (
                cidade_id,
                cidade,
                data_hora,
                chuva
            ))

            total_inseridos += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Processo finalizado. Previsões inseridas: {total_inseridos}")


if __name__ == "__main__":
    salvar_previsao_chuva()