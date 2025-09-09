import re
from datetime import datetime
from babel.dates import format_date
from api.azure import AzureDevOpsAPI
from utils.datas import calcular_horas_uteis
import os


class Relatorios:
    def __init__(self, api: AzureDevOpsAPI):
        self.api = api
        self.template_task = os.getenv('TEMPLATE_PADRAO_TASK')
        self.template_bug = os.getenv('TEMPLATE_PADRAO_BUG')
        self.template_pbi = os.getenv('TEMPLATE_PADRAO_PBI')
        self.template_criterios = os.getenv(
            'TEMPLATE_PADRAO_CRITERIOS_DE_ACEITE'
        )
        self.dominio_autorizado_done = os.getenv('DOMINIO_AUTORIZADO_DONE')

    def gera_relatorio_descricao(
        self, tipo_solicitado=None, mes=None, ano=None
    ):
        checklist = []

        if tipo_solicitado:
            tipo_solicitado = tipo_solicitado.title()

        if tipo_solicitado in ['História', 'Historia']:
            tipo_solicitado = 'Product Backlog Item'
            checklist = [
                {
                    'nome': 'Descrição',
                    'campo': 'System.Description',
                    'valor': '',
                    'template': self.template_pbi,
                },
                {
                    'nome': 'Critérios de Aceite',
                    'campo': 'Microsoft.VSTS.Common.AcceptanceCriteria',
                    'valor': '',
                    'template': self.template_criterios,
                },
            ]
        elif tipo_solicitado == 'Bug':
            checklist = [
                {
                    'nome': 'Descrição',
                    'campo': 'Microsoft.VSTS.TCM.ReproSteps',
                    'valor': '',
                    'template': self.template_bug,
                }
            ]
        elif tipo_solicitado == 'Task':
            checklist = [
                {
                    'nome': 'Descrição',
                    'campo': 'System.Description',
                    'valor': '',
                    'template': self.template_task,
                }
            ]
        else:
            return f'❌ Tipo de work item "{tipo_solicitado}" inválido.'

        itens_a_checar = ', '.join([item['nome'] for item in checklist])

        lista_projetos = self.api.puxar_projetos()
        lista_todos_times = self.api.puxar_times(lista_projetos)
        projetos_times = self.api.mesclar_projeto_com_time(
            lista_projetos, lista_todos_times
        )

        work_items_por_pessoa = {}
        ids_por_pessoa = {}

        sprints = self.api.busca_sprint(
            projetos_times, mes_alvo=mes, ano_alvo=ano
        )
        for projeto, time, sprint_id in sprints:
            ids = self.api.busca_id_work_items(projeto, time, sprint_id)
            wi = self.api.busca_campos_work_items(projeto, ids)
            for work_item in wi:
                fields = work_item.get('fields', {})
                tipo = fields.get('System.WorkItemType', '')
                assigned_to = fields.get('System.AssignedTo', {}).get(
                    'displayName', 'Sem responsável'
                )
                wid = str(work_item['id'])
                title = fields.get('System.Title', '(sem título)')
                state = fields.get('System.State')

                for item in checklist:
                    item['valor'] = re.sub(
                        rf'{item["template"][:20]}.+{item["template"][-15:]}\s*',
                        '',
                        fields.get(item['campo'], ''),
                    )

                    if (
                        tipo == tipo_solicitado
                        and state == 'Done'
                        and (
                            item['valor'] == ''
                            or item['valor'] == item['template']
                        )
                    ):
                        work_items_por_pessoa[assigned_to] = (
                            work_items_por_pessoa.get(assigned_to, 0) + 1
                        )
                        ids_por_pessoa.setdefault(assigned_to, []).append(
                            f'#{wid} - {title} (sem {item["nome"]})'
                        )

        data = datetime(
            ano or datetime.now().year, mes or datetime.now().month, 1
        )
        mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

        if not work_items_por_pessoa:
            return f'✅ Nenhum(a) {tipo_solicitado} sem descrição encontrada em {mes_nome}.\n\n'

        texto = (
            f'⚠️ {tipo_solicitado}(s) sem {itens_a_checar} em {mes_nome}:\n\n'
        )
        for pessoa, qtd in sorted(
            work_items_por_pessoa.items(), key=lambda x: x[1], reverse=True
        ):
            texto += f'👤 {pessoa}: {qtd} {tipo_solicitado}(s)\n'
            texto += '\n'.join(ids_por_pessoa[pessoa]) + '\n\n'

        return texto

    def gera_relatorio_horas(self, mes=None, ano=None):
        lista_projetos = self.api.puxar_projetos()
        lista_todos_times = self.api.puxar_times(lista_projetos)
        projetos_times = self.api.mesclar_projeto_com_time(
            lista_projetos, lista_todos_times
        )

        total_por_pessoa = {}
        sprints = self.api.busca_sprint(
            projetos_times, mes_alvo=mes, ano_alvo=ano
        )

        for projeto, time, sprint_id in sprints:
            ids = self.api.busca_id_work_items(projeto, time, sprint_id)
            horas = self.api.busca_horas_work_items(projeto, ids)
            for pessoa, total in horas.items():
                total_por_pessoa[pessoa] = (
                    total_por_pessoa.get(pessoa, 0) + total
                )

        data = datetime(
            ano or datetime.now().year, mes or datetime.now().month, 1
        )
        mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')
        horas_uteis = calcular_horas_uteis(data.month, data.year)

        if not total_por_pessoa:
            return f'Nenhuma hora registrada em {mes_nome}.\n\n'

        texto = f'📊 Horas por profissional em {mes_nome}:\n\n'
        for pessoa, horas in sorted(
            total_por_pessoa.items(), key=lambda x: x[0].lower()
        ):
            horas = round(horas, 2)
            faltam = round(horas_uteis - horas, 2)
            if faltam > 0:
                dias = round(faltam / 8, 1)
                texto += (
                    f'{pessoa}: {horas}h (faltam {faltam}h ≈ {dias} dias)\n\n'
                )
            elif faltam < 0:
                excedente = abs(faltam)
                dias_extra = round(excedente / 8, 1)
                texto += f'{pessoa}: {horas}h (+{excedente}h a mais ≈ {dias_extra} dias)\n\n'
            else:
                texto += (
                    f'{pessoa}: {horas}h (exatamente as horas previstas)\n\n'
                )

        texto += f'ℹ️ Horas úteis do mês: {horas_uteis}h\n'
        return texto

    def gera_relatorio_done(self, mes=None, ano=None):
        lista_projetos = self.api.puxar_projetos()
        lista_todos_times = self.api.puxar_times(lista_projetos)
        projetos_times = self.api.mesclar_projeto_com_time(
            lista_projetos, lista_todos_times
        )

        data = datetime(
            ano or datetime.now().year, mes or datetime.now().month, 1
        )
        mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

        dones_nao_autorizados = []
        sprints = self.api.busca_sprint(
            projetos_times, mes_alvo=mes, ano_alvo=ano
        )

        for projeto, time, sprint_id in sprints:
            ids = self.api.busca_id_work_items(projeto, time, sprint_id)
            wi = self.api.busca_done_work_items(projeto, ids)
            for work_item in wi:
                fields = work_item.get('fields', {})
                tipo = fields.get('System.WorkItemType', '')
                wid = str(work_item['id'])
                title = fields.get('System.Title', '(sem título)')
                state = fields.get('System.State')
                info_closed = fields.get('Microsoft.VSTS.Common.ClosedBy')
                autor_done = info_closed['uniqueName'] if info_closed else ''

                if (
                    state == 'Done'
                    and tipo in ['Product Backlog Item', 'Bug']
                    and not autor_done.endswith(self.dominio_autorizado_done)
                ):
                    dones_nao_autorizados.append(
                        f'#{wid} - {title} ({autor_done})\n\n'
                    )

        if not dones_nao_autorizados:
            return f'✅ Nenhuma História ou Bug com Done irregular em {mes_nome}.\n\n'
        return (
            f'⚠️ Histórias/Bugs com Done irregular em {mes_nome}:\n\n'
            + ''.join(dones_nao_autorizados)
        )

    def gera_relatorio_transbordo(self, mes_inicio=None, ano_inicio=None):
        lista_projetos = self.api.puxar_projetos()
        lista_todos_times = self.api.puxar_times(lista_projetos)
        projetos_times = self.api.mesclar_projeto_com_time(
            lista_projetos, lista_todos_times
        )

        lista_tudo = []
        historias_transbordadas = []

        data = datetime(
            ano_inicio or datetime.now().year,
            mes_inicio or datetime.now().month,
            1,
        )
        mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

        sprints = self.api.busca_sprints(
            projetos_times, mes_alvo=mes_inicio, ano_alvo=ano_inicio
        )
        for projeto, time, sprint_id in sprints:
            ids = self.api.busca_id_work_items(projeto, time, sprint_id)
            wi = self.api.busca_done_work_items(projeto, ids)
            for work_item in wi:
                fields = work_item.get('fields', {})
                tipo = fields.get('System.WorkItemType', '')
                wid = str(work_item['id'])
                title = fields.get('System.Title', '(sem título)')

                if tipo == 'Product Backlog Item':
                    if wid in lista_tudo:
                        historias_transbordadas.append(f'#{wid} - {title}\n\n')
                    else:
                        lista_tudo.append(wid)

        if not historias_transbordadas:
            return (
                f'✅ Nenhuma história transbordada a partir de {mes_nome}.\n\n'
            )
        return f'⚠️ Histórias com transbordo em {mes_nome}:\n\n' + ''.join(
            historias_transbordadas
        )
