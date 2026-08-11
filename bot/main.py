import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from bot import handlers

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Erro ao processar update: %s', update, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            '❌ Ocorreu um erro ao processar seu pedido. Tente novamente.'
        )


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler('start', handlers.start))
    application.add_handler(CommandHandler('help', handlers.ajuda))
    application.add_handler(CommandHandler('id', handlers.meu_id))
    application.add_handler(CommandHandler('horas', handlers.horas))
    application.add_handler(CommandHandler('descricao', handlers.descricao))
    application.add_handler(CommandHandler('completo', handlers.completo))
    application.add_handler(CommandHandler('done', handlers.done))
    application.add_handler(CommandHandler('transbordo', handlers.transbordo))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    logger.info('Bot iniciado. Aguardando comandos...')
    print('Bot iniciado. Aguardando comandos...')
    application.run_polling()


if __name__ == '__main__':
    main()
