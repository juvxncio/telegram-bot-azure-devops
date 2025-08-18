import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import api_azure
from datetime import datetime

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GRUPO_PERMITIDO = int(os.getenv('GRUPO_PERMITIDO'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GRUPO_PERMITIDO:
        await update.message.reply_text(
            '❌ Este comando só pode ser usado no grupo autorizado.'
        )
        return

    try:
        if len(context.args) >= 2:
            # /horas <mes> <ano>
            mes = int(context.args[0])
            ano = int(context.args[1])
        elif len(context.args) == 1:
            # /horas <mes> → usa o ano atual
            mes = int(context.args[0])
            ano = datetime.now().year
        else:
            # /horas sem parâmetros → mês anterior
            hoje = datetime.now()
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1

        relatorio = api_azure.main(mes=mes, ano=ano)
        await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(f'❌ Erro ao gerar relatório: {str(e)}')


async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Seu ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}'
    )


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('horas', horas))
    application.add_handler(CommandHandler('id', id))
    print('Bot iniciado. Aguardando comandos...')
    application.run_polling()


if __name__ == '__main__':
    main()
