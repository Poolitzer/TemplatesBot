from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Filters, ConversationHandler, MessageHandler
import handlers
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename="log.log")

(SECOND, MORE, CUSTOM_START, CUSTOM_CHOOSE, CUSTOM_RECEIVE, CUSTOM_ERROR, UPDATE_DETERMINE, UPDATE_RECEIVE) = range(8)


def main():
    updater = Updater(token='TOKEN', use_context=True)
    dp = updater.dispatcher
    start_handler = CommandHandler('start', handlers.start)
    dp.add_handler(start_handler)
    start_inline_handler = CallbackQueryHandler(handlers.start_inline, pattern="start")
    dp.add_handler(start_inline_handler)
    add_inline_handler = CallbackQueryHandler(handlers.add_inline, pattern="add")
    dp.add_handler(add_inline_handler)
    setup = ConversationHandler(
        entry_points=[CommandHandler('setup', handlers.setup)],
        states={
            SECOND: [CallbackQueryHandler(handlers.second_inline, pattern="second")],
            MORE: [CallbackQueryHandler(handlers.more_inline, pattern="more"),
                   CallbackQueryHandler(handlers.finish_inline, pattern="finish")]
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel_setup)]
    )
    dp.add_handler(setup)
    create_handler = CallbackQueryHandler(handlers.create, pattern="create")
    dp.add_handler(create_handler)
    custom = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.custom_start_inline, pattern="custom"),
                      CommandHandler('custom', handlers.custom_start_command)],
        states={
            CUSTOM_CHOOSE: [CallbackQueryHandler(handlers.custom_append, pattern="custom_a"),
                            CallbackQueryHandler(handlers.custom_override, pattern="custom_o"),
                            CommandHandler('generate', handlers.custom_generate)],
            CUSTOM_RECEIVE: [MessageHandler(Filters.text, handlers.custom_receive)],
            CUSTOM_ERROR: [CallbackQueryHandler(handlers.custom_error_cancel, pattern="custom_cancel"),
                           CallbackQueryHandler(handlers.custom_error_proceed, pattern="custom_proceed"),
                           CallbackQueryHandler(handlers.custom_error_receive, pattern="custom_receive")],
        },
        fallbacks=[CommandHandler('cancel', handlers.custom_cancel)]
    )
    dp.add_handler(custom)
    generate_handler = CommandHandler('generate', handlers.generate_file)
    dp.add_handler(generate_handler)
    update_handler = MessageHandler(Filters.regex(r'en') & Filters.user(user_id=[79125365, 38482949]),
                                    handlers.update_start)
    dp.add_handler(update_handler)
    update = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.update_global, pattern="update_g"),
                      CallbackQueryHandler(handlers.update_typo, pattern="update_t")],
        states={
            UPDATE_RECEIVE: [MessageHandler(Filters.text, handlers.update_receive)]
        },
        fallbacks=[CommandHandler('cancel', handlers.update_cancel)], allow_reentry=True
    )
    dp.add_handler(update)
    deep_handler = MessageHandler(Filters.text & Filters.user(user_id=[79125365, 38482949]), handlers.deep)
    dp.add_handler(deep_handler)
    updater.start_polling()


if __name__ == '__main__':
    main()
