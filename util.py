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
