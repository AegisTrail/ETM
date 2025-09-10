# - This code is intended for local testing only. Do NOT use real mnemonics/private keys on mainnet.

import logging
from web3 import Web3
from telegram.ext import ApplicationBuilder, ConversationHandler, MessageHandler, filters
from telegram.ext import CommandHandler


from bot.config import config
from bot.storage import JSONStorage
from bot.wallet import WalletManager
from bot.handlers import Handlers, SEND_TO, SEND_AMOUNT, TSYMBOL, TTO, TAMOUNT, SIGN_MSG, VERIFY_AWAIT

logging.basicConfig(level=logging.WARNING)


def main():
    w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    if not w3.is_connected():
        raise SystemExit(f"Cannot connect to RPC at {config.RPC_URL}. Is Anvil running??")

    storage = JSONStorage()
    wallet = WalletManager(w3, config.WALLET_MNEMONIC, config.CHAIN_ID, gas_price_gwei=config.GAS_PRICE_GWEI, faucet_pk=config.FAUCET_PRIVATE_KEY)
    handlers = Handlers(wallet, storage)

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help))
    app.add_handler(CommandHandler("new", handlers.new_wallet))
    app.add_handler(CommandHandler("address", handlers.address))
    app.add_handler(CommandHandler("balance", handlers.balance))
    app.add_handler(CommandHandler("faucet", handlers.faucet))
    app.add_handler(CommandHandler("history", handlers.history))
    app.add_handler(CommandHandler("token_add", handlers.token_add))
    app.add_handler(CommandHandler("token_balance", handlers.token_balance))

    send_conv = ConversationHandler(
        entry_points=[CommandHandler("send", handlers.send_start)],
        states={
            SEND_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.send_got_to)],
            SEND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.send_got_amount)],
        },
        fallbacks=[CommandHandler("cancel", handlers.send_cancel)],
    )
    app.add_handler(send_conv)

    token_conv = ConversationHandler(
        entry_points=[CommandHandler("token_send", handlers.token_send_start)],
        states={
            TSYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.token_send_symbol)],
            TTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.token_send_to)],
            TAMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.token_send_amount)],
        },
        fallbacks=[CommandHandler("cancel", handlers.send_cancel)],
    )
    app.add_handler(token_conv)

    sign_conv = ConversationHandler(
        entry_points=[CommandHandler("sign", handlers.sign_start)],
        states={SIGN_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.sign_finish)]},
        fallbacks=[],
    )
    app.add_handler(sign_conv)

    verify_conv = ConversationHandler(
        entry_points=[CommandHandler("verify", handlers.verify_start)],
        states={VERIFY_AWAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.verify_finish)]},
        fallbacks=[],
    )
    app.add_handler(verify_conv)

    print("Bot is running (polling). Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
