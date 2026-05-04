import requests
import pandas as pd
from bs4 import BeautifulSoup
from src.database.conexao import get_connection


URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQg45w_7LsGx0S2nU7oDm74LjrYqS9TUsW2n5_cn_UhYO5tLp0KvMECIbePBVAVB6zQz1fKR17_b34f/pub?output=csv"


def to_float(valor):
    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "" or valor == "-":
        return None

    try:
        return float(valor.replace(".", "").replace(",", "."))
    except Exception:
        try:
            return float(valor.replace(",", "."))
        except Exception:
            return None


def to_int(valor):
    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "" or valor == "-":
        return None

    try:
        return int(float(valor.replace(",", ".")))
    except Exception:
        return None


from io import StringIO

from io import StringIO

def coletar_tabela_historica():
    response = requests.get(URL, timeout=60)
    response.raise_for_status()

    # Corrige encoding
    response.encoding = "utf-8"

    df_raw = pd.read_csv(StringIO(response.text), header=None)

    print("\nPrimeiras linhas brutas:")
    print(df_raw.head())

    # A linha 1 contém os cabeçalhos reais
    df_historico = df_raw.iloc[2:, 0:6].copy()
    df_historico.columns = [
        "Ocorrência",
        "Ano",
        "Data do pico da cheia",
        "Volume mm",
        "Metragem",
        "Dias de chuva"
    ]

    print("\nHistórico tratado:")
    print(df_historico.head())

    return [df_historico]

def salvar_historico(df):
    conn = get_connection()
    cursor = conn.cursor()

    inseridos = 0

    for _, row in df.iterrows():
        ocorrencia = to_int(row.get("Ocorrência"))
        ano = to_int(row.get("Ano"))
        data_pico_cheia = str(row.get("Data do pico da cheia")).strip() if row.get("Data do pico da cheia") is not None else None
        volume_chuva_mm = to_float(row.get("Volume mm"))
        metragem = to_float(row.get("Metragem"))
        dias_de_chuva = to_int(row.get("Dias de chuva"))

        if not ano or not metragem:
            continue

        cursor.execute("""
            INSERT INTO historico_enchentes_rio_do_sul (
                ocorrencia,
                ano,
                data_pico_cheia,
                volume_chuva_mm,
                metragem,
                dias_de_chuva
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ocorrencia, ano, data_pico_cheia, metragem) DO NOTHING;
        """, (
            ocorrencia,
            ano,
            data_pico_cheia,
            volume_chuva_mm,
            metragem,
            dias_de_chuva
        ))

        inseridos += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Histórico inserido: {inseridos}")


if __name__ == "__main__":
    tabelas = coletar_tabela_historica()

    # Normalmente a primeira tabela é a principal de enchentes históricas
    df_historico = tabelas[0]

    salvar_historico(df_historico)