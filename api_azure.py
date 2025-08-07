from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

ORGANIZATION = os.getenv('ORGANIZATION')
PAT = os.getenv('PAT')
URL_PROJETOS = os.getenv('URL_PROJETOS')

response = requests.get(URL_PROJETOS, auth=HTTPBasicAuth('', PAT))

if response.status_code == 200:
    projetos = response.json()['value']
    for projeto in projetos:
        print(projeto['name'])
else:
    print('Não foi possível se conectar ao Azure DevOps')