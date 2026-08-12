"""Lógica compartilhada de execução de etapas de coleta.

Cada etapa roda em subprocesso isolado (``python -m <modulo>``) e nunca
interrompe as demais etapas, mesmo em caso de falha. Etapas marcadas como
``critica=True`` fazem o pipeline retornar exit code != 0 ao final caso
falhem — isso é o que faz o GitHub Actions marcar o job como FAILURE.
Etapas não críticas podem falhar sem derrubar o job, mas a falha continua
visível no resumo final impresso.
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Etapa:
    nome: str
    modulo: str
    critica: bool = False


@dataclass
class ResultadoEtapa:
    etapa: Etapa
    sucesso: bool
    duracao_s: float
    returncode: int


def _formatar_duracao(duracao_s: float) -> str:
    if duracao_s < 60:
        return f"{duracao_s:.1f}s"
    minutos, segundos = divmod(duracao_s, 60)
    return f"{int(minutos)}m{segundos:04.1f}s"


def executar_etapa(etapa: Etapa) -> ResultadoEtapa:
    print(f"\n[{datetime.now()}] {etapa.nome} ({etapa.modulo})...")

    inicio = time.perf_counter()
    resultado = subprocess.run(
        [sys.executable, "-m", etapa.modulo],
        check=False,
    )
    duracao_s = time.perf_counter() - inicio

    sucesso = resultado.returncode == 0

    if sucesso:
        print(f"Etapa concluída: {etapa.nome} ({_formatar_duracao(duracao_s)})")
    else:
        rotulo = "CRÍTICA" if etapa.critica else "não crítica"
        print(
            f"Falha na etapa '{etapa.nome}' ({rotulo}): "
            f"módulo {etapa.modulo} retornou código {resultado.returncode}"
        )
        print("Continuando para a próxima etapa...")

    return ResultadoEtapa(
        etapa=etapa,
        sucesso=sucesso,
        duracao_s=duracao_s,
        returncode=resultado.returncode,
    )


def imprimir_resumo(titulo: str, resultados: list[ResultadoEtapa]) -> None:
    print(f"\n{titulo}")
    for r in resultados:
        status = "OK" if r.sucesso else "FAIL"
        marcador = "*" if r.etapa.critica else " "
        print(f"{marcador}{r.etapa.nome:<24}{status:<6}{_formatar_duracao(r.duracao_s)}")

    duracao_total = sum(r.duracao_s for r in resultados)
    print(f"\nDuração total: {_formatar_duracao(duracao_total)}")


def houve_falha_critica(resultados: list[ResultadoEtapa]) -> bool:
    return any(not r.sucesso and r.etapa.critica for r in resultados)


def executar_etapas(titulo: str, etapas: list[Etapa]) -> tuple[list[ResultadoEtapa], int]:
    """Executa todas as etapas (nunca para no meio) e retorna (resultados, exit_code).

    exit_code é != 0 somente se alguma etapa CRÍTICA falhar. Falhas em
    etapas não críticas ficam registradas no resumo, mas não derrubam o job.
    """
    print(f"Iniciando {titulo}...")

    resultados = [executar_etapa(etapa) for etapa in etapas]

    imprimir_resumo(titulo, resultados)

    falha_critica = houve_falha_critica(resultados)
    resultado_final = "FAILURE" if falha_critica else "SUCCESS"
    print(f"\nResultado: {resultado_final}")

    return resultados, (1 if falha_critica else 0)
