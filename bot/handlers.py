import os
from datetime import datetime
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
from api import relatorios
from api.relatorios import gera_relatorio_horas, gera_relatorio_descricao

load_dotenv()
GRUPO_PERMITIDO = int(os.getenv('GRUPO_PERMITIDO'))


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 2:
            mes = int(context.args[0])
            ano = int(context.args[1])
        elif len(context.args) == 1:
            mes = int(context.args[0])
            ano = datetime.now().year
        else:
            hoje = datetime.now()
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1

        relatorio = relatorios.gera_relatorio_horas(mes=mes, ano=ano)

        if len(relatorio) > 4000:
            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f'relatorio_horas_{mes}_{ano}.txt'
            await update.message.reply_document(document=bio)
        else:
            await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(f'❌ Erro ao gerar relatório: {str(e)}')


async def descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 3:
            tipo = context.args[0]
            mes = int(context.args[1])
            ano = int(context.args[2])
        elif len(context.args) == 2:
            tipo = context.args[0]
            mes = int(context.args[1])
            ano = datetime.now().year
        elif len(context.args) == 1:
            tipo = context.args[0]
            hoje = datetime.now()
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1
        else:
            await update.message.reply_text(
                '❌ Informar o tipo de Work Item (Task, História ou Bug)'
            )

        relatorio = relatorios.gera_relatorio_descricao(
            tipo_solicitado=tipo, mes=mes, ano=ano
        )

        if len(relatorio) > 4000:
            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f'relatorio_descricao_{tipo}_{mes}_{ano}.txt'
            await update.message.reply_document(document=bio)
        else:
            await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(
            f'❌ Erro ao gerar relatório de tarefas: {str(e)}'
        )


async def completo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 2:
            mes = int(context.args[0])
            ano = int(context.args[1])
        elif len(context.args) == 1:
            mes = int(context.args[0])
            ano = datetime.now().year
        else:
            hoje = datetime.now()
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1

        relatorio = ''
        relatorio += relatorios.gera_relatorio_descricao(
            tipo_solicitado='História', mes=mes, ano=ano
        )
        relatorio += '\n\n'
        relatorio += relatorios.gera_relatorio_descricao(
            tipo_solicitado='Bug', mes=mes, ano=ano
        )
        relatorio += '\n\n'
        relatorio += relatorios.gera_relatorio_descricao(
            tipo_solicitado='Task', mes=mes, ano=ano
        )
        relatorio += '\n\n'
        relatorio += relatorios.gera_relatorio_horas(mes=mes, ano=ano)

        if len(relatorio) > 4000:
            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f'relatorio_completo_{mes}_{ano}.txt'
            await update.message.reply_document(document=bio)
        else:
            await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(
            f'❌ Erro ao gerar relatório completo: {str(e)}'
        )


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 2:
            mes = int(context.args[0])
            ano = int(context.args[1])
        elif len(context.args) == 1:
            mes = int(context.args[0])
            ano = datetime.now().year
        else:
            hoje = datetime.now()
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1

        relatorio = relatorios.gera_relatorio_done(mes=mes, ano=ano)

        if len(relatorio) > 4000:
            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f'relatorio_horas_{mes}_{ano}.txt'
            await update.message.reply_document(document=bio)
        else:
            await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(f'❌ Erro ao gerar relatório: {str(e)}')


async def transbordo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 2:
            mes = int(context.args[0])
            ano = int(context.args[1])
        else:
            await update.message.reply_text(
                '❌ Informar o mês e ano de início.'
            )

        relatorio = relatorios.gera_relatorio_transbordo(mes_inicio=mes, ano_inicio=ano)

        if len(relatorio) > 4000:
            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f'relatorio_transbordo_{mes}_{ano}.txt'
            await update.message.reply_document(document=bio)
        else:
            await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(f'❌ Erro ao gerar relatório: {str(e)}')


async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Seu ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}'
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """<b>Comandos:</b>
⌚ <code>/horas [mês] [ano]</code> → Relatório de horas trabalhadas por pessoa no período.
✍️📖 <code>/descricao task [mês] [ano]</code> → Relatório de tarefas concluídas no período sem descrição/com descrição padrão.
✍️🐞 <code>/descricao bug [mês] [ano]</code> → Relatório de bugs concluídos no período sem descrição/com descrição padrão.
✍️📔 <code>/descricao historia [mês] [ano]</code> → Relatório de histórias concluídas no período sem descrição ou critérios de aceite/com descrição ou critérios de aceite padrão.
✅ <code>/done [mês] [ano]</code> → Relatório de histórias cujo status Done tenha sido feito por alguém não autorizado.
🌊 <code>/transbordo [mês] [ano]</code> → Relatório de histórias que foram movidas de sprint.
📚 <code>/completo [mês] [ano]</code> → Junção dos comandos anteriores em um só relatório.
ℹ️ <code>/id</code> → Mostra o seu ID de usuário e o Chat ID (útil para configurar permissões).\n
‼️ <u>Relatórios grandes são enviados automaticamente como arquivo .txt</u> ‼️
""",
        parse_mode="HTML"
    )
