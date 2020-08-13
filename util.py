from common import *

from libra_client import Client as LibraClient
from violas_client import Client as ViolasClient
from violas_client import exchange_client

from ErrorCode import ErrorMsg

def MakeLibraClient():
    return LibraClient("libra_testnet")

def MakeViolasClient():
    return ViolasClient.new(config['NODE INFO']['VIOLAS_HOST'], faucet_file = config['NODE INFO']['VIOLAS_MINT_KEY'])

def MakeExchangeClient():
    cli = exchange_client.Client.new(config['NODE INFO']['VIOLAS_HOST'], faucet_file = config['NODE INFO']['VIOLAS_MINT_KEY'])
    cli.set_exchange_module_address(VIOLAS_CORE_CODE_ADDRESS)
    cli.set_exchange_owner_address(association_address())
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

    def __init__(self, type, address, lable=None):
        self.type = type
        flow = type[0:3]
        chain_in, chain_out = flow.split("2")
        self.schain = self._parse_chain_name(chain_in)
        self.rchain = self._parse_chain_name(chain_out)
        self.lable = lable

        self.type = type
        self.address = address

    def get_lable(self):
        if self.schain != self.BTC_CHAIN_NAME:
            return self.type[0:3] + "m"
        return self.lable

    def get_receiver_address(self):
        if self.rchain == self.BTC_CHAIN_NAME:
            return self.address
        return self.address[32:]

    def get_smodule_address(self):
        if self.schain == self.BTC_CHAIN_NAME:
            return ""
        if self.schain == self.LIBRA_CHAIN_NAME:
            return LIBRA_CORE_CODE_ADDRESS.hex()
        if self.schain == self.VIOLAS_CHAIN_NAME:
            return VIOLAS_CORE_CODE_ADDRESS.hex()

    def get_rmodule_address(self):
        if self.rchain == self.BTC_CHAIN_NAME:
            return ""
        if self.rchain == self.LIBRA_CHAIN_NAME:
            return LIBRA_CORE_CODE_ADDRESS.hex()
        if self.rchain == self.VIOLAS_CHAIN_NAME:
            return VIOLAS_CORE_CODE_ADDRESS.hex()

    def get_smapping_module(self):
        if self.schain == self.BTC_CHAIN_NAME:
            return ""
        return self.type[3:].upper()

    def get_rmapping_module(self):
        if self.rchain == self.BTC_CHAIN_NAME:
            return ""
        return self.type[3:].upper()

    def get_smapping_name(self):
        if self.schain == self.BTC_CHAIN_NAME:
            return "BTC"
        return self.type[3:].upper()

    def get_rmapping_name(self):
        if self.rchain == self.BTC_CHAIN_NAME:
            return "BTC"
        return self.type[3:].upper()

    def get_slogo_url(self):
        return f"{ICON_URL}{self.schain}.png"

    def get_rlogo_url(self):
        return f"{ICON_URL}{self.rchain}.png"

    def to_mapping_json(self):
        return {
            "from_coin": {
                "assert": {
                    "address": self.get_smodule_address(),
                    "module": self.get_smapping_module(),
                    "name": self.get_smapping_name(),
                    "icon": self.get_slogo_url()
                },
                "coin_type": self.schain
            },
            "to_coin": {
                "assert": {
                    "address": self.get_rmodule_address(),
                    "module": self.get_rmapping_module(),
                    "name": self.get_rmapping_name(),
                    "icon": self.get_rlogo_url()
                },
                "coin_type": self.rchain
            },
            "lable": self.get_lable()
        }

    def _parse_chain_name(self, v):
        if v == "b":
            return "btc"
        if v == "l":
            return "libra"
        if v == "v":
            return "violas"

