from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from urllib.parse import quote

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
    else:
        print(
            'Não foi possível se conectar ao Azure DevOps',
            response.status_code,
        )
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
        else:
            print(
                'Não foi possível se conectar ao Azure DevOps',
                response.status_code,
            )
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


def busca_sprint(projetos_times):
    mes_atual = datetime.now().month - 1
    ano_atual = datetime.now().year
    sprints_mes = []

    for projeto, time in projetos_times:
        url = f'{URL_BASE}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations?api-version=7.0'
        response = requests.get(url, auth=HTTPBasicAuth('', PAT))

        if response.status_code != 200:
            print(
                f'Erro ao buscar sprints para {projeto}/{time}: {response.status_code}'
            )
            continue

        sprints = response.json()['value']
        for sprint in sprints:
            start_raw = sprint['attributes'].get('startDate')
            finish_raw = sprint['attributes'].get('finishDate')

            if not start_raw or not finish_raw:
                continue

            inicio = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            fim = datetime.fromisoformat(finish_raw.replace('Z', '+00:00'))

            if inicio.month == mes_atual and inicio.year == ano_atual:
                # print(
                #     f"Sprint atual: {sprint['name']} Id: {sprint['id']} ({inicio.date()} → {fim.date()})"
                # )
                sprints_mes.append((projeto, time, sprint['id']))
    for i in sprints_mes:
        print(i)
    return sprints_mes


def busca_work_items(projeto, time, sprint_id):
    url = f'{URL_BASE}{quote(projeto)}/{quote(time)}/_apis/work/teamsettings/iterations/{sprint_id}/workitems?api-version=7.0'
    response = requests.get(url, auth=HTTPBasicAuth('', PAT))
    if response.status_code != 200:
        return []

    items_data = response.json().get('workItemRelations', [])
    return [
        str(item['target']['id']) for item in items_data if 'target' in item
    ]


def busca_detalhes_work_items(projeto, ids):
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


def gera_relatorio():
    lista_projetos = puxar_projetos()
    lista_todos_times = puxar_times(lista_projetos)
    projetos_times = mesclar_projeto_com_time(
        lista_projetos, lista_todos_times
    )

    total_por_pessoa = {}
    sprints = busca_sprint(projetos_times)

    for projeto, time, sprint_id in sprints:
        ids = busca_work_items(projeto, time, sprint_id)
        horas = busca_detalhes_work_items(projeto, ids)

        for pessoa, total in horas.items():
            total_por_pessoa[pessoa] = total_por_pessoa.get(pessoa, 0) + total

    print('\n📊 Horas por profissional no mês atual:')
    for pessoa, horas in sorted(
        total_por_pessoa.items(), key=lambda x: x[0].lower()
    ):
        print(f'{pessoa}: {horas}h')


def main():
    return gera_relatorio()


if __name__ == '__main__':
    print(main())
