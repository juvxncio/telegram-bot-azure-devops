import re
from datetime import datetime
from babel.dates import format_date
from api import azure
from utils.datas import calcular_horas_uteis
import os

TEMPLATE_PADRAO = os.getenv('TEMPLATE_PADRAO')


def gera_relatorio_tarefas(mes=None, ano=None):
    lista_projetos = azure.puxar_projetos()
    lista_todos_times = azure.puxar_times(lista_projetos)
    projetos_times = azure.mesclar_projeto_com_time(lista_projetos, lista_todos_times)

    tarefas_por_pessoa = {}
    ids_por_pessoa = {}

    sprints = azure.busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:
        ids = azure.busca_work_items(projeto, time, sprint_id)
        tarefas = azure.busca_tasks(projeto, ids)

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
    lista_projetos = azure.puxar_projetos()
    lista_todos_times = azure.puxar_times(lista_projetos)
    projetos_times = azure.mesclar_projeto_com_time(lista_projetos, lista_todos_times)

    total_por_pessoa = {}
    sprints = azure.busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:
        ids = azure.busca_work_items(projeto, time, sprint_id)
        horas = azure.busca_horas_work_items(projeto, ids)

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
