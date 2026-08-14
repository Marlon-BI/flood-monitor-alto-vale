import contextlib

from src.database.conexao import get_connection
from src.coleta.coletar_barragem_taio import coletar_dados, BARRAGEM_ID

FONTE = "Defesa Civil Taio (API uniparking)"


def buscar_ultima_leitura(cursor):
    cursor.execute(
        """
        SELECT MAX(data_hora)
        FROM hidro_leituras_barragens
        WHERE barragem_id = %s AND fonte = %s;
        """,
        (BARRAGEM_ID, FONTE),
    )
    (ultima,) = cursor.fetchone()
    return ultima


def salvar_dados():
    conn = get_connection()
    cursor = None
    inseridos = 0

    try:
        cursor = conn.cursor()

        ultima_leitura = buscar_ultima_leitura(cursor)
        dados = coletar_dados(ultima_leitura_local=ultima_leitura)

        for d in dados:
            cursor.execute(
                """
                INSERT INTO hidro_leituras_barragens (
                    barragem_id,
                    codigo_estacao,
                    data_hora,
                    montante_m,
                    jusante_m,
                    comportas_abertas,
                    comportas_fechadas,
                    extravasor_m,
                    nivel_percentual,
                    nivel_vertido_m,
                    chuva_mm,
                    fonte
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (barragem_id, data_hora, fonte) DO UPDATE SET
                    codigo_estacao = EXCLUDED.codigo_estacao,
                    montante_m = EXCLUDED.montante_m,
                    jusante_m = EXCLUDED.jusante_m,
                    comportas_abertas = EXCLUDED.comportas_abertas,
                    comportas_fechadas = EXCLUDED.comportas_fechadas,
                    extravasor_m = EXCLUDED.extravasor_m,
                    nivel_percentual = EXCLUDED.nivel_percentual,
                    nivel_vertido_m = EXCLUDED.nivel_vertido_m,
                    chuva_mm = EXCLUDED.chuva_mm,
                    coletado_em = NOW();
                """,
                (
                    d["barragem_id"],
                    d["codigo_estacao"],
                    d["data_hora"],
                    d["montante_m"],
                    d["jusante_m"],
                    d["comportas_abertas"],
                    d["comportas_fechadas"],
                    d["extravasor_m"],
                    d["nivel_percentual"],
                    d["nivel_vertido_m"],
                    d["chuva_mm"],
                    FONTE,
                ),
            )

            inseridos += cursor.rowcount

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

    print(f"Processo finalizado (Barragem Oeste / Taio). Registros inseridos/atualizados: {inseridos}")


if __name__ == "__main__":
    salvar_dados()
