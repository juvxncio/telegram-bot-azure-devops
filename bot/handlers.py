import os
from io import BytesIO
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
from api.azure import AzureDevOpsAPI
from api.relatorios import Relatorios

load_dotenv()
GRUPO_PERMITIDO = int(os.getenv('GRUPO_PERMITIDO'))

api = AzureDevOpsAPI()
relatorios = Relatorios(api)

COMMANDS = {
    '/horas': '⌚️ Relatório de horas trabalhadas',
    '/descricao task': '✍️📖 Tarefas sem descrição',
    '/descricao bug': '✍️🐞 Bugs sem descrição',
    '/descricao historia': '✍️📔 Histórias sem descrição',
    '/done': '✅ Histórias com Done dado por não autorizados',
    '/completo': '📚 Relatório completo',
    '/transbordo': '🌊 Histórias movidas de sprint',
    '/help': '❓ Mostrar comandos',
}


def calcula_mes_ano_padrao(args):
    if len(args) >= 2:
        return int(args[0]), int(args[1])
    elif len(args) == 1:
        hoje = datetime.now()
        return int(args[0]), hoje.year
    else:
        hoje = datetime.now()
        mes = hoje.month - 1 or 12
        ano = hoje.year if hoje.month > 1 else hoje.year - 1
        return mes, ano


async def enviar_relatorio(message, texto, prefixo, mes, ano):
    if len(texto) > 4000:
        bio = BytesIO(texto.encode('utf-8'))
        bio.name = f'relatorio_{prefixo}_{mes}_{ano}.txt'
        await message.reply_document(document=bio)
    else:
        await message.reply_text(texto)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(desc, callback_data=f'cmd:{cmd}')]
        for cmd, desc in COMMANDS.items()
    ]
    keyboard.append(
        [InlineKeyboardButton('❌ Cancelar', callback_data='cancel')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '📌 Escolha um relatório:', reply_markup=reply_markup
    )


import re


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

    if data == 'voltar':
        keyboard = [
            [InlineKeyboardButton(desc, callback_data=f'cmd:{cmd}')]
            for cmd, desc in COMMANDS.items()
        ]
        keyboard.append(
            [InlineKeyboardButton('❌ Cancelar', callback_data='cancel')]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            '📌 Escolha um relatório:', reply_markup=reply_markup
        )
        return

    if data.startswith('cmd:'):
        cmd = data.split(':', 1)[1]
        if cmd == '/help':
            texto = extrair_comandos_readme()
            keyboard = [
                [InlineKeyboardButton('🔙 Voltar', callback_data='voltar')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                texto, parse_mode='HTML', reply_markup=reply_markup
            )
            return

        keyboard = [
            [InlineKeyboardButton(str(m), callback_data=f'mes:{cmd}:{m}')]
            for m in range(1, 13)
        ]
        keyboard.append(
            [
                InlineKeyboardButton('❌ Cancelar', callback_data='cancel'),
                InlineKeyboardButton('🔙 Voltar', callback_data='voltar'),
            ]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f'📌 Você escolheu {cmd}. Agora selecione o mês:',
            reply_markup=reply_markup,
        )
        return

    if data.startswith('mes:'):
        _, cmd, mes = data.split(':')
        mes = int(mes)
        ano_atual = datetime.now().year
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
            [
                InlineKeyboardButton('❌ Cancelar', callback_data='cancel'),
                InlineKeyboardButton('🔙 Voltar', callback_data='voltar'),
            ]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f'📌 Você escolheu {cmd} mês {mes}. Agora selecione o ano:',
            reply_markup=reply_markup,
        )
        return

    if data.startswith('ano:'):
        _, cmd, mes, ano = data.split(':')
        mes, ano = int(mes), int(ano)
        await query.edit_message_text('⏳ Gerando relatório, aguarde...')

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
                    'Historia', mes=mes, ano=ano
                )
                + '\n\n'
                + relatorios.gera_relatorio_descricao('Bug', mes=mes, ano=ano)
                + '\n\n'
                + relatorios.gera_relatorio_descricao('Task', mes=mes, ano=ano)
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

        await enviar_relatorio(
            query.message, relatorio, cmd.strip('/'), mes, ano
        )
        return


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return
    mes, ano = calcula_mes_ano_padrao(context.args)
    texto = relatorios.gera_relatorio_horas(mes=mes, ano=ano)
    await enviar_relatorio(update, texto, 'horas', mes, ano)


async def descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return
    if not context.args:
        await update.message.reply_text(
            '❌ Informar o tipo de Work Item (Task, Historia ou Bug)'
        )
        return
    tipo = context.args[0]
    mes, ano = calcula_mes_ano_padrao(context.args[1:])
    texto = relatorios.gera_relatorio_descricao(
        tipo_solicitado=tipo, mes=mes, ano=ano
    )
    await enviar_relatorio(update, texto, f'descricao_{tipo}', mes, ano)


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return
    mes, ano = calcula_mes_ano_padrao(context.args)
    texto = relatorios.gera_relatorio_done(mes=mes, ano=ano)
    await enviar_relatorio(update, texto, 'done', mes, ano)


async def completo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return
    mes, ano = calcula_mes_ano_padrao(context.args)
    texto = (
        relatorios.gera_relatorio_descricao('Historia', mes=mes, ano=ano)
        + '\n\n'
        + relatorios.gera_relatorio_descricao('Bug', mes=mes, ano=ano)
        + '\n\n'
        + relatorios.gera_relatorio_descricao('Task', mes=mes, ano=ano)
        + '\n\n'
        + relatorios.gera_relatorio_done(mes=mes, ano=ano)
        + '\n\n'
        + relatorios.gera_relatorio_horas(mes=mes, ano=ano)
    )
    await enviar_relatorio(update, texto, 'completo', mes, ano)


async def transbordo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return
    if len(context.args) < 2:
        await update.message.reply_text('❌ Informar o mês e ano de início.')
        return
    mes, ano = int(context.args[0]), int(context.args[1])
    texto = relatorios.gera_relatorio_transbordo(
        mes_inicio=mes, ano_inicio=ano
    )
    await enviar_relatorio(update, texto, 'transbordo', mes, ano)


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
    texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
    texto = re.sub(r'`(/.*?)`', r'<code>\1</code>', texto)
    return f'<b>Comandos:</b>\n{texto}'


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comandos = extrair_comandos_readme()
    await update.message.reply_text(comandos, parse_mode='HTML')
