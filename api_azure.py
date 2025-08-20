import os
import re
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from urllib.parse import quote
from babel.dates import format_date
import calendar
import holidays
from dotenv import load_dotenv

load_dotenv()

PAT = os.getenv('PAT')
URL_BASE = os.getenv('URL_BASE')
URL_PROJETOS = f'{URL_BASE}_apis/projects?api-version=7.0'

TEMPLATE_PADRAO = os.getenv('TEMPLATE_PADRAO')

lista_times_ignorados_str = os.getenv('lista_times_ignorados')
lista_times_ignorados = (
    lista_times_ignorados_str.split(',') if lista_times_ignorados_str else []
)


def calcular_horas_uteis(mes, ano):
    feriados = holidays.Brazil(years=ano, prov='SP')

    primeiro = datetime(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    ultimo = datetime(ano, mes, ultimo_dia)

    horas = 0
    dia = primeiro

    while dia <= ultimo:
        if dia.weekday() < 5 and dia not in feriados:
            if (
                dia.weekday() == 2
                and (dia - timedelta(days=1)) in feriados
                and 'Carnaval' in feriados.get(dia - timedelta(days=1), '')
            ):
                horas += 4
            else:
                horas += 8
        dia += timedelta(days=1)

    return horas


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


def busca_work_items(projeto, time, sprint_id):
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


def busca_tasks(projeto, ids):
    tarefas = []
    if ids:
        for i in range(0, len(ids), 200):
            ids_str = ','.join(ids[i : i + 200])
            url = (
                f'{URL_BASE}{quote(projeto)}/_apis/wit/workitems'
                f'?ids={ids_str}&fields=System.Id,System.Title,System.AssignedTo,System.State,System.Description,System.WorkItemType&api-version=7.0'
            )
            r = requests.get(url, auth=HTTPBasicAuth('', PAT))
            if r.status_code == 200:
                tarefas.extend(r.json().get('value', []))

    return tarefas


def gera_relatorio_tarefas(mes=None, ano=None):
    lista_projetos = puxar_projetos()
    lista_todos_times = puxar_times(lista_projetos)
    projetos_times = mesclar_projeto_com_time(
        lista_projetos, lista_todos_times
    )

    tarefas_por_pessoa = {}
    ids_por_pessoa = {}

    sprints = busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:

        ids = busca_work_items(projeto, time, sprint_id)
        tarefas = busca_tasks(projeto, ids)

        for work_item in tarefas:
            fields = work_item.get('fields', {})
            description = fields.get('System.Description', '')
            assigned_to = fields.get('System.AssignedTo', {}).get(
                'displayName', 'Sem responsável'
            )
            tipo = fields.get('System.WorkItemType')
            wid = str(work_item['id'])
            title = fields.get('System.Title', '(sem título)')
            state = fields.get('System.State')

            desc_limpa = re.sub(
                r'Objetivo: Explicação clara da atividade .+ para conclusão\.',
                '',
                description,
            )

            # Agora só conta se a descrição for exatamente vazia ou exatamente igual ao template
            if (
                tipo == 'Task'
                and state == 'Done'
                and (desc_limpa == '' or desc_limpa == TEMPLATE_PADRAO)
            ):
                tarefas_por_pessoa[assigned_to] = (
                    tarefas_por_pessoa.get(assigned_to, 0) + 1
                )
                ids_por_pessoa.setdefault(assigned_to, []).append(
                    f'#{wid} - {title}'
                )

    data = datetime(ano or datetime.now().year, mes or datetime.now().month, 1)
    mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

    if not tarefas_por_pessoa:
        return f'✅ Nenhuma task sem descrição encontrada em {mes_nome}.'

    texto = f'⚠️ Tasks finalizadas sem descrição em {mes_nome}:\n\n'
    for pessoa, qtd in sorted(
        tarefas_por_pessoa.items(), key=lambda x: x[1], reverse=True
    ):
        texto += f'👤 {pessoa}: {qtd} tasks\n'
        texto += '\n'.join(ids_por_pessoa[pessoa]) + '\n\n'

    return texto


def gera_relatorio(mes=None, ano=None):
    lista_projetos = puxar_projetos()
    lista_todos_times = puxar_times(lista_projetos)
    projetos_times = mesclar_projeto_com_time(
        lista_projetos, lista_todos_times
    )

    total_por_pessoa = {}
    sprints = busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:
        ids = busca_work_items(projeto, time, sprint_id)
        horas = busca_horas_work_items(projeto, ids)

        for pessoa, total in horas.items():
            total_por_pessoa[pessoa] = total_por_pessoa.get(pessoa, 0) + total

    data = datetime(ano or datetime.now().year, mes or datetime.now().month, 1)
    mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

    horas_uteis = calcular_horas_uteis(data.month, data.year)

    if not total_por_pessoa:
        return f'Nenhuma hora registrada em {mes_nome}.'

    texto = f'📊 Horas por profissional em {mes_nome}:\n\n'
    for pessoa, horas in sorted(
        total_por_pessoa.items(), key=lambda x: x[0].lower()
    ):
        horas = round(horas, 2)
        faltam = round(horas_uteis - horas, 2)
        if faltam > 0:
            dias = round(faltam / 8, 1)
            texto += f'{pessoa}: {horas}h (faltam {faltam}h ≈ {dias} dias)\n\n'
        elif faltam < 0:
            excedente = abs(faltam)
            dias_extra = round(excedente / 8, 1)
            texto += f'{pessoa}: {horas}h (+{excedente}h a mais ≈ {dias_extra} dias)\n\n'
        else:
            texto += f'{pessoa}: {horas}h (exatamente as horas previstas)\n\n'

    texto += f'ℹ️ Horas úteis do mês: {horas_uteis}h\n'
    return texto


def main(modo='horas', mes=None, ano=None):
    if modo == 'tarefas':
        return gera_relatorio_tarefas(mes, ano)
    return gera_relatorio(mes, ano)


if __name__ == '__main__':
    print(main())
