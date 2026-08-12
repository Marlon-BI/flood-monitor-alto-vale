import unittest
from unittest.mock import MagicMock, patch

from src.coleta.orquestrador import Etapa, executar_etapas, houve_falha_critica


def _mock_completed_process(returncode):
    processo = MagicMock()
    processo.returncode = returncode
    return processo


class TestExecutarEtapas(unittest.TestCase):
    @patch("src.coleta.orquestrador.subprocess.run")
    def test_a_todas_as_criticas_passam_exit_0(self, mock_run):
        mock_run.return_value = _mock_completed_process(0)

        etapas = [
            Etapa("RIO", "src.coleta.salvar_rio", critica=True),
            Etapa("CHUVA_REAL_DC", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul", critica=True),
            Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False),
        ]

        resultados, exit_code = executar_etapas("PIPELINE CRÍTICO", etapas)

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_run.call_count, 3)
        self.assertTrue(all(r.sucesso for r in resultados))

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_b_rio_falha_demais_etapas_ainda_executam_exit_diferente_de_0(self, mock_run):
        mock_run.side_effect = [
            _mock_completed_process(1),  # RIO falha
            _mock_completed_process(0),  # CHUVA_REAL_DC ok
            _mock_completed_process(0),  # BARRAGENS ok
        ]

        etapas = [
            Etapa("RIO", "src.coleta.salvar_rio", critica=True),
            Etapa("CHUVA_REAL_DC", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul", critica=True),
            Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False),
        ]

        resultados, exit_code = executar_etapas("PIPELINE CRÍTICO", etapas)

        self.assertEqual(mock_run.call_count, 3, "demais etapas devem executar mesmo com falha crítica")
        self.assertNotEqual(exit_code, 0)
        self.assertFalse(resultados[0].sucesso)
        self.assertTrue(resultados[1].sucesso)
        self.assertTrue(resultados[2].sucesso)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_c_chuva_real_dc_falha_demais_etapas_executam_exit_diferente_de_0(self, mock_run):
        mock_run.side_effect = [
            _mock_completed_process(0),  # RIO ok
            _mock_completed_process(1),  # CHUVA_REAL_DC falha
            _mock_completed_process(0),  # BARRAGENS ok
        ]

        etapas = [
            Etapa("RIO", "src.coleta.salvar_rio", critica=True),
            Etapa("CHUVA_REAL_DC", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul", critica=True),
            Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False),
        ]

        resultados, exit_code = executar_etapas("PIPELINE CRÍTICO", etapas)

        self.assertEqual(mock_run.call_count, 3)
        self.assertNotEqual(exit_code, 0)
        self.assertTrue(resultados[0].sucesso)
        self.assertFalse(resultados[1].sucesso)
        self.assertTrue(resultados[2].sucesso)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_d_etapa_nao_critica_falha_mantem_exit_0(self, mock_run):
        mock_run.side_effect = [
            _mock_completed_process(0),  # RIO ok
            _mock_completed_process(0),  # CHUVA_REAL_DC ok
            _mock_completed_process(1),  # BARRAGENS falha (não crítica)
        ]

        etapas = [
            Etapa("RIO", "src.coleta.salvar_rio", critica=True),
            Etapa("CHUVA_REAL_DC", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul", critica=True),
            Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False),
        ]

        resultados, exit_code = executar_etapas("PIPELINE CRÍTICO", etapas)

        self.assertEqual(exit_code, 0)
        self.assertFalse(resultados[2].sucesso)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_e_resumo_final_contem_estados_corretos(self, mock_run):
        mock_run.side_effect = [
            _mock_completed_process(1),  # RIO falha
            _mock_completed_process(0),  # CHUVA_REAL_DC ok
        ]

        etapas = [
            Etapa("RIO", "src.coleta.salvar_rio", critica=True),
            Etapa("CHUVA_REAL_DC", "src.coleta.coletar_chuva_real_defesa_civil_rio_sul", critica=True),
        ]

        resultados, _ = executar_etapas("PIPELINE CRÍTICO", etapas)

        self.assertEqual(len(resultados), 2)
        self.assertEqual(resultados[0].etapa.nome, "RIO")
        self.assertFalse(resultados[0].sucesso)
        self.assertEqual(resultados[0].returncode, 1)
        self.assertEqual(resultados[1].etapa.nome, "CHUVA_REAL_DC")
        self.assertTrue(resultados[1].sucesso)
        self.assertEqual(resultados[1].returncode, 0)


class TestHouveFalhaCritica(unittest.TestCase):
    @patch("src.coleta.orquestrador.subprocess.run")
    def test_falha_nao_critica_isolada_nao_conta_como_critica(self, mock_run):
        mock_run.return_value = _mock_completed_process(1)
        etapas = [Etapa("BARRAGENS", "src.coleta.coletar_barragens", critica=False)]
        resultados, _ = executar_etapas("TESTE", etapas)
        self.assertFalse(houve_falha_critica(resultados))


if __name__ == "__main__":
    unittest.main()
