from unittest.mock import MagicMock

from api.relatorios import Relatorios


def _api_mock():
    api = MagicMock()
    api.puxar_projetos.return_value = ['ProjA']
    api.puxar_times.return_value = ['TimeA']
    api.mesclar_projeto_com_time.return_value = [('ProjA', 'TimeA')]
    api.busca_sprint.return_value = [('ProjA', 'TimeA', 'sprint1')]
    api.busca_id_work_items.return_value = ['1']
    api.busca_campos_work_items.return_value = []
    api.busca_done_work_items.return_value = []
    api.busca_horas_work_items.return_value = {}
    return api


def test_regex_nao_quebra_com_caracteres_especiais_no_template():
    api = _api_mock()
    api.busca_campos_work_items.return_value = [
        {
            'id': 1,
            'fields': {
                'System.WorkItemType': 'Bug',
                'System.State': 'Done',
                'System.AssignedTo': {'displayName': 'Fulano'},
                'System.Title': 'Bug 1',
                'Microsoft.VSTS.TCM.ReproSteps': '',
            },
        }
    ]

    relatorios = Relatorios(api)
    texto = relatorios.gera_relatorio_descricao('Bug', mes=1, ano=2026)

    assert 'Bug' in texto


def test_gera_relatorio_completo_busca_contexto_uma_unica_vez():
    api = _api_mock()

    relatorios = Relatorios(api)
    relatorios.gera_relatorio_completo(mes=1, ano=2026)

    assert api.puxar_projetos.call_count == 1
    assert api.puxar_times.call_count == 1
    assert api.mesclar_projeto_com_time.call_count == 1
    assert api.busca_sprint.call_count == 1
    assert api.busca_id_work_items.call_count == 1
