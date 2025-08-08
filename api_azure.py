from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

ORGANIZATION = os.getenv('ORGANIZATION')
PAT = os.getenv('PAT')
URL_BASE = os.getenv('URL_BASE')
URL_PROJETOS = f'{URL_BASE}_apis/projects?api-version=7.0'

url_times = []
url_sprints = []
lista_projetos = []
lista_todos_times = []
lista_times_ignorados_str = os.getenv('lista_times_ignorados')
lista_times_ignorados = lista_times_ignorados_str.split(',')
lista_times_ativos = []
projetos_times = []
time_index = 0

def puxar_projetos():

    response = requests.get(URL_PROJETOS, auth=HTTPBasicAuth('', PAT))

    if response.status_code == 200:
        projetos = response.json()['value']
        for projeto in projetos:
            if not ('SUSPENSO' in projeto['name'].upper()):
                lista_projetos.append(projeto['name'])
    else:
        print('Não foi possível se conectar ao Azure DevOps', response.status_code)

puxar_projetos()

def puxar_times():

    for projeto in lista_projetos:
        url_times.append(f'{URL_BASE}_apis/projects/{projeto}/teams?api-version=7.0')

    for url_time in url_times:
        response = requests.get(url_time, auth=HTTPBasicAuth('', PAT))

        if response.status_code == 200:
            times = response.json()['value']
            for time in times:
                lista_todos_times.append(time['name'])
        else:
            print('Não foi possível se conectar ao Azure DevOps', response.status_code)

puxar_times()

mesclar_projeto_com_time()
    for time in lista_todos_times:
        if not any(palavra in time for palavra in lista_times_ignorados):
            lista_times_ativos.append(time)


    for projeto in lista_projetos:
        projetos_times.append((projeto, lista_times_ativos[time_index]))
        time_index += 1

        if (projeto.startswith('CODAE') or projeto.startswith('COPED')) and time_index < len(lista_times_ativos):
            projetos_times.append((projeto, lista_times_ativos[time_index]))
            time_index += 1

mesclar_projeto_com_time()
