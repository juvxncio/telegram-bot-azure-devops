import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import api_azure
from datetime import datetime

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mes = None
        ano = None

        if len(context.args) >= 1:
            mes = int(context.args[0])
        else:
            mes = datetime.now().month

        if len(context.args) >= 2:
            ano = int(context.args[1])
        else:
            ano = datetime.now().year

        relatorio = api_azure.main(mes=mes, ano=ano)
        await update.message.reply_text(relatorio)

    except Exception as e:
        await update.message.reply_text(f'❌ Erro ao gerar relatório: {str(e)}')


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('horas', horas))
    print('Bot iniciado. Aguardando comandos...')
    application.run_polling()


if __name__ == '__main__':
    main()
