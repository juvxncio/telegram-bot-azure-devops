import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from bot import handlers

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('horas', handlers.horas))
    application.add_handler(CommandHandler('descricao', handlers.descricao))
    application.add_handler(CommandHandler('completo', handlers.completo))
    application.add_handler(CommandHandler('done', handlers.done))
    application.add_handler(CommandHandler('transbordo', handlers.transbordo))
    application.add_handler(CommandHandler('id', handlers.id))
    print('Bot iniciado. Aguardando comandos...')
    application.run_polling()


if __name__ == '__main__':
    main()
