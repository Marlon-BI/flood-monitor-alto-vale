import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from src.database.conexao import get_connection


URL = "https://defesacivil.riodosul.sc.gov.br/index.php?r=externo%2Fmetragem"
FONTE = "Defesa Civil Rio do Sul"


MAPA_BARRAGENS = {
    1: {"barragem": "Barragem Sul", "cidade": "Ituporanga"},
    2: {"barragem": "Barragem Oeste", "cidade": "Taió"},
}


def converter_numero(valor):
    if valor is None:
        return None

    texto = str(valor).strip()

    if texto in ("", "-", "NULL", "null", "None"):
        return None

    texto = texto.replace(",", ".")
    texto = re.sub(r"[^0-9\.\-]", "", texto)

    if texto == "":
        return None

    try:
        return float(texto)
    except ValueError:
        return None


def converter_inteiro(valor):
    numero = converter_numero(valor)
    if numero is None:
        return None
    return int(numero)


def converter_data_hora(valor):
    texto = str(valor).strip()

    formatos = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %HH",
        "%d/%m %HH",
        "%d/%m %H:%M",
    ]

    for formato in formatos:
        try:
            data = datetime.strptime(texto, formato)

            if "%Y" not in formato:
                data = data.replace(year=datetime.now().year)

            return data
        except ValueError:
            continue

    return None


def buscar_tabelas():
    response = requests.get(URL, timeout=60)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find_all("table")


def extrair_barragens():
    tabelas = buscar_tabelas()
    registros = []

    for indice_tabela, config in MAPA_BARRAGENS.items():
        if indice_tabela >= len(tabelas):
            continue

        tabela = tabelas[indice_tabela]
        linhas = tabela.find_all("tr")

        for linha in linhas:
            colunas = [c.get_text(" ", strip=True) for c in linha.find_all(["td", "th"])]

            if len(colunas) < 9:
                continue

            if "Data" in colunas[0] or "Montante" in " ".join(colunas):
                continue

            data_hora = converter_data_hora(colunas[0])
            if not data_hora:
                continue

            registros.append({
                "data_hora": data_hora,
                "barragem": config["barragem"],
                "cidade": config["cidade"],
                "montante_m": converter_numero(colunas[1]),
                "diferenca_m": converter_numero(colunas[2]),
                "jusante_m": converter_numero(colunas[3]),
                "comportas_abertas": converter_inteiro(colunas[4]),
                "comportas_fechadas": converter_inteiro(colunas[5]),
                "extravasor_m": converter_numero(colunas[6]),
                "indicador_pluviometrico_mm": converter_numero(colunas[7]),
                "tempo_status": colunas[8],
            })

    return registros


def salvar_registros(registros):
    conn = get_connection()
    cursor = conn.cursor()

    total = 0

    for item in registros:
        cursor.execute("""
            INSERT INTO barragens_defesa_civil_rio_sul (
                data_hora,
                barragem,
                cidade,
                montante_m,
                diferenca_m,
                jusante_m,
                comportas_abertas,
                comportas_fechadas,
                extravasor_m,
                indicador_pluviometrico_mm,
                tempo_status,
                fonte
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data_hora, barragem, cidade, fonte) DO UPDATE SET
                montante_m = EXCLUDED.montante_m,
                diferenca_m = EXCLUDED.diferenca_m,
                jusante_m = EXCLUDED.jusante_m,
                comportas_abertas = EXCLUDED.comportas_abertas,
                comportas_fechadas = EXCLUDED.comportas_fechadas,
                extravasor_m = EXCLUDED.extravasor_m,
                indicador_pluviometrico_mm = EXCLUDED.indicador_pluviometrico_mm,
                tempo_status = EXCLUDED.tempo_status,
                coletado_em = NOW();
        """, (
            item["data_hora"],
            item["barragem"],
            item["cidade"],
            item["montante_m"],
            item["diferenca_m"],
            item["jusante_m"],
            item["comportas_abertas"],
            item["comportas_fechadas"],
            item["extravasor_m"],
            item["indicador_pluviometrico_mm"],
            item["tempo_status"],
            FONTE,
        ))

        total += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return total


def main():
    print("Coletando barragens da Defesa Civil de Rio do Sul...")

    registros = extrair_barragens()

    if not registros:
        print("Nenhum registro encontrado.")
        return

    total = salvar_registros(registros)

    print(f"Registros extraídos: {len(registros)}")
    print(f"Registros salvos/atualizados: {total}")


if __name__ == "__main__":
    main()