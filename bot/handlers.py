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


async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Seu ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}'
    )
