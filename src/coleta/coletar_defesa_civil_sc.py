import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from src.database.conexao import get_connection


URL_API = "https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts"


def limpar_html(html):
    soup = BeautifulSoup(html or "", "html.parser")
    texto = soup.get_text(" ", strip=True)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def coletar_boletins():
    print("Buscando boletins da Defesa Civil SC via API WordPress...")

    params = {
        "search": "previsão",
        "per_page": 10,
    }

    try:
        response = requests.get(URL_API, params=params, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar API da Defesa Civil SC: {e}")
        return []

    posts = response.json()

    boletins = []

    for post in posts:
        titulo = limpar_html(post.get("title", {}).get("rendered"))
        url = post.get("link")
        data_publicacao = post.get("date")
        conteudo = limpar_html(post.get("content", {}).get("rendered"))

        if "previsão para os próximos 5 dias" not in titulo.lower():
            continue

        boletins.append({
            "titulo": titulo,
            "url": url,
            "data_publicacao": datetime.fromisoformat(data_publicacao),
            "resumo": conteudo[:3000],
        })

    return boletins


def salvar_boletins(boletins):
    conn = get_connection()
    cursor = conn.cursor()

    inseridos = 0
    atualizados = 0

    for b in boletins:
        try:
            cursor.execute("""
                INSERT INTO boletins_defesa_civil_sc (
                    titulo,
                    url,
                    data_publicacao,
                    resumo
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    titulo = EXCLUDED.titulo,
                    data_publicacao = EXCLUDED.data_publicacao,
                    resumo = EXCLUDED.resumo,
                    coletado_em = NOW();
            """, (
                b["titulo"],
                b["url"],
                b["data_publicacao"],
                b["resumo"]
            ))

            if cursor.rowcount == 1:
                inseridos += 1

        except Exception as e:
            conn.rollback()
            print("Erro ao inserir/atualizar:", e)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Boletins processados: {len(boletins)}")


if __name__ == "__main__":
    boletins = coletar_boletins()

    if not boletins:
        print("Nenhum boletim coletado.")
    else:
        salvar_boletins(boletins)