import re
from datetime import datetime
from babel.dates import format_date
from api import azure
from utils.datas import calcular_horas_uteis
import os

TEMPLATE_PADRAO_TASK = os.getenv('TEMPLATE_PADRAO_TASK')
TEMPLATE_PADRAO_BUG = os.getenv('TEMPLATE_PADRAO_BUG')
TEMPLATE_PADRAO_PBI = os.getenv('TEMPLATE_PADRAO_PBI')


def gera_relatorio_descricao(tipo_solicitado=None, mes=None, ano=None):

    if tipo_solicitado.title() == 'História' or tipo_solicitado.title() == 'Historia':
        tipo_solicitado = 'Product Backlog Item'
        template_padrao = TEMPLATE_PADRAO_PBI
    elif tipo_solicitado.title() == 'Bug':
        tipo_solicitado = tipo_solicitado.title()
        template_padrao = TEMPLATE_PADRAO_BUG
    elif tipo_solicitado.title() == 'Task':
        tipo_solicitado = tipo_solicitado.title()
        template_padrao = TEMPLATE_PADRAO_TASK
    else:
        return f'❌ Tipo de work item "{tipo_solicitado}" inválido.'

    lista_projetos = azure.puxar_projetos()
    lista_todos_times = azure.puxar_times(lista_projetos)
    projetos_times = azure.mesclar_projeto_com_time(
        lista_projetos, lista_todos_times
    )

    work_items_por_pessoa = {}
    ids_por_pessoa = {}

    sprints = azure.busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:
        ids = azure.busca_id_work_items(projeto, time, sprint_id)
        wi = azure.busca_campos_work_items(projeto, ids)

        for work_item in wi:
            fields = work_item.get('fields', {})
            tipo = fields.get('System.WorkItemType', '')

            if tipo == 'Task' and tipo_solicitado == 'Task':
                description = fields.get('System.Description', '')
            elif tipo == 'Bug' and tipo_solicitado == 'Bug':
                description = fields.get('Microsoft.VSTS.TCM.ReproSteps', '')
            elif tipo == 'Product Backlog Item' and tipo_solicitado == 'Product Backlog Item':
                description = fields.get('System.Description', '')
            else:
                continue

            assigned_to = fields.get('System.AssignedTo', {}).get(
                'displayName', 'Sem responsável'
            )
            wid = str(work_item['id'])
            title = fields.get('System.Title', '(sem título)')
            state = fields.get('System.State')

            desc_limpa = re.sub(
                rf'{template_padrao[:20]}.+{template_padrao[-15:]}\s*',
                '',
                description,
            )

            if (
                tipo == tipo_solicitado
                and state == 'Done'
                and (desc_limpa == '' or desc_limpa == template_padrao)
            ):
                work_items_por_pessoa[assigned_to] = (
                    work_items_por_pessoa.get(assigned_to, 0) + 1
                )
                ids_por_pessoa.setdefault(assigned_to, []).append(
                    f'#{wid} - {title}'
                )

    data = datetime(ano or datetime.now().year, mes or datetime.now().month, 1)
    mes_nome = format_date(data, 'LLLL/yyyy', locale='pt_BR')

    if not work_items_por_pessoa:
        return f'✅ Nenhum(a) {tipo_solicitado} sem descrição encontrada em {mes_nome}.'

    texto = f'⚠️ {tipo_solicitado}(s) sem descrição em {mes_nome}:\n\n'
    for pessoa, qtd in sorted(
        work_items_por_pessoa.items(), key=lambda x: x[1], reverse=True
    ):
        texto += f'👤 {pessoa}: {qtd} {tipo_solicitado}(s)\n'
        texto += '\n'.join(ids_por_pessoa[pessoa]) + '\n\n'

    return texto


def gera_relatorio_horas(mes=None, ano=None):
    lista_projetos = azure.puxar_projetos()
    lista_todos_times = azure.puxar_times(lista_projetos)
    projetos_times = azure.mesclar_projeto_com_time(
        lista_projetos, lista_todos_times
    )

    total_por_pessoa = {}
    sprints = azure.busca_sprint(projetos_times, mes_alvo=mes, ano_alvo=ano)

    for projeto, time, sprint_id in sprints:
        ids = azure.busca_id_work_items(projeto, time, sprint_id)
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
