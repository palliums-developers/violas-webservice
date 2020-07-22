import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time import sleep
from violas_client.exchange_client import Wallet, Client
from violas_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS
from violas_client.lbrtypes.account_config import association_address

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
    cli.add_currency_to_account(moduleAccount, "VLSUSD")
    cli.mint_coin(moduleAccount.address, 100000000, auth_key_prefix=moduleAccount.auth_key_prefix, currency_code="VLSUSD")
    cli.add_currency_to_account(moduleAccount, "VLSEUR")
    cli.mint_coin(moduleAccount.address, 100000000, auth_key_prefix=moduleAccount.auth_key_prefix, currency_code="VLSEUR")

    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix)
    cli.add_currency_to_account(liquidityAccount, "VLSUSD")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="VLSUSD")
    cli.add_currency_to_account(liquidityAccount, "VLSEUR")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="VLSEUR")
    cli.add_currency_to_account(liquidityAccount, "VLSGBP")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="VLSGBP")
    cli.add_currency_to_account(liquidityAccount, "VLSSGD")
    cli.mint_coin(liquidityAccount.address, 100000000, auth_key_prefix=liquidityAccount.auth_key_prefix, currency_code="VLSSGD")

    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix)
    cli.add_currency_to_account(swapAccount, "VLSUSD")
    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix, currency_code="VLSUSD")
    cli.add_currency_to_account(swapAccount, "VLSEUR")
    cli.mint_coin(swapAccount.address, 100000000, auth_key_prefix=swapAccount.auth_key_prefix, currency_code="VLSEUR")

    # print("publish contract")
    # cli.swap_publish_contract(moduleAccount)
    # print("initialize swap")
    # cli.swap_initialize(moduleAccount)

print(f"module account address: {moduleAccount.address_hex}")
print(f"module account balance: {cli.get_balances(moduleAccount.address)}")
print(f"liquidity account address: {liquidityAccount.address_hex}")
print(f"liquidity account balance: {cli.get_balances(liquidityAccount.address)}")
print(f"swap account address: {swapAccount.address_hex}")
print(f"swap account balance: {cli.get_balances(swapAccount.address)}")

# print(f"set exchange module address to: {moduleAccount.address_hex}")
# cli.set_exchange_module_address(moduleAccount.address)
print(f"set exchange module address to: {CORE_CODE_ADDRESS.hex()}")
cli.set_exchange_module_address(CORE_CODE_ADDRESS)
print(f"set exchange owner address to: {association_address().hex()}")
cli.set_exchange_owner_address(association_address())


# print("add LBR to swap")
# cli.swap_add_currency(moduleAccount, "LBR")
# print("add VLSUSD to swap")
# cli.swap_add_currency(moduleAccount, "VLSUSD")
# print("add VLSEUR to swap")
# cli.swap_add_currency(moduleAccount, "VLSEUR")

# print("make liquidity")

# cli.swap_add_liquidity(liquidityAccount, "VLSUSD", "VLSEUR", 10000, 5318)
# cli.swap_add_liquidity(liquidityAccount, "", "VLSEUR", 10000, 5318)
# cli.swap_remove_liquidity(liquidityAccount, "VLSUSD", "VLSEUR", 9000)
# cli.swap_remove_liquidity(liquidityAccount, "VLSUSD", "VLSEUR", 999)

# print("make swap")
# cli.swap(liquidityAccount, "VLSUSD", "VLSEUR", 10000)


print(f"swap registered currencies: {cli.swap_get_registered_currencies()}")
print(f"reserver info: {cli.swap_get_reserves_resource()}")
print(f"liquidity account balance: {cli.swap_get_liquidity_balances(liquidityAccount.address_hex)}")
# print(f"get liquidity rate: {1000000 / cli.swap_get_liquidity_output_amount('VLSEUR', 'VLSUSD', 1000000)}")
