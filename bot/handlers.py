from decimal import Decimal
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
from web3 import Web3

from .wallet import WalletManager
from .storage import JSONStorage
from .config import config

SEND_TO, SEND_AMOUNT = range(2)
TSYMBOL, TTO, TAMOUNT = range(3)
SIGN_MSG = 1
VERIFY_AWAIT = 1

class Handlers:
    def __init__(self, wallet: WalletManager, storage: JSONStorage):
        self.wallet = wallet
        self.storage = storage

    async def check_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if not config.WHITELIST:
            return True
        user = update.effective_user
        user_id = user.id if user else None
        if user_id not in config.WHITELIST:
            if update.effective_message:
                await update.effective_message.reply_text("⛔ You are not authorized to use this bot. Nice try tho!")
            return False
        return True

    def _get_derivation_index(self, user_id: int) -> int:
        users = self.storage.get_users()
        key = str(user_id)
        if key not in users:
            users[key] = len(users)
            self.storage.save_users(users)
        return int(users[key])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        await update.message.reply_text(self.help_text())

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        await update.message.reply_text(self.help_text())

    def help_text(self) -> str:
        return (
            "Welcome — Telegram Ethereum Wallet (dev chain)\n\n"
            "Commands:\n"
            "/start, /help - this message\n"
            "/new - register a derived wallet index\n"
            "/address - show your derived address\n"
            "/balance [address] - show ETH balance\n"
            "/send - send ETH (guided)\n"
            "/history [blocks] - scan recent blocks for txs\n"
            "/sign - sign a message\n"
            "/verify - verify a signed message (paste address, message, signature)\n"
            "/faucet [amount] - drip from faucet (dev only)\n"
            "/token_add <symbol> <address> [decimals]\n"
            "/token_balance <symbol>\n"
            "/token_send - guided token send\n"
        )

    async def new(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.new_wallet(update, context)

    async def new_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        await update.message.reply_text(f"Assigned HD index {idx}. Address: {acct.address}")

    def _derive_account_for_index(self, index: int):
        return WalletManager(self.wallet.w3, self.wallet.mnemonic, self.wallet.chain_id).derive_account(index)

    async def address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        await update.message.reply_text(f"Your address: {acct.address}")

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        args = context.args
        if args:
            addr = args[0]
        else:
            user = update.effective_user
            idx = self._get_derivation_index(user.id)
            acct = self._derive_account_for_index(idx)
            addr = acct.address
        try:
            checksum = Web3.to_checksum_address(addr)
        except Exception:
            await update.message.reply_text("❌ Invalid address")
            return
        bal = self.wallet.get_balance(checksum)
        await update.message.reply_text(f"Balance of {checksum}: {bal} ETH")

    async def send_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return ConversationHandler.END
        await update.message.reply_text("Enter destination address:")
        return SEND_TO

    async def send_got_to(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        addr = update.message.text.strip()
        try:
            addr = Web3.to_checksum_address(addr)
        except Exception:
            await update.message.reply_text("❌ Invalid address")
            return ConversationHandler.END
        context.user_data["send_to"] = addr
        await update.message.reply_text("Enter amount in ETH:")
        return SEND_AMOUNT

    async def send_got_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return ConversationHandler.END
        try:
            amount = Decimal(update.message.text.strip())
        except Exception:
            await update.message.reply_text("❌ Invalid amount")
            return ConversationHandler.END
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        to = context.user_data.get("send_to")
        value_wei = int((amount * Decimal(10**18)).to_integral_value())
        try:
            tx_hash = self.wallet.send_eth(acct, to, value_wei)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send: {e}")
            return ConversationHandler.END
        await update.message.reply_text(f"✅ Sent {amount} ETH to {to}. Tx: {tx_hash}")
        return ConversationHandler.END

    async def send_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Send cancelled.")
        return ConversationHandler.END

    async def faucet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        if not config.FAUCET_PRIVATE_KEY:
            await update.message.reply_text("Faucet not configured")
            return
        amount = Decimal(context.args[0]) if context.args else Decimal("0.1")
        amount_wei = int((amount * Decimal(10**18)).to_integral_value())
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        try:
            tx_hash = self.wallet.faucet(acct.address, amount_wei)
        except Exception as e:
            await update.message.reply_text(f"Faucet failed: {e}")
            return
        await update.message.reply_text(f"Dripped {amount} ETH to {acct.address}. Tx: {tx_hash}")

    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        blocks = int(context.args[0]) if context.args else 100
        latest = self.wallet.w3.eth.block_number
        start = max(0, latest - blocks + 1)
        hits = []
        await update.message.reply_text(f"Scanning {start}..{latest} for txs involving {acct.address} ...")
        for n in range(start, latest + 1):
            block = self.wallet.w3.eth.get_block(n, full_transactions=True)
            for tx in block.transactions:
                frm = tx.get("from", "")
                to = tx.get("to", "")
                if (frm and frm.lower() == acct.address.lower()) or (to and to.lower() == acct.address.lower()):
                    hits.append(tx.get("hash").hex())
            if len(hits) >= 20:
                break
        if not hits:
            await update.message.reply_text("(no recent transactions found)")
        else:
            await update.message.reply_text("\n".join(hits))

    async def sign_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return ConversationHandler.END
        await update.message.reply_text("Send the message to sign:")
        return SIGN_MSG

    async def sign_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        message = update.message.text
        from eth_account.messages import encode_defunct
        m = encode_defunct(text=message)
        sig = acct.sign_message(m).signature.hex()
        await update.message.reply_text(f"Signature:\n{sig}")
        return ConversationHandler.END

    async def verify_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return ConversationHandler.END
        await update.message.reply_text("Paste three lines: address, message, signature")
        return VERIFY_AWAIT

    async def verify_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            text = update.message.text
            addr, message, signature = [l.strip() for l in text.splitlines()[:3]]
            from eth_account.messages import encode_defunct
            m = encode_defunct(text=message)
            from eth_account import Account
            signer = Account.recover_message(m, signature=signature)
            ok = Web3.to_checksum_address(signer) == Web3.to_checksum_address(addr)
            await update.message.reply_text(f"Verified: {ok}\nRecovered: {signer}")
        except Exception as e:
            await update.message.reply_text(f"Verify failed: {e}")
        return ConversationHandler.END

    async def token_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /token_add <symbol> <address> [decimals]")
            return
        symbol = context.args[0].upper()
        addr = context.args[1]
        try:
            checksum = Web3.to_checksum_address(addr)
        except Exception:
            await update.message.reply_text("Invalid token address")
            return
        decimals = None
        if len(context.args) >= 3:
            try:
                decimals = int(context.args[2])
            except Exception:
                decimals = None
        tokens = self.storage.get_tokens()
        chat_key = str(update.effective_chat.id)
        chat_registry = tokens.get(chat_key, {})
        chat_registry[symbol] = {"address": checksum, "decimals": decimals}
        tokens[chat_key] = chat_registry
        self.storage.save_tokens(tokens)
        await update.message.reply_text(f"Added {symbol} at {checksum} (decimals={decimals})")

    async def token_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /token_balance <symbol>")
            return
        symbol = context.args[0].upper()
        tokens = self.storage.get_tokens()
        registry = tokens.get(str(update.effective_chat.id), {})
        if symbol not in registry:
            await update.message.reply_text("Unknown token in this chat. Use /token_add")
            return
        info = registry[symbol]
        contract = self.wallet.w3.eth.contract(address=info["address"], abi=[
            {"name":"balanceOf","inputs":[{"name":"","type":"address"}],"outputs":[{"name":"","type":"uint256"}],"type":"function"},
            {"name":"decimals","inputs":[],"outputs":[{"name":"","type":"uint8"}],"type":"function"}
        ])
        user = update.effective_user
        idx = self._get_derivation_index(user.id)
        acct = self._derive_account_for_index(idx)
        bal = contract.functions.balanceOf(acct.address).call()
        decimals = info.get("decimals") or contract.functions.decimals().call()
        human = Decimal(bal) / Decimal(10**int(decimals))
        await update.message.reply_text(f"{symbol} balance: {human}")

    async def token_send_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_whitelist(update, context):
            return ConversationHandler.END
        await update.message.reply_text("Enter token symbol to send:")
        return TSYMBOL

    async def token_send_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = update.message.text.strip().upper()
        tokens = self.storage.get_tokens()
        registry = tokens.get(str(update.effective_chat.id), {})
        if symbol not in registry:
            await update.message.reply_text("Unknown token. Use /token_add")
            return ConversationHandler.END
        context.user_data["tsym"] = symbol
        await update.message.reply_text("Enter destination address:")
        return TTO

    async def token_send_to(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            to = Web3.to_checksum_address(update.message.text.strip())
        except Exception:
            await update.message.reply_text("Invalid address")
            return ConversationHandler.END
        context.user_data["tto"] = to
        await update.message.reply_text("Enter amount:")
        return TAMOUNT

    async def token_send_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = Decimal(update.message.text.strip())
        except Exception:
            await update.message.reply_text("Invalid amount")
            return ConversationHandler.END
        symbol = context.user_data["tsym"]
        tokens = self.storage.get_tokens()
        registry = tokens.get(str(update.effective_chat.id), {})
        info = registry[symbol]
        decimals = int(info.get("decimals") or 18)
        value = int((amount * Decimal(10**decimals)).to_integral_value())
        contract = self.wallet.w3.eth.contract(address=info["address"], abi=[
            {"name":"transfer","inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"outputs":[{"name":"","type":"bool"}],"type":"function"}
        ])
        tx_data = contract.functions.transfer(context.user_data["tto"], value).build_transaction({"from": self._derive_account_for_index(self._get_derivation_index(update.effective_user.id)).address})["data"]
        acct = self._derive_account_for_index(self._get_derivation_index(update.effective_user.id))
        try:
            tx = self.wallet.build_tx(acct.address, info["address"], 0, data=tx_data)
            tx_hash = self.wallet.sign_and_send(acct, tx)
        except Exception as e:
            await update.message.reply_text(f"Token send failed: {e}")
            return ConversationHandler.END
        await update.message.reply_text(f"Sent {amount} {symbol} to {context.user_data['tto']}. Tx: {tx_hash}")
        return ConversationHandler.END
