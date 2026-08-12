import unittest
from unittest.mock import patch

from src.coleta import executar_pipeline_critico, executar_pipeline_pesado, executar_pipeline_once


class TestPipelineCritico(unittest.TestCase):
    def test_rio_e_chuva_real_dc_sao_criticas(self):
        criticas = {e.nome for e in executar_pipeline_critico.ETAPAS if e.critica}
        self.assertEqual(criticas, {"RIO", "CHUVA_REAL_DC"})

    def test_barragens_presente_e_nao_critica(self):
        barragens = next(e for e in executar_pipeline_critico.ETAPAS if e.nome == "BARRAGENS")
        self.assertFalse(barragens.critica)

    def test_nao_contem_etapas_pesadas(self):
        nomes = {e.nome for e in executar_pipeline_critico.ETAPAS}
        self.assertNotIn("PREVISAO_CHUVA", nomes)
        self.assertNotIn("EPAGRI_PREVISAO", nomes)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_main_retorna_0_quando_tudo_ok(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertEqual(executar_pipeline_critico.main(), 0)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_main_retorna_nao_zero_quando_rio_falha(self, mock_run):
        def side_effect(cmd, check):
            processo_mock = unittest.mock.MagicMock()
            processo_mock.returncode = 1 if "salvar_rio" in cmd[-1] else 0
            return processo_mock

        mock_run.side_effect = side_effect

        self.assertNotEqual(executar_pipeline_critico.main(), 0)


class TestPipelinePesado(unittest.TestCase):
    def test_nenhuma_etapa_pesada_e_critica(self):
        self.assertTrue(all(not e.critica for e in executar_pipeline_pesado.ETAPAS))

    def test_contem_previsao_chuva_e_epagri(self):
        nomes = {e.nome for e in executar_pipeline_pesado.ETAPAS}
        self.assertIn("PREVISAO_CHUVA", nomes)
        self.assertIn("EPAGRI_OBSERVADA", nomes)
        self.assertIn("EPAGRI_PREVISAO", nomes)

    def test_nao_contem_rio_nem_chuva_real_dc(self):
        nomes = {e.nome for e in executar_pipeline_pesado.ETAPAS}
        self.assertNotIn("RIO", nomes)
        self.assertNotIn("CHUVA_REAL_DC", nomes)

    @patch("src.coleta.orquestrador.subprocess.run")
    def test_main_retorna_0_mesmo_com_falha_nao_critica(self, mock_run):
        mock_run.return_value.returncode = 1
        self.assertEqual(executar_pipeline_pesado.main(), 0)


class TestPipelineOnce(unittest.TestCase):
    @patch("src.coleta.executar_pipeline_once.executar_etapas")
    def test_agrega_criterio_e_pesado_e_propaga_pior_exit_code(self, mock_executar):
        mock_executar.side_effect = [([], 1), ([], 0)]

        resultado = executar_pipeline_once.main()

        self.assertEqual(resultado, 1)
        self.assertEqual(mock_executar.call_count, 2)


if __name__ == "__main__":
    unittest.main()
