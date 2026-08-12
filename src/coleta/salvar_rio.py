import contextlib

from src.database.conexao import get_connection
from src.coleta.coletar_rio import coletar_dados

FONTE = "Defesa Civil Rio do Sul"


def buscar_ultima_leitura(cursor):
    cursor.execute(
        "SELECT MAX(data_hora) FROM hidro_leituras_rio WHERE fonte = %s;",
        (FONTE,),
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
                INSERT INTO hidro_leituras_rio (
                    data_hora,
                    nivel_metros,
                    variacao,
                    chuva_mm,
                    fonte
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (data_hora, fonte) DO NOTHING;
                """,
                (
                    d["data_hora"],
                    d["nivel_metros"],
                    d["variacao"],
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

    print(f"Processo finalizado. Registros inseridos: {inseridos}")


if __name__ == "__main__":
    salvar_dados()
