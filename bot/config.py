from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    RPC_URL: str = os.getenv("RPC_URL", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WALLET_MNEMONIC: str = os.getenv("WALLET_MNEMONIC", "")
    GAS_PRICE_GWEI: str = os.getenv("GAS_PRICE_GWEI", "")
    FAUCET_PRIVATE_KEY: str = os.getenv("FAUCET_PRIVATE_KEY", "")

    _chain_id = os.getenv("CHAIN_ID")
    CHAIN_ID: int | None = int(_chain_id) if _chain_id and _chain_id.isdigit() else None

    _whitelist = os.getenv("WHITELIST", "")
    WHITELIST: set[int] = frozenset(
        int(x.strip()) for x in _whitelist.split(",") if x.strip().isdigit()
    )

    def validate(self):
        missing = []

        if not self.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not self.WALLET_MNEMONIC:
            missing.append("WALLET_MNEMONIC")
        if not self.RPC_URL:
            missing.append("RPC_URL")
        if not self.WHITELIST:
            missing.append("WHITELIST")
        if not self.CHAIN_ID:
            missing.append("CHAIN_ID")

        if missing:
            print(f"[WARNING] Missing in .env: {', '.join(missing)}")


config = Config()
config.validate()
