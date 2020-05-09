from time import sleep
from violas import Wallet, Client

cli = Client.new("127.0.0.1", 40001, faucet_file = "./mint_external.key")

filename = "./account_recovery"
module = "e1be1ab8360a35a0259f1c93e3eac736"

wallet = Wallet.new()
account = wallet.new_account()
print("Wallet info:")
print(f"Address: {account.address_hex}")
print(f"Auth_key_prefix: {account.auth_key_prefix_hex}")
print(f"Private Key: {account.private_key_hex}")
print(f"Public Kye: {account.public_key_hex}")

cli.mint_coin(account.address_hex, 1000000, auth_key_prefix = account.auth_key_prefix_hex)
sleep(1)
cli.publish_resource(account, module)
sleep(1)
accountState = cli.get_account_state(account.address_hex)
print(f"{accountState.is_published(module)}")
moduleState = cli.get_account_state(module)
for i in range(moduleState.get_scoin_resources(module).get_token_num()):
    print(f"{moduleState.get_token_data(i, module)} = {cli.get_balance(account.address_hex, i, module)}")

wallet.write_recovery(filename)
