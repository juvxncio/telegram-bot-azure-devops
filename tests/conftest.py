import os

os.environ.setdefault('PAT', 'fake-pat')
os.environ.setdefault('URL_BASE', 'https://dev.azure.com/fake/')
os.environ.setdefault('lista_times_ignorados', '')
os.environ.setdefault('TELEGRAM_TOKEN', 'fake-token')
os.environ.setdefault('GRUPO_PERMITIDO', '12345')
os.environ.setdefault('TEMPLATE_PADRAO_TASK', 'Objetivo: Explicação clara da atividade a ser realizada.')
os.environ.setdefault('TEMPLATE_PADRAO_PBI', 'Como: tipo de usuário Quero: ação Para: benefício')
os.environ.setdefault('TEMPLATE_PADRAO_BUG', 'Qual é o problema? (O que está ocorrendo e qual deve ser o comportamento correto)')
os.environ.setdefault('TEMPLATE_PADRAO_CRITERIOS_DE_ACEITE', 'Deve permitir que o usuário...')
os.environ.setdefault('DOMINIO_AUTORIZADO_DONE', '@empresa.com')
