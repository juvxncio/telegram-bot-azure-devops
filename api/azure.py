import os
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class AzureDevOpsAPI:
    def __init__(
        self,
        pat: str = None,
        url_base: str = None,
        lista_times_ignorados: list = None,
    ):
        self.pat = pat or os.getenv('PAT')
        self.url_base = url_base or os.getenv('URL_BASE')
        self.url_projetos = f'{self.url_base}_apis/projects?api-version=7.0'
        if lista_times_ignorados is None:
            lt = os.getenv('lista_times_ignorados')
            self.lista_times_ignorados = lt.split(',') if lt else []
        else:
            self.lista_times_ignorados = lista_times_ignorados
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth('', self.pat)

    def _get(self, url, params=None):
        try:
            r = self.session.get(url, params=params, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except requests.RequestException:
            return None

    def puxar_projetos(self):
        lista_projetos = []
        data = self._get(self.url_projetos)
        if not data:
            return []

        for projeto in data['value']:
            if 'SUSPENSO' not in projeto['name'].upper():
                lista_projetos.append(projeto['name'])
        return lista_projetos

    def puxar_times(self, lista_projetos):
        lista_todos_times = []
        for projeto in lista_projetos:
            url = f'{self.url_base}_apis/projects/{projeto}/teams?api-version=7.0'
            data = self._get(url)
            if not data:
                continue
            for time in data.get('value', []):
                lista_todos_times.append(time['name'])
        return lista_todos_times

    def mesclar_projeto_com_time(self, lista_projetos, lista_todos_times):
        lista_times_ativos = []
        projetos_times = []
        time_index = 0

        for time in lista_todos_times:
            if not any(
                palavra in time for palavra in self.lista_times_ignorados
            ):
                lista_times_ativos.append(time)

        for projeto in lista_projetos:
            if time_index >= len(lista_times_ativos):
                break
            projetos_times.append((projeto, lista_times_ativos[time_index]))
            time_index += 1

            if (
                projeto.startswith('CODAE') or projeto.startswith('COPED')
            ) and time_index < len(lista_times_ativos):
                projetos_times.append(
                    (projeto, lista_times_ativos[time_index])
                )
                time_index += 1
        return projetos_times

    def _filtra_sprints(
        self,
        projetos_times,
        mes_inicio=None,
        ano_inicio=None,
        tipo_filtro='igual',
    ):
        mes_atual = mes_inicio or datetime.now().month
        ano_atual = ano_inicio or datetime.now().year

        sprints_filtradas = []

        for projeto, time in projetos_times:
            url = f'{self.url_base}/{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations?api-version=7.0'
            data = self._get(url)
            if not data:
                continue

            for sprint in data.get('value', []):
                start_raw = sprint['attributes'].get('startDate')
                finish_raw = sprint['attributes'].get('finishDate')
                if not start_raw or not finish_raw:
                    continue

                inicio = datetime.fromisoformat(
                    start_raw.replace('Z', '+00:00')
                )

                if tipo_filtro == 'igual':
                    if inicio.month == mes_atual and inicio.year == ano_atual:
                        sprints_filtradas.append((projeto, time, sprint['id']))
                elif tipo_filtro == 'a_partir':
                    if (inicio.year > ano_atual) or (
                        inicio.year == ano_atual and inicio.month >= mes_atual
                    ):
                        sprints_filtradas.append((projeto, time, sprint['id']))

        return sprints_filtradas

    def busca_sprint(self, projetos_times, mes_alvo=None, ano_alvo=None):
        return self._filtra_sprints(
            projetos_times, mes_alvo, ano_alvo, tipo_filtro='igual'
        )

    def busca_sprints(self, projetos_times, mes_alvo=None, ano_alvo=None):
        return self._filtra_sprints(
            projetos_times, mes_alvo, ano_alvo, tipo_filtro='a_partir'
        )

    def busca_id_work_items(self, projeto, time, sprint_id):
        url = f'{self.url_base}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations/{sprint_id}/workitems?api-version=7.0'
        data = self._get(url)
        if not data:
            return []
        items_data = data.get('workItemRelations', [])
        return [
            str(item['target']['id'])
            for item in items_data
            if 'target' in item
        ]

    @staticmethod
    def _chunk_list(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i : i + size]

    def _busca_work_items_por_chunks(self, projeto, ids, fields):
        work_items = []
        if not ids:
            return work_items

        fields_str = ','.join(fields)
        for chunk in self._chunk_list(ids, 200):
            ids_str = ','.join(chunk)
            url = f'{self.url_base}{quote(projeto)}/_apis/wit/workitems?ids={ids_str}&fields={fields_str}&api-version=7.0'
            data = self._get(url)
            if not data:
                continue
            work_items.extend(data.get('value', []))

        return work_items

    def busca_horas_work_items(self, projeto, ids):
        horas_por_pessoa = {}
        if not ids:
            return horas_por_pessoa

        fields = [
            'System.AssignedTo',
            'Microsoft.VSTS.Scheduling.CompletedWork',
        ]
        work_items = self._busca_work_items_por_chunks(projeto, ids, fields)

        for wi in work_items:
            assigned_to = (
                wi['fields']
                .get('System.AssignedTo', {})
                .get('displayName', 'Sem responsável')
            )
            horas = wi['fields'].get(
                'Microsoft.VSTS.Scheduling.CompletedWork', 0
            )
            horas_por_pessoa[assigned_to] = (
                horas_por_pessoa.get(assigned_to, 0) + horas
            )

        return horas_por_pessoa

    def busca_campos_work_items(self, projeto, ids):
        fields = [
            'System.Id',
            'System.Title',
            'System.AssignedTo',
            'System.State',
            'System.Description',
            'Microsoft.VSTS.TCM.ReproSteps',
            'Microsoft.VSTS.Common.AcceptanceCriteria',
            'System.WorkItemType',
        ]
        return self._busca_work_items_por_chunks(projeto, ids, fields)

    def busca_done_work_items(self, projeto, ids):
        fields = [
            'System.Id',
            'System.Title',
            'System.AssignedTo',
            'System.State',
            'System.WorkItemType',
            'Microsoft.VSTS.Common.ClosedBy',
        ]
        return self._busca_work_items_por_chunks(projeto, ids, fields)
