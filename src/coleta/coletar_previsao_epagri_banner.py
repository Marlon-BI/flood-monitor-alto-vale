import re
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import requests
import pytesseract
from PIL import Image, ImageOps, ImageEnhance

from src.database.conexao import get_connection
from src.coleta.municipios_bacia import MUNICIPIOS_BACIA_IBGE


TMP_DIR = Path("tmp_epagri")
MODELO = "GFS"
BASE_URL = "https://ciram.epagri.sc.gov.br/meteogramas/figs/banner/gfs"

TIMEOUT_SEGUNDOS = 60
PAUSA_ENTRE_MUNICIPIOS_SEGUNDOS = 2


def preparar_tmp():
    TMP_DIR.mkdir(exist_ok=True)


def limpar_tmp():
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def buscar_pasta_valida(codigo_ibge: str) -> str:
    for dias in range(0, 5):
        data = datetime.now() - timedelta(days=dias)
        data_formatada = data.strftime("%Y%m%d")

        for rodada in ["00", "12"]:
            pasta = f"{data_formatada}{rodada}"
            url = f"{BASE_URL}/{pasta}/{codigo_ibge}.png"

            try:
                resposta = requests.head(url, timeout=10, allow_redirects=True)
                if resposta.status_code == 200:
                    return pasta
            except Exception:
                continue

    raise RuntimeError(f"Nenhuma pasta válida encontrada para {codigo_ibge}")


def baixar_banner(codigo_ibge: str, pasta: str) -> Path:
    url = f"{BASE_URL}/{pasta}/{codigo_ibge}.png"
    arquivo = TMP_DIR / f"{codigo_ibge}.png"

    resposta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
    resposta.raise_for_status()

    arquivo.write_bytes(resposta.content)
    return arquivo


def tratar_imagem_para_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = img.resize((img.width * 2, img.height * 2))
    return img


def limpar_decimal(texto: str):
    texto = texto.replace(",", ".")
    texto = re.sub(r"[^0-9.]", "", texto)

    match = re.search(r"\d+\.\d+|\d+", texto)
    return float(match.group(0)) if match else None


def limpar_inteiro(texto: str):
    texto = re.sub(r"[^0-9]", "", texto)

    if not texto:
        return None

    valor = int(texto)

    if 0 <= valor <= 100:
        return valor

    return None


def ocr_decimal(img: Image.Image):
    texto = pytesseract.image_to_string(
        img,
        lang="eng",
        config="--psm 7 -c tessedit_char_whitelist=0123456789.,"
    ).strip()

    return limpar_decimal(texto), texto


def ocr_inteiro(img: Image.Image):
    texto = pytesseract.image_to_string(
        img,
        lang="eng",
        config="--psm 7 -c tessedit_char_whitelist=0123456789"
    ).strip()

    return limpar_inteiro(texto), texto


def extrair_numeros_linha(texto: str):
    texto = texto.replace(",", ".")
    return re.findall(r"\d+\.\d+|\d+", texto)


def ocr_linha_chuva_prob(img: Image.Image):
    img_ocr = tratar_imagem_para_ocr(img)

    texto = pytesseract.image_to_string(
        img_ocr,
        lang="eng",
        config="--psm 6 -c tessedit_char_whitelist=0123456789., "
    ).strip()

    numeros = extrair_numeros_linha(texto)

    chuva = None
    prob = None

    if len(numeros) >= 1:
        chuva = float(numeros[0])

    if len(numeros) >= 2:
        prob = int(float(numeros[-1]))

        if not 0 <= prob <= 100:
            prob = None

    return chuva, prob, texto


def extrair_chuva_probabilidade(
    arquivo: Path,
    codigo_ibge: str,
    municipio: str,
    pasta_modelo: str,
    salvar_debug: bool = False
):
    img = Image.open(arquivo).convert("RGB")

    largura_card = img.width / 5
    altura = img.height
    data_base = datetime.strptime(pasta_modelo[:8], "%Y%m%d").date()

    resultados = []

    for i in range(5):
        card_x = int(i * largura_card)

        y1 = int(altura * 0.815)
        y2 = int(altura * 0.925)

        chuva_crop = img.crop((
            int(card_x + largura_card * 0.04),
            y1,
            int(card_x + largura_card * 0.34),
            y2
        ))

        prob_crop = img.crop((
            int(card_x + largura_card * 0.55),
            y1,
            int(card_x + largura_card * 0.78),
            y2
        ))

        linha_crop = img.crop((
            int(card_x + largura_card * 0.02),
            y1,
            int(card_x + largura_card * 0.94),
            y2
        ))

        chuva_ocr = tratar_imagem_para_ocr(chuva_crop)
        prob_ocr = tratar_imagem_para_ocr(prob_crop)

        chuva_mm, chuva_txt = ocr_decimal(chuva_ocr)
        prob_pct, prob_txt = ocr_inteiro(prob_ocr)

        linha_txt = ""

        if chuva_mm is None or prob_pct is None:
            chuva_linha, prob_linha, linha_txt = ocr_linha_chuva_prob(linha_crop)

            if chuva_mm is None:
                chuva_mm = chuva_linha

            if prob_pct is None:
                prob_pct = prob_linha

        if salvar_debug:
            prefixo = f"{codigo_ibge}_card_{i + 1}"
            chuva_crop.save(TMP_DIR / f"{prefixo}_chuva_original.png")
            prob_crop.save(TMP_DIR / f"{prefixo}_prob_original.png")
            linha_crop.save(TMP_DIR / f"{prefixo}_linha_original.png")
            chuva_ocr.save(TMP_DIR / f"{prefixo}_chuva_tratada.png")
            prob_ocr.save(TMP_DIR / f"{prefixo}_prob_tratada.png")

        resultados.append({
            "codigo_ibge": codigo_ibge,
            "municipio": municipio,
            "modelo": MODELO,
            "pasta_modelo": pasta_modelo,
            "dia_previsao": i + 1,
            "data_previsao": data_base + timedelta(days=i),
            "chuva_mm": chuva_mm,
            "probabilidade_chuva_pct": prob_pct,
            "ocr_chuva": chuva_txt,
            "ocr_probabilidade": prob_txt,
            "ocr_linha": linha_txt,
            "fonte": "EPAGRI/CIRAM",
            "coletado_em": datetime.now(),
        })

    return resultados


