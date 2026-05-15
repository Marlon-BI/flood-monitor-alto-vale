import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from src.database.conexao import get_connection


URL = "https://defesacivil.riodosul.sc.gov.br/index.php?r=externo%2Fmetragem-sensores"
FONTE = "Defesa Civil Rio do Sul"
CIDADE = "Rio do Sul"
ESTACAO = "Sensor Ponte Dom Tito Buss"


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


def buscar_tabela_defesa_civil():
    response = requests.get(URL, timeout=60)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    tabelas = soup.find_all("table")

    for tabela in tabelas:
        texto = tabela.get_text(" ", strip=True)

        if "Taxa Chuva" in texto or "Chuva Acum" in texto or "Ind.Pluv" in texto:
            return tabela

    raise RuntimeError("Tabela de chuva/nível não encontrada na página da Defesa Civil.")


def extrair_linhas():
    tabela = buscar_tabela_defesa_civil()
    linhas_extraidas = []

    linhas = tabela.find_all("tr")

    for linha in linhas:
        colunas = [c.get_text(" ", strip=True) for c in linha.find_all(["td", "th"])]

        if len(colunas) < 5:
            continue

        if "Data" in colunas[0] or "Nível" in " ".join(colunas):
            continue

        # Tela completa:
        # Data | Nível | Diferença | Taxa Chuva (mm/h) | Chuva Acum. Dia (mm) | Temp (°C)
        # Tela lateral:
        # Data Hora | Nível | Diferença | Ind.Pluv. | Tempo
        data_hora = converter_data_hora(colunas[0])
        if not data_hora:
            continue

        nivel_metros = converter_numero(colunas[1]) if len(colunas) > 1 else None
        diferenca_m = converter_numero(colunas[2]) if len(colunas) > 2 else None

        taxa_chuva_mm_h = None
        chuva_acumulada_dia_mm = None
        temperatura_c = None
        tempo_status = None

        if len(colunas) >= 6:
            taxa_chuva_mm_h = converter_numero(colunas[3])
            chuva_acumulada_dia_mm = converter_numero(colunas[4])
            temperatura_c = converter_numero(colunas[5])
        elif len(colunas) >= 5:
            taxa_chuva_mm_h = converter_numero(colunas[3])
            tempo_status = colunas[4]

        linhas_extraidas.append({
            "data_hora": data_hora,
            "nivel_metros": nivel_metros,
            "diferenca_m": diferenca_m,
            "taxa_chuva_mm_h": taxa_chuva_mm_h,
            "chuva_acumulada_dia_mm": chuva_acumulada_dia_mm,
            "temperatura_c": temperatura_c,
            "tempo_status": tempo_status,
        })

    return linhas_extraidas


def salvar_dados(linhas):
    conn = get_connection()
    cursor = conn.cursor()

    inseridos = 0

    for item in linhas:
        cursor.execute("""
            INSERT INTO chuva_real_defesa_civil_rio_sul (
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
                diferenca_m = EXCLUDED.diferenca_m,
                taxa_chuva_mm_h = EXCLUDED.taxa_chuva_mm_h,
                chuva_acumulada_dia_mm = EXCLUDED.chuva_acumulada_dia_mm,
                temperatura_c = EXCLUDED.temperatura_c,
                tempo_status = EXCLUDED.tempo_status,
                coletado_em = NOW();
        """, (
            item["data_hora"],
            CIDADE,
            ESTACAO,
            item["nivel_metros"],
            item["diferenca_m"],
            item["taxa_chuva_mm_h"],
            item["chuva_acumulada_dia_mm"],
            item["temperatura_c"],
            item["tempo_status"],
            FONTE,
        ))

        inseridos += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return inseridos


def main():
    print("Coletando chuva real da Defesa Civil de Rio do Sul...")

    linhas = extrair_linhas()

    if not linhas:
        print("Nenhuma linha encontrada.")
        return

    inseridos = salvar_dados(linhas)

    print(f"Linhas extraídas: {len(linhas)}")
    print(f"Registros salvos/atualizados: {inseridos}")


if __name__ == "__main__":
    main()