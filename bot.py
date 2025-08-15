import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import api_azure

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


async def horas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    relatorio = api_azure.gera_relatorio()
    await update.message.reply_text(relatorio)


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler(['horas'], horas))

    print('Bot iniciado. Aguardando comandos...')
    app.run_polling()