def coletar_municipio(codigo_ibge: str, municipio: str, salvar_debug: bool = False):
    pasta = buscar_pasta_valida(codigo_ibge)
    arquivo = baixar_banner(codigo_ibge, pasta)

    return extrair_chuva_probabilidade(
        arquivo=arquivo,
        codigo_ibge=codigo_ibge,
        municipio=municipio,
        pasta_modelo=pasta,
        salvar_debug=salvar_debug
    )


def salvar_previsoes_no_banco(registros):
    if not registros:
        print("Nenhum registro para salvar.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO public.hidro_previsao_epagri_ciram_ocr (
            codigo_ibge,
            municipio,
            modelo,
            pasta_modelo,
            dia_previsao,
            data_previsao,
            chuva_mm,
            probabilidade_chuva_pct,
            fonte,
            coletado_em
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (
            codigo_ibge,
            data_previsao,
            modelo
        )
        DO UPDATE SET
            municipio = EXCLUDED.municipio,
            pasta_modelo = EXCLUDED.pasta_modelo,
            dia_previsao = EXCLUDED.dia_previsao,
            chuva_mm = EXCLUDED.chuva_mm,
            probabilidade_chuva_pct = EXCLUDED.probabilidade_chuva_pct,
            fonte = EXCLUDED.fonte,
            coletado_em = EXCLUDED.coletado_em;
    """

    for r in registros:
        cursor.execute(sql, (
            r["codigo_ibge"],
            r["municipio"],
            r["modelo"],
            r["pasta_modelo"],
            r["dia_previsao"],
            r["data_previsao"],
            r["chuva_mm"],
            r["probabilidade_chuva_pct"],
            r["fonte"],
            r["coletado_em"],
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Previsões salvas no banco: {len(registros)}")


def executar():
    preparar_tmp()

    todos_resultados = []
    municipios_sucesso = 0
    municipios_falha = 0
    manter_tmp_debug = False

    try:
        for item in MUNICIPIOS_BACIA_IBGE:
            codigo_ibge = item["codigo_ibge"]
            municipio = item["municipio"]

            print(f"Coletando previsão EPAGRI/CIRAM para {municipio} ({codigo_ibge})...")

            try:
                resultados = coletar_municipio(
                    codigo_ibge=codigo_ibge,
                    municipio=municipio,
                    salvar_debug=False
                )

                todos_resultados.extend(resultados)
                municipios_sucesso += 1

                total_chuva = sum(r["chuva_mm"] or 0 for r in resultados)

                print(
                    f"{municipio}: {len(resultados)} dias extraídos | "
                    f"chuva acumulada 5d={total_chuva:.1f} mm"
                )

            except Exception as erro:
                municipios_falha += 1
                print(f"Erro ao coletar {municipio}: {erro}")

            time.sleep(PAUSA_ENTRE_MUNICIPIOS_SEGUNDOS)

        print()
        print("RESUMO FINAL")
        print("-" * 60)
        print(f"Municípios com sucesso: {municipios_sucesso}")
        print(f"Municípios com falha: {municipios_falha}")
        print(f"Registros extraídos: {len(todos_resultados)}")

        print()
        print("AMOSTRA")
        print("-" * 60)

        for r in todos_resultados[:15]:
            print(
                f"{r['municipio']} | "
                f"{r['data_previsao']} | "
                f"chuva={r['chuva_mm']} mm | "
                f"prob={r['probabilidade_chuva_pct']}%"
            )

        salvar_previsoes_no_banco(todos_resultados)

    finally:
        if manter_tmp_debug:
            print()
            print(f"Debug mantido em: {TMP_DIR.resolve()}")
        else:
            limpar_tmp()


if __name__ == "__main__":
    executar()