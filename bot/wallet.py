from decimal import Decimal, ROUND_DOWN
from typing import Optional

from web3 import Web3
from web3.types import TxParams
from eth_account import Account
from eth_account.signers.local import LocalAccount


class WalletManager:
    def __init__(self, w3: Web3, mnemonic: str, chain_id: int, gas_price_gwei: Optional[str] = None, faucet_pk: Optional[str] = None):
        self.w3 = w3
        self.mnemonic = mnemonic
        self.chain_id = chain_id
        self.gas_price_gwei = gas_price_gwei
        self.faucet_pk = faucet_pk
        Account.enable_unaudited_hdwallet_features()

    def derive_account(self, user_id: int) -> LocalAccount:
        index = user_id 
        path = f"m/44'/60'/0'/0/{index}"
        acct = Account.from_mnemonic(self.mnemonic, account_path=path)
        return acct

    def get_balance(self, address: str) -> Decimal:
        checksum = Web3.to_checksum_address(address)
        wei = self.w3.eth.get_balance(checksum)
        return Decimal(wei) / Decimal(10**18)

    def _gwei_to_wei(self, g: Decimal) -> int:
        return int((g * Decimal(10**9)).to_integral_value(rounding=ROUND_DOWN))

    def get_gas_price(self) -> int:
        if self.gas_price_gwei:
            return self._gwei_to_wei(Decimal(self.gas_price_gwei))
        return self.w3.eth.gas_price

    def build_tx(self, from_addr: str, to: Optional[str], value_wei: int, data: bytes = b"") -> TxParams:
        tx: TxParams = {
            "chainId": self.chain_id,
            "from": Web3.to_checksum_address(from_addr),
            "to": Web3.to_checksum_address(to) if to else None,
            "value": value_wei,
            "data": data,
            "gasPrice": self.get_gas_price(),
        }
        tx["nonce"] = self.w3.eth.get_transaction_count(from_addr)
        estimate_dict = {k: v for k, v in tx.items() if v is not None}
        gas_est = self.w3.eth.estimate_gas(estimate_dict)
        tx["gas"] = int(gas_est * 1.2)
        return tx

    def sign_and_send(self, acct: LocalAccount, tx: TxParams) -> str:
        signed = acct.sign_transaction(tx)
        raw = None
        if hasattr(signed, "rawTransaction"):
            raw = getattr(signed, "rawTransaction")
        elif hasattr(signed, "raw_transaction"):
            raw = getattr(signed, "raw_transaction")
        else:
            try:
                raw = signed["rawTransaction"]
            except Exception:
                raw = None
        if raw is None:
            raise RuntimeError("Could not find raw transaction bytes on signed transaction (version mismatch)")
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        return tx_hash.hex()

    def send_eth(self, acct: LocalAccount, to: str, value_wei: int) -> str:
        tx = self.build_tx(acct.address, to, value_wei)
        return self.sign_and_send(acct, tx)

    def faucet(self, to: str, amount_wei: int) -> str:
        if not self.faucet_pk:
            raise RuntimeError("Faucet not configured")
        faucet_acct = Account.from_key(self.faucet_pk)
        tx = self.build_tx(faucet_acct.address, to, amount_wei)
        return self.sign_and_send(faucet_acct, tx)
