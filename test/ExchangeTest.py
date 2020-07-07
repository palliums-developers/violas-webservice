import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time import sleep
from violas_client.exchange_client import Wallet, Client

filename = "./account_recovery"

cli = Client.new("http://52.27.228.84:50001", faucet_file = "../mint_test.key")
#cli = Client()

if os.path.exists(filename):
    print(f"Wallet already created!")
    wallet = Wallet.recover(filename)

    moduleAccount = wallet.new_account()
    liquidityAccount = wallet.new_account()
    swapAccount = wallet.new_account()
else:
    print(f"Create new wallet.")
    wallet = Wallet.new()
    wallet.write_recovery(filename)

    moduleAccount = wallet.new_account()
    liquidityAccount = wallet.new_account()
    swapAccount = wallet.new_account()


    cli.mint_coin(moduleAccount.address, 100000000, auth_key_prefix=moduleAccount.auth_key_prefix)
    cli.add_currency_to_account(moduleAccount, "Coin1")
    cli.mint_coin(moduleAccount.address, 100000000, auth_key_prefix=moduleAccount.auth_key_prefix, currency_code="Coin1")
    cli.add_currency_to_account(moduleAccount, "Coin2")
    cli.mint_coin(moduleAccount.address, 100000000, auth_key_prefix=moduleAccount.auth_key_prefix, currency_code="Coin2")

    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix)
    cli.add_currency_to_account(liquidityAccount, "Coin1")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="Coin1")
    cli.add_currency_to_account(liquidityAccount, "Coin2")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="Coin2")

    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix)
    cli.add_currency_to_account(swapAccount, "Coin1")
    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix, currency_code="Coin1")
    cli.add_currency_to_account(swapAccount, "Coin2")
    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix, currency_code="Coin2")

print(f"module account address: {moduleAccount.address_hex}")
print(f"liquidity account address: {liquidityAccount.address_hex}")
print(f"swap account address: {swapAccount.address_hex}")
print(f"module account balance: {cli.get_balances(moduleAccount.address)}")
print(f"liquidity account balance: {cli.get_balances(liquidityAccount.address)}")
print(f"swap account balance: {cli.get_balances(swapAccount.address)}")

# print("publish contract")
# cli.swap_publish_contract(moduleAccount)
# print("initialize swap")
# cli.swap_initialize(moduleAccount)

cli.set_exchange_module_address(moduleAccount.address)
print(f"set exchange module address to: {cli.get_exchange_module_address().hex()}")

# print("add LBR to swap")
# cli.swap_add_currency(moduleAccount, "LBR")
# print("add Coin1 to swap")
# cli.swap_add_currency(moduleAccount, "Coin1")
# print("add Coin2 to swap")
# cli.swap_add_currency(moduleAccount, "Coin2")

# print("add liquidity")
# cli.swap_add_liquidity(liquidityAccount, "LBR", "Coin1", 1000000, 2000000)



print(f"swap registered currencies: {cli.swap_get_registered_currencies()}")
print(f"reserver info: {cli.swap_get_reserves_resource()}")
print(f"")
# print(f"liquidity account balance: {cli.swap_get_liquidity_balances(liquidityAccount.address_hex)}")
# print(f"get liquidity rate: {cli.swap_get_liquidity_output_amount('LBR', 'Coin1', 1000000)}")