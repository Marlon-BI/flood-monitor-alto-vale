import json
from pathlib import Path

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"
FIXTURES_DIR = FIXTURES_ROOT / "asthon"


def carregar(nome_arquivo):
    with open(FIXTURES_DIR / nome_arquivo, encoding="utf-8") as f:
        return json.load(f)


def carregar_json(subdiretorio, nome_arquivo):
    with open(FIXTURES_ROOT / subdiretorio / nome_arquivo, encoding="utf-8") as f:
        return json.load(f)


def carregar_texto(subdiretorio, nome_arquivo):
    with open(FIXTURES_ROOT / subdiretorio / nome_arquivo, encoding="utf-8") as f:
        return f.read()
