import sys
sys.path.append("..")
from violas import Wallet

filename = "./account_recovery"
module = "e1be1ab8360a35a0259f1c93e3eac736"

wallet = Wallet.recover(filename)
account = wallet.accounts[0]

print("Wallet info:")
print(f"Address: {account.address_hex}")
print(f"Auth_key_prefix: {account.auth_key_prefix_hex}")
print(f"Private Key: {account.private_key_hex}")
print(f"Public Kye: {account.public_key_hex}")


