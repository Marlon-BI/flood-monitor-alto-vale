import contextlib

from src.database.conexao import get_connection
from src.coleta.asthon import cliente, modelos

FONTE = "Defesa Civil Rio do Sul"
CIDADE = "Rio do Sul"
ESTACAO = "Sensor Ponte Dom Tito Buss"
STATION_ID_DOM_TITO_BUSS = "f6360951-219f-4859-935f-b2e2d13962f1"


def coletar_leitura():
    payload = cliente.buscar_panel()
    estacao_panel = modelos.extrair_estacao_painel(payload, STATION_ID_DOM_TITO_BUSS)

    if estacao_panel is None:
        return None

    return modelos.normalizar_leitura_chuva_defesa_civil(estacao_panel)


def salvar_dados(leitura):
    if leitura is None:
        return 0

    conn = get_connection()
    cursor = None
    inseridos = 0

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hidro_chuva_defesa_civil (
                data_hora,
                cidade,
                estacao,
                nivel_metros,
                diferenca_m,
                taxa_chuva_mm_h,
                chuva_acumulada_dia_mm,
                temperatura_c,
                tempo_status,
                fonte
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data_hora, cidade, estacao, fonte) DO UPDATE SET
                nivel_metros = EXCLUDED.nivel_metros,
                diferenca_m = COALESCE(
                    EXCLUDED.diferenca_m,
                    hidro_chuva_defesa_civil.diferenca_m
                ),
                taxa_chuva_mm_h = COALESCE(
                    EXCLUDED.taxa_chuva_mm_h,
                    hidro_chuva_defesa_civil.taxa_chuva_mm_h
                ),
                chuva_acumulada_dia_mm = COALESCE(
                    EXCLUDED.chuva_acumulada_dia_mm,
                    hidro_chuva_defesa_civil.chuva_acumulada_dia_mm
                ),
                temperatura_c = COALESCE(
                    EXCLUDED.temperatura_c,
                    hidro_chuva_defesa_civil.temperatura_c
                ),
                tempo_status = COALESCE(
                    EXCLUDED.tempo_status,
                    hidro_chuva_defesa_civil.tempo_status
                ),
                coletado_em = NOW()
            WHERE hidro_chuva_defesa_civil.nivel_metros IS DISTINCT FROM EXCLUDED.nivel_metros;
        """, (
            leitura.data_hora,
            CIDADE,
            ESTACAO,
            leitura.nivel_metros,
            leitura.diferenca_m,
            leitura.taxa_chuva_mm_h,
            leitura.chuva_acumulada_dia_mm,
            leitura.temperatura_c,
            leitura.tempo_status,
            FONTE,
        ))

        inseridos = cursor.rowcount
        conn.commit()
    except Exception:
        with contextlib.suppress(Exception):
            conn.rollback()
        raise
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        with contextlib.suppress(Exception):
            conn.close()

    return inseridos


def main():
    print("Coletando nível real (Asthon) da Ponte Dom Tito Buss para hidro_chuva_defesa_civil...")

    leitura = coletar_leitura()

    if leitura is None:
        print("Estação Dom Tito Buss não encontrada no payload da Asthon.")
        return

    inseridos = salvar_dados(leitura)

    print(f"Registros salvos/atualizados: {inseridos}")


if __name__ == "__main__":
    main()
