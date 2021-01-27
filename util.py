from common import *

from datetime import datetime
from decimal import Decimal

from libra_client import Client as LibraClient
from violas_client import Client as ViolasClient
from violas_client import exchange_client
from violas_client import bank_client
from violas_client import Wallet

from ErrorCode import ErrorMsg

def MakeLibraClient():
    return LibraClient(config["NODE INFO"]["LIBRA_HOST"])

def MakeViolasClient():
    # return ViolasClient()
    return ViolasClient.new(config['NODE INFO']['VIOLAS_HOST'])

def MakeExchangeClient():
    # return exchange_client.Client()
    cli = exchange_client.Client.new(config['NODE INFO']['VIOLAS_HOST'])
    cli.set_exchange_module_address(VIOLAS_CORE_CODE_ADDRESS)
    cli.set_exchange_owner_address(config["NODE INFO"]["EXCHANGE_MODULE_ADDRESS"])
    return cli

def MakeBankClient():
    # return bank_client.Client()
    cli = bank_client.Client.new(config['NODE INFO']['VIOLAS_HOST'])
    cli.set_bank_module_address(VIOLAS_CORE_CODE_ADDRESS)
    cli.set_bank_owner_address(config["NODE INFO"]["BANK_MODULE_ADDRESS"])
    return cli

def MakeResp(code, data = None, exception = None, message = None):
    resp = {}

    resp["code"] = code
    if exception is not None:
        resp["message"] = f"{exception.msg}"
    elif message is not None:
        resp["message"] = message
    else:
        resp["message"] = ErrorMsg[code]

    if data is not None:
        resp["data"] = data

    return resp

def AllowedType(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def GetRates():
    # yesterday = datetime.date.fromtimestamp(time.time() - 24 * 60 * 60)
    # today = datetime.date.today()
    # start = f"{yesterday.year}-{yesterday.month if yesterday.month > 9 else '0' + str(yesterday.month)}-{yesterday.day if yesterday.day > 9 else '0' + str(yesterday.day)}"
    # end = f"{today.year}-{today.month if today.month > 9 else '0' + str(today.month)}-{today.day if today.day > 9 else '0' + str(today.day)}"
    # url = f"https://api.exchangeratesapi.io/history?base=USD&start_at={start}&end_at={end}"
    url = f"https://api.exchangeratesapi.io/latest?base=USD"
    resp = requests.get(url)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    rates = resp.json()["rates"]

    return rates

def VerifyCodeExist(receiver, code):
    value = rdsVerify.get(receiver)

    if value is None:
        return False
    elif value.decode("utf8") != str(code):
        return False

    rdsVerify.delete(receiver)

    return True

def get_show_name(name):
    if name == "Coin1":
        return "USD"
    if name == "Coin2":
        return "EUR"
    return name


class AddressInfo():
    BTC_CHAIN_NAME = "btc"
    LIBRA_CHAIN_NAME = "libra"
    VIOLAS_CHAIN_NAME = "violas"
    ETH_CHAIN_NAME = "eth"

    def __init__(self, type, address, scoin, rcoin, lable=None):
        self.type = type
        flow = type[0:3]
        chain_in, chain_out = flow.split("2")
        self.schain = self._parse_chain_name(chain_in)
        self.rchain = self._parse_chain_name(chain_out)
        self.lable = lable
        self.scoin = scoin
        self.rcoin = rcoin

        self.type = type
        self.address = address

    def get_lable(self):
        if self.schain != self.BTC_CHAIN_NAME:
            return self.type
        return self.lable

    def get_receiver_address(self):
        if self.schain == self.BTC_CHAIN_NAME:
            return self.address
        return self.address[:32]

    def get_smodule_address(self):
        if self.schain == self.LIBRA_CHAIN_NAME:
            return LIBRA_CORE_CODE_ADDRESS.hex()
        elif self.schain == self.VIOLAS_CHAIN_NAME:
            return VIOLAS_CORE_CODE_ADDRESS.hex()
        else:
            return ""

    def get_rmodule_address(self):
        if self.rchain == self.LIBRA_CHAIN_NAME:
            return LIBRA_CORE_CODE_ADDRESS.hex()
        elif self.rchain == self.VIOLAS_CHAIN_NAME:
            return VIOLAS_CORE_CODE_ADDRESS.hex()
        else:
            return ""


    def get_smapping_name(self):
        return self.scoin

        # if self.schain == self.BTC_CHAIN_NAME:
        #     return "BTC"
        # coin = self.type[3:].upper()
        # if self.schain == self.LIBRA_CHAIN_NAME:
        #     if coin == "USD":
        #         return "Coin1"
        #     if coin == "EUR":
        #         return "Coin2"
        # return coin

    def get_rmapping_name(self):
        return self.rcoin

        # if self.rchain == self.BTC_CHAIN_NAME:
        #     return "BTC"
        # coin = self.type[3:].upper()
        # if self.rchain == self.LIBRA_CHAIN_NAME:
        #     if coin == "USD":
        #         return "Coin1"
        #     if coin == "EUR":
        #         return "Coin2"
        # return coin

    def get_show_name(self, name):
        if name == "Coin1":
            return "USD"
        if name == "Coin2":
            return "EUR"
        return name

    def get_slogo_url(self):
        from common import ICON_URL
        return f"{ICON_URL}{self.schain}.png"

    def get_rlogo_url(self):
        from common import ICON_URL
        return f"{ICON_URL}{self.rchain}.png"

    def to_mapping_json(self):
        return {
            "from_coin": {
                "assert": {
                    "address": self.get_smodule_address(),
                    "module": self.get_smapping_name(),
                    "name": self.get_smapping_name(),
                    "show_name": self.get_show_name(self.get_smapping_name()),
                    "icon": self.get_slogo_url()
                },
                "coin_type": self.schain
            },
            "to_coin": {
                "assert": {
                    "address": self.get_rmodule_address(),
                    "module": self.get_rmapping_name(),
                    "name": self.get_rmapping_name(),
                    "show_name":self.get_show_name(self.get_rmapping_name()),
                    "icon": self.get_rlogo_url(),

                },
                "coin_type": self.rchain
            },
            "receiver_address": self.get_receiver_address(),
            "lable": self.get_lable()
        }

    def _parse_chain_name(self, v):
        if v == "b":
            return "btc"
        if v == "l":
            return "libra"
        if v == "v":
            return "violas"
        if v == "e":
            return "eth"

def GetIDNumber():
    idNumber = datetime.strftime(datetime.today(), "%Y%m%d%H%M%S")
    randNumber = random.randint(100000,999999)

    return idNumber + str(randNumber)

def GetMnemonic():
    filePath = "./backend.mne"

    if os.path.exists(filePath):
        with open(filePath) as f:
            data = f.read()
            keys = data.split(Wallet.DELIMITER)
            if len(keys) != 2:
                return None

            return keys

def GetAccount():
    mnemonic = GetMnemonic()
    wallet = Wallet.new_from_mnemonic(mnemonic[0])
    wallet.generate_addresses(int(mnemonic[1]))

    return wallet.new_account()

def MakeTransfer(senderAccount, receiveAddress, amount, coin = None):
    cli = MakeViolasClient()
    cli.transfer_coin(senderAccount, receiveAddress, amount, currency_code = coin, gas_currency_code = coin)

def ConvertToUSD(amount):
    return float(Decimal(amount / 1000000).quantize(Decimal("0.00")))
