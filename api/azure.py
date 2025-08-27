import os
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

PAT = os.getenv('PAT')
URL_BASE = os.getenv('URL_BASE')
URL_PROJETOS = f'{URL_BASE}_apis/projects?api-version=7.0'

lista_times_ignorados_str = os.getenv('lista_times_ignorados')
lista_times_ignorados = (
    lista_times_ignorados_str.split(',') if lista_times_ignorados_str else []
)


def puxar_projetos():
    lista_projetos = []
    response = requests.get(URL_PROJETOS, auth=HTTPBasicAuth('', PAT))
    if response.status_code == 200:
        projetos = response.json()['value']
        for projeto in projetos:
            if 'SUSPENSO' not in projeto['name'].upper():
                lista_projetos.append(projeto['name'])
    return lista_projetos


def puxar_times(lista_projetos):
    url_times = []
    lista_todos_times = []

    for projeto in lista_projetos:
        url_times.append(
            f'{URL_BASE}_apis/projects/{projeto}/teams?api-version=7.0'
        )

    for url_time in url_times:
        response = requests.get(url_time, auth=HTTPBasicAuth('', PAT))
        if response.status_code == 200:
            times = response.json()['value']
            for time in times:
                lista_todos_times.append(time['name'])
    return lista_todos_times


def mesclar_projeto_com_time(lista_projetos, lista_todos_times):
    lista_times_ativos = []
    projetos_times = []
    time_index = 0

    for time in lista_todos_times:
        if not any(palavra in time for palavra in lista_times_ignorados):
            lista_times_ativos.append(time)

    for projeto in lista_projetos:
        if time_index >= len(lista_times_ativos):
            break
        projetos_times.append((projeto, lista_times_ativos[time_index]))
        time_index += 1

        if (
            projeto.startswith('CODAE') or projeto.startswith('COPED')
        ) and time_index < len(lista_times_ativos):
            projetos_times.append((projeto, lista_times_ativos[time_index]))
            time_index += 1
    return projetos_times


def busca_sprint(projetos_times, mes_alvo=None, ano_alvo=None):
    from datetime import datetime

    mes_atual = mes_alvo or datetime.now().month
    ano_atual = ano_alvo or datetime.now().year
    sprints_mes = []

    for projeto, time in projetos_times:
        url = f'{URL_BASE}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations?api-version=7.0'
        response = requests.get(url, auth=HTTPBasicAuth('', PAT))
        if response.status_code != 200:
            continue

        sprints = response.json()['value']
        for sprint in sprints:
            start_raw = sprint['attributes'].get('startDate')
            finish_raw = sprint['attributes'].get('finishDate')

            if not start_raw or not finish_raw:
                continue

            inicio = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))

            if inicio.month == mes_atual and inicio.year == ano_atual:
                sprints_mes.append((projeto, time, sprint['id']))

    return sprints_mes


def busca_sprints(projetos_times, mes_alvo=None, ano_alvo=None):
    from datetime import datetime

    mes_inicial = mes_alvo or datetime.now().month
    ano_inicial = ano_alvo or datetime.now().year
    sprints_meses = []

    for projeto, time in projetos_times:
        url = f'{URL_BASE}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations?api-version=7.0'
        response = requests.get(url, auth=HTTPBasicAuth('', PAT))
        if response.status_code != 200:
            continue

        sprints = response.json()['value']
        for sprint in sprints:
            start_raw = sprint['attributes'].get('startDate')
            finish_raw = sprint['attributes'].get('finishDate')

            if not start_raw or not finish_raw:
                continue

            inicio = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))

            if inicio.month >= mes_inicial and inicio.year >= ano_inicial:
                sprints_meses.append((projeto, time, sprint['id']))

    return sprints_meses


def busca_id_work_items(projeto, time, sprint_id):
    url = f'{URL_BASE}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations/{sprint_id}/workitems?api-version=7.0'
    response = requests.get(url, auth=HTTPBasicAuth('', PAT))
    if response.status_code != 200:
        return []

    items_data = response.json().get('workItemRelations', [])
    return [
        str(item['target']['id']) for item in items_data if 'target' in item
    ]


def busca_horas_work_items(projeto, ids):
    horas_por_pessoa = {}
    if not ids:
        return horas_por_pessoa

    def chunk_lista(lista, tamanho):
        for i in range(0, len(lista), tamanho):
            yield lista[i : i + tamanho]

    for chunk in chunk_lista(ids, 200):
        ids_str = ','.join(chunk)
        url = (
            f'{URL_BASE}{quote(projeto)}/_apis/wit/workitems'
            f'?ids={ids_str}&fields=System.Title,System.AssignedTo,Microsoft.VSTS.Scheduling.CompletedWork&api-version=7.0'
        )
        response = requests.get(url, auth=HTTPBasicAuth('', PAT))
        if response.status_code != 200:
            continue

        for work_item in response.json().get('value', []):
            assigned_to = (
                work_item['fields']
                .get('System.AssignedTo', {})
                .get('displayName', 'Sem responsável')
            )
            horas = work_item['fields'].get(
                'Microsoft.VSTS.Scheduling.CompletedWork', 0
            )
            horas_por_pessoa[assigned_to] = (
                horas_por_pessoa.get(assigned_to, 0) + horas
            )

    return horas_por_pessoa


def busca_campos_work_items(projeto, ids):
    wi = []
    if ids:
        for i in range(0, len(ids), 200):
            ids_str = ','.join(ids[i : i + 200])
            url = (
                f'{URL_BASE}{quote(projeto)}/_apis/wit/workitems'
                f'?ids={ids_str}&fields=System.Id,System.Title,System.AssignedTo,System.State,System.Description,Microsoft.VSTS.TCM.ReproSteps,Microsoft.VSTS.Common.AcceptanceCriteria,System.WorkItemType&api-version=7.0'
            )
            r = requests.get(url, auth=HTTPBasicAuth('', PAT))
            if r.status_code == 200:
                wi.extend(r.json().get('value', []))

    return wi


def busca_done_work_items(projeto, ids):
    wi = []
    if ids:
        for i in range(0, len(ids), 200):
            ids_str = ','.join(ids[i : i + 200])
            url = (
                f'{URL_BASE}{quote(projeto)}/_apis/wit/workitems'
                f'?ids={ids_str}&fields=System.Id,System.Title,System.AssignedTo,System.State,Microsoft.VSTS.Common.ClosedBy,System.WorkItemType&api-version=7.0'
            )
            r = requests.get(url, auth=HTTPBasicAuth('', PAT))
            if r.status_code == 200:
                wi.extend(r.json().get('value', []))

    return wi
