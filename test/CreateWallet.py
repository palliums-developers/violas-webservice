from os import path
from time import sleep
from violas_client.exchange_client import Wallet, Client

filename = "./account_recovery"

cli = Client.new("http://52.27.228.84:50001", faucet_file = "./mint_test.key")

if path.exists(filename):
    print(f"Wallet already created!")
    wallet = Wallet.recover(filename)
else:
    print(f"Create new wallet.")
    wallet = Wallet.new()
    wallet.write_recovery(filename)
