import os
import sys
sys.path.append(os.path.abspath(".."))
from time import sleep
from violas_client import Wallet, Client

from violas_client.bank_client import Client as BankClient
from violas_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS

from violas_client.error.error import LibraError

fileName = "./bank_wallet_recovery"

bankCli = BankClient.new("http://52.27.228.84:50001", faucet_file = "../mint_test.key")
#bankCli = BankClient()

if os.path.exists(fileName):
    print("wallet already created!")
    wallet = Wallet.recover(fileName)

    account = wallet.new_account()
else:
    print("Create new wallet!")
    wallet = Wallet.new()
    wallet.write_recovery(fileName)

    account = wallet.new_account()

bankCli.set_bank_module_address(CORE_CODE_ADDRESS)
bankCli.set_bank_owner_address("00000000000000000000000042414E4B")

print(f"account address: {account.address_hex}")
print(f"auth key prefix: {account.auth_key_prefix.hex()}")
print(f"currencies on chain: {bankCli.get_registered_currencies()}")

# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix)
# bankCli.add_currency_to_account(account, "VLSUSD")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="VLSUSD")
# bankCli.add_currency_to_account(account, "VLSEUR")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="VLSEUR")
# bankCli.add_currency_to_account(account, "VLSGBP")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="VLSGBP")
# bankCli.add_currency_to_account(account, "USD")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="USD")
# bankCli.add_currency_to_account(account, "EUR")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="EUR")
# bankCli.add_currency_to_account(account, "GBP")
# bankCli.mint_coin(account.address_hex, 5000000, account.auth_key_prefix, currency_code="GBP")
# bankCli.add_currency_to_account(account, "SGD")

# bankCli.bank_publish(account)

# res = bankCli.bank_lock(account, 1000000, "USD")
# print(f"lock 1000000 USD return: {res}")
# res = bankCli.bank_lock(account, 1000000, "GBP")
# print(f"lock 1000000 GBP return: {res}")

# res = bankCli.bank_redeem(account, "USD", 2000)
# print(f"redeem 2000 USD return:{res}")
# res = bankCli.bank_redeem(account, "GBP", 3000)
# print(f"redeem 3000 GBP return:{res}")

# res = bankCli.bank_borrow(account, 40000, "EUR")
# print(f"borrow 40000 EUR return: {res}")
# try:
#     res = bankCli.bank_repay_borrow(account, "EUR", 1000)
#     print(f"repay 37000 EUR return: {res}")
# except LibraError as e:
#     print(e.data)

print(f"account balance: {bankCli.get_balances(account.address_hex)}")
res = bankCli.bank_get_lock_rate("USD")
print(f"rate of lock USD: {res}")
res = bankCli.bank_get_lock_rate("GBP")
print(f"rate of lock GBP: {res}")
res = bankCli.bank_get_lock_rate("EUR")
print(f"rate of lock EUR: {res}")
res = bankCli.bank_get_lock_amounts(account.address_hex)
print(f"locked amount: {res}")

res = bankCli.bank_get_borrow_rate("USD")
print(f"rate of borrow USD: {res}")
res = bankCli.bank_get_borrow_rate("GBP")
print(f"rate of borrow GBP: {res}")
res = bankCli.bank_get_borrow_rate("EUR")
print(f"rate of borrow EUR: {res}")
res = bankCli.bank_get_total_borrow_value(account.address_hex)
print(f"total borrow value: {res}")
res = bankCli.bank_get_max_borrow_amount(account.address_hex, "VLSUSD")
print(f"max borrow amount: {res}")
