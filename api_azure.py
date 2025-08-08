from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

ORGANIZATION = os.getenv('ORGANIZATION')
PAT = os.getenv('PAT')
URL_BASE = os.getenv('URL_BASE')
URL_PROJETOS = f'{URL_BASE}projects?api-version=7.0'

url_times = []
lista_projetos = []
lista_times = []

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
        url_times.append(f'{URL_BASE}projects/{projeto}/teams?api-version=7.0')

    for url_time in url_times:
        response = requests.get(url_time, auth=HTTPBasicAuth('', PAT))

        if response.status_code == 200:
            times = response.json()['value']
            for time in times:
                lista_times.append(time['name'])
        else:
            print('Não foi possível se conectar ao Azure DevOps', response.status_code)

puxar_times()