import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time import sleep
from violas_client import Wallet, Client
from violas_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS
from violas_client.lbrtypes.account_config import association_address

filename = "./wallet_account_recovery"

cli = Client.new("http://52.27.228.84:50001", faucet_file = "../mint_test.key")
# cli = Client()

if os.path.exists(filename):
    print(f"Wallet already created!")
    wallet = Wallet.recover(filename)

    account = wallet.new_account()
else:
    print(f"Create new wallet.")
    wallet = Wallet.new()
    wallet.write_recovery(filename)

    account = wallet.new_account()

print(f"account address: {account.address_hex}")
print(f"auth key perfix: {account.auth_key_prefix.hex()}")
