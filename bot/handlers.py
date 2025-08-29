import os
from datetime import datetime
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from api import relatorios
from api.relatorios import (
    gera_relatorio_horas,
    gera_relatorio_descricao,
    gera_relatorio_done,
)
import re
import datetime

load_dotenv()
GRUPO_PERMITIDO = int(os.getenv('GRUPO_PERMITIDO'))

COMMANDS = {
    '/horas': '⌚️ Relatório de horas trabalhadas',
    '/descricao task': '✍️📖 Tarefas sem descrição',
    '/descricao bug': '✍️🐞 Bugs sem descrição',
    '/descricao historia': '✍️📔 Histórias sem descrição',
    '/done': '✅ Histórias com Done dado por não autorizados',
    '/completo': '📚 Relatório completo',
    '/transbordo': '🌊 Histórias movidas de sprint',
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f'{desc}', callback_data=f'cmd:{cmd}')]
        for cmd, desc in COMMANDS.items()
    ]
    keyboard.append(
        [InlineKeyboardButton('❌ Cancelar', callback_data='cancel')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '📌 Escolha um relatório:', reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'cancel':
        try:
            await query.message.delete()
        except:
            await query.edit_message_text('❌ Operação cancelada.')
        return

    if data.startswith('cmd:'):
        cmd = data.split(':', 1)[1]
        keyboard = [
            [InlineKeyboardButton(str(m), callback_data=f'mes:{cmd}:{m}')]
            for m in range(1, 13)
        ]
        keyboard.append(
            [InlineKeyboardButton('❌ Cancelar', callback_data='cancel')]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f'📌 Você escolheu {cmd}. Agora selecione o mês:',
            reply_markup=reply_markup,
        )

    elif data.startswith('mes:'):
        _, cmd, mes = data.split(':')
        mes = int(mes)
        ano_atual = datetime.datetime.now().year
        anos = list(range(2024, ano_atual + 1))

        keyboard = [
            [
                InlineKeyboardButton(
                    str(a), callback_data=f'ano:{cmd}:{mes}:{a}'
                )
            ]
            for a in anos
        ]
        keyboard.append(
            [InlineKeyboardButton('❌ Cancelar', callback_data='cancel')]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f'📌 Você escolheu {cmd} mês {mes}. Agora selecione o ano:',
            reply_markup=reply_markup,
        )

    elif data.startswith('ano:'):
        _, cmd, mes, ano = data.split(':')
        mes, ano = int(mes), int(ano)

        await query.edit_message_text('⏳ Gerando relatório, aguarde...')

        # Gera o relatório
        if cmd == '/horas':
            relatorio = relatorios.gera_relatorio_horas(mes=mes, ano=ano)
        elif cmd.startswith('/descricao'):
            tipo = cmd.split()[1]
            relatorio = relatorios.gera_relatorio_descricao(
                tipo_solicitado=tipo, mes=mes, ano=ano
            )
        elif cmd == '/done':
            relatorio = relatorios.gera_relatorio_done(mes=mes, ano=ano)
        elif cmd == '/completo':
            relatorio = (
                relatorios.gera_relatorio_descricao(
                    tipo_solicitado='História', mes=mes, ano=ano
                )
                + '\n\n'
                + relatorios.gera_relatorio_descricao(
                    tipo_solicitado='Bug', mes=mes, ano=ano
                )
                + '\n\n'
                + relatorios.gera_relatorio_descricao(
                    tipo_solicitado='Task', mes=mes, ano=ano
                )
                + '\n\n'
                + relatorios.gera_relatorio_done(mes=mes, ano=ano)
                + '\n\n'
                + relatorios.gera_relatorio_horas(mes=mes, ano=ano)
            )
        elif cmd == '/transbordo':
            relatorio = relatorios.gera_relatorio_transbordo(
                mes_inicio=mes, ano_inicio=ano
            )
        else:
            relatorio = '❌ Comando não reconhecido.'

        if len(relatorio) > 4000:
            from io import BytesIO

            bio = BytesIO(relatorio.encode('utf-8'))
            bio.name = f"relatorio_{cmd.strip('/')}_{mes}_{ano}.txt"
            await query.message.reply_document(document=bio)
        else:
            await query.message.reply_text(relatorio)


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
        relatorio += relatorios.gera_relatorio_done(mes=mes, ano=ano)
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

        relatorio = relatorios.gera_relatorio_transbordo(
            mes_inicio=mes, ano_inicio=ano
        )

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


def extrair_comandos_readme() -> str:
    with open('README.md', 'r', encoding='utf-8') as f:
        conteudo = f.read()

    match = re.search(r'## 🚀 Funcionalidades(.*?)---', conteudo, re.S)
    if not match:
        return 'Erro ao carregar comandos.'

    texto = match.group(1).strip()

    texto = texto.replace('**', '<b>').replace('**', '</b>', 1)
    texto = re.sub(r'`(/.*?)`', r'<code>\1</code>', texto)
    return f'<b>Comandos:</b>\n{texto}'


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = extrair_comandos_readme()
    await update.message.reply_text(comandos, parse_mode='HTML')
