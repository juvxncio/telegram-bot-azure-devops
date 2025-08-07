from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

# from lista_url_times import lista_url_times

load_dotenv()

ORGANIZATION = os.getenv('ORGANIZATION')
PAT = os.getenv('PAT')
URL_BASE = os.getenv('URL_BASE')
URL_PROJETOS = f'{URL_BASE}projects?api-version=7.0'
URLS_TIMES = '{URL_BASE}projects/{project}/teams?api-version=7.0'

response = requests.get(URL_PROJETOS, auth=HTTPBasicAuth('', PAT))

lista_projetos = []

if response.status_code == 200:
    projetos = response.json()['value']
    for projeto in projetos:
        if not ('SUSPENSO' in projeto['name'].upper()):
            lista_projetos.append(projeto['name'])
else:
    print('Não foi possível se conectar ao Azure DevOps')

for projeto in lista_projetos:
    print(projeto + '\n')