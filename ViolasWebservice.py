import os, random, logging, configparser, datetime, json, time, datetime
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from redis import Redis
import requests
import nacl.signing
import hashlib

from libra_client import Client as LibraClient
from libra_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS as LIBRA_CORE_CODE_ADDRESS

from violas_client import Client as ViolasClient
from violas_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS as VIOLAS_CORE_CODE_ADDRESS
from violas_client.lbrtypes.account_config import association_address

from violas_client import exchange_client

from ViolasPGHandler import ViolasPGHandler
from LibraPGHandler import LibraPGHandler
from PushServerHandler import PushServerHandler

from ErrorCode import ErrorCode, ErrorMsg

logging.basicConfig(filename = "ViolasWebservice.log", level = logging.DEBUG)
config = configparser.ConfigParser()
config.read("./config.ini")

app = Flask(__name__)
CORS(app, resources = r"/*")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
PHOTO_FOLDER = os.path.abspath("/var/www/violas_wallet/photo")
PHOTO_URL = f"{config['IMAGE SERVER']['HOST']}/1.0/violas/photo/"
ICON_URL = f"{config['IMAGE SERVER']['HOST']}/1.0/violas/icon/"

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"
HLibra = LibraPGHandler(libraDBUrl)

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"
HViolas = ViolasPGHandler(violasDBUrl)

pushInfo = config["PUSH SERVER"]
pushh = PushServerHandler(pushInfo["HOST"], int(pushInfo["PORT"]))

cachingInfo = config["CACHING SERVER"]
rdsVerify = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["VERIFYDB"], cachingInfo["PASSWORD"])
rdsCoinMap = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["COINMAPDB"], cachingInfo["PASSWORD"])
rdsAuth = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["AUTH"], cachingInfo["PASSWORD"])

ContractAddress = "e1be1ab8360a35a0259f1c93e3eac736"

GovernorFailedReason = {
    -1: "其他",
    0: "信息不全面"
}

ChairmanFailedReason = {
    -1: "其他",
    0: "信息不全面"
}

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

# LIBRA WALLET
@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        if currency is None:
            balances = cli.get_balances(address)
            data = {"balances": balances}
            data = []
            for key, value in balances.items():
                item = {}
                item["name"] = key
                item["balance"] = value

                if key == "Coin1":
                    showName = "USD"
                elif key == "Coin2":
                    showName = "EUR"
                else:
                    showName = key

                item["show_name"] = showName
                item["show_icon"] = f"{ICON_URL}libra.png"
                item["address"] = address

                data.append(item)
        else:
            balance = cli.get_balance(address, currency_code = currency)
            if currency == "Coin1":
                showName = "USD"
            elif currency == "Coin2":
                showName = "EUR"
            else:
                showName = currency

            data = [{currency: balance, "name": currency, "show_name": showName, "show_icon": f"{ICON_URL}libra.png"}]

    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, {"balances": data})

@app.route("/1.0/libra/seqnum")
def GetLibraSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
        return MakeResp(ErrorCode.ERR_OK, {"seqnum": seqNum})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeLibraClient()
    try:
        cli.submit_signed_transaction(signedtxn, True)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    flows = request.args.get("flows", type = int)
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)
    address = address.lower()

    succ, datas = HLibra.GetTransactionsForWallet(address, currency, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/libra/mint")
def MintLibraToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        cli.mint_coin(address, 100, auth_key_prefix = authKey, is_blocking = True, currency_code=currency)
    except ValueError:
        return MakeResp(ErrorCode.ERR_INVAILED_ADDRESS)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/currency")
def GetLibraCurrency():
    cli = MakeLibraClient()

    try:
        currencies = cli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = []
    for i in currencies:
        cInfo = {}
        cInfo["name"] = i
        cInfo["module"] = i
        cInfo["address"] = LIBRA_CORE_CODE_ADDRESS.hex()
        cInfo["show_icon"] = f"{ICON_URL}libra.png"
        if i == "Coin1":
            cInfo["show_name"] = "USD"
        elif i == "Coin2":
            cInfo["show_name"] = "EUR"
        else:
            cInfo["show_name"] = i

        data.append(cInfo)

    return MakeResp(ErrorCode.ERR_OK, {"currencies": data})

@app.route("/1.0/libra/account/info")
def GetLibraAccountInfo():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeLibraClient()

    try:
        state = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_account_resource().authentication_key.hex(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_account_resource().key_rotation_capability.value.account_address.hex(),
            "delegated_withdrawal_capability": state.get_account_resource().withdrawal_capability.value.account_address.hex(),
            "received_events_key": state.get_account_resource().received_events.get_key(),
            "sent_events_key": state.get_account_resource().sent_events.get_key()}

    return MakeResp(ErrorCode.ERR_OK, data)

# VIOLAS WALLET
@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeViolasClient()
    try:
        if currency is None:
            balances = cli.get_balances(address)

            data = []
            for key, value in balances.items():
                item = {}
                item["name"] = key
                item["balance"] = value
                item["show_name"] = key
                item["show_icon"] = f"{ICON_URL}violas.png"
                item["address"] = address

                data.append(item)
        else:
            balance = cli.get_balance(address, currency_code = currency)
            showName = currency[3:] if len(currency) > 3 else currency
            data = [{currency: balance, "name": currency, "show_name": currency, "show_icon": f"{ICON_URL}violas.png"}]

    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, {"balances": data})

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeViolasClient()
    try:
        seqNum = cli.get_account_sequence_number(address)
        return MakeResp(ErrorCode.ERR_OK, {"seqnum": seqNum})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeViolasClient()

    try:
        cli.submit_signed_transaction(signedtxn, True)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/transaction")
def GetViolasTransactionInfo():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    flows = request.args.get("flows", type = int)
    limit = request.args.get("limit", 10, int)
    offset = request.args.get("offset", 0, int)
    address = address.lower()

    succ, datas = HViolas.GetTransactionsForWallet(address, currency, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/currency")
def GetViolasCurrency():
    cli = MakeViolasClient()

    try:
        currencies = cli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    filtered = []
    for i in currencies:
        if i != "Coin1" and i != "Coin2":
            filtered.append(i)

    data = []
    for i in filtered:
        cInfo = {}
        cInfo["name"] = i
        cInfo["module"] = i
        cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
        cInfo["show_icon"] = f"{ICON_URL}violas.png"
        cInfo["show_name"] = i

        data.append(cInfo)

    return MakeResp(ErrorCode.ERR_OK, {"currencies": data})

@app.route("/1.0/violas/currency/published")
def CheckCurrencyPublished():
    addr = request.args.get("addr")
    addr = addr.lower()

    cli = MakeViolasClient()

    try:
        balances = cli.get_balances(addr)
        print(balances)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    keys = []
    for key in balances:
        keys.append(key)

    return MakeResp(ErrorCode.ERR_OK, {"published": keys})

def AllowedType(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/1.0/violas/photo", methods = ["POST"])
def UploadPhoto():
    photo = request.files["photo"]

    if not AllowedType(photo.filename):
        return MakeResp(ErrorCode.ERR_IMAGE_FORMAT)

    ext = secure_filename(photo.filename).rsplit(".", 1)[1]
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    randomNum = random.randint(1000, 9999)
    uuid = str(nowTime) + str(randomNum) + "." + ext
    path = os.path.join(PHOTO_FOLDER, uuid)
    photo.save(path)

    return MakeResp(ErrorCode.ERR_OK, {"image": uuid})

@app.route("/1.0/violas/verify_code", methods = ["POST"])
def SendVerifyCode():
    params = request.get_json()
    address = params["address"]
    local_number = params.get("phone_local_number")
    receiver = params["receiver"]

    receiver = receiver.lower()
    address = address.lower()

    verifyCode = random.randint(100000, 999999)

    succ, result = HViolas.AddSSOUser(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if receiver.find("@") >= 0:
        succ = pushh.PushEmailSMSCode(verifyCode, receiver, 5)
        rdsVerify.setex(receiver, 600, str(verifyCode))
    else:
        succ = pushh.PushPhoneSMSCode(verifyCode, local_number + receiver, 5)
        rdsVerify.setex(local_number + receiver, 600, str(verifyCode))

    if not succ:
        return MakeResp(ErrorCode.ERR_SEND_VERIFICATION_CODE)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/singin", methods = ["POST"])
def UploadWalletInfo():
    params = request.get_json()
    wallets = []
    for i in params["wallets"]:
        wallets.append(i)

    value = rdsAuth.get(params["session_id"])

    if value is None:
        return MakeResp(ErrorCode.ERR_SESSION_NOT_EXIST)

    data = {"status": "Success", "wallets": wallets}

    rdsAuth.set(params["session_id"], json.JSONEncoder().encode(data))

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/mint")
def MintViolasToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeViolasClient()
    try:
        cli.mint_coin(address, 100, auth_key_prefix = authKey, is_blocking = True, currency_code=currency)
    except ValueError:
        return MakeResp(ErrorCode.ERR_INVAILED_ADDRESS)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/account/info")
def GetAccountInfo():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        state = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_account_resource().authentication_key.hex(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_account_resource().key_rotation_capability.value.account_address.hex(),
            "delegated_withdrawal_capability": state.get_account_resource().withdrawal_capability.value.account_address.hex(),
            "received_events_key": state.get_account_resource().received_events.get_key(),
            "sent_events_key": state.get_account_resource().sent_events.get_key()}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/value/btc")
def GetBTCValue():
    url = "https://api.coincap.io/v2/assets/bitcoin"
    resp = requests.get(url)
    rate = resp.json()["data"]["priceUsd"]

    data = [{"name": "BTC", "rate": float(rate)}]

    return MakeResp(ErrorCode.ERR_OK, data)

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

@app.route("/1.0/violas/value/violas")
def GetViolasValue():
    address = request.args.get("address")
    cli = MakeViolasClient()

    balances = cli.get_balances(address)
    currencies = []
    for currency in balances.keys():
        currencies.append(currency)

    rates = GetRates()
    values = []
    for currency in currencies:
        item = {}
        item["name"] = currency
        item["rate"] = rates.get(currency[3:]) if rates.get(currency[3:]) is not None else 0

        values.append(item)

    return MakeResp(ErrorCode.ERR_OK, values)

@app.route("/1.0/violas/value/libra")
def GetLibraValue():
    address = request.args.get("address")
    cli = MakeLibraClient()

    balances = cli.get_balances(address)
    currencies = []
    for currency in balances.keys():
        currencies.append(currency)

    rates = GetRates()
    values = []
    for currency in currencies:
        item = {}
        if currency == "Coin1":
            name = "USD"
        elif currency == "Coin2":
            name = "EUR"
        else:
            name = currency

        item["name"] = currency
        item["rate"] = rates.get(name) if rates.get(name) is not None else 0

        values.append(item)

    return MakeResp(ErrorCode.ERR_OK, values)

# VBTC
@app.route("/1.0/violas/vbtc/transaction")
def GetVBtcTransactionInfo():
    receiverAddress = request.args.get("receiver_address")
    moduleAddress = request.args.get("module_address")
    startVersion = request.args.get("start_version", type = int)

    receiverAddress = receiverAddress.lower()
    moduleAddress = moduleAddress.lower()

    succ, datas = HViolas.GetTransactionsAboutVBtc(receiverAddress, moduleAddress, startVersion)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/vbtc/transaction", methods = ["POST"])
def VerifyVBtcTransactionInfo():
    params = request.get_json()

    params["sender_address"] = params["sender_address"].lower()
    params["receiver"] = params["receiver"].lower()
    params["module"] = params["module"].lower()

    succ, result = HViolas.VerifyTransactionAboutVBtc(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_VBTC_TRANSACTION_INFO)

    return MakeResp(ErrorCode.ERR_OK)

# SSO
@app.route("/1.0/violas/sso/user", methods = ["POST"])
def SSOUserRegister():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddSSOUser(params["wallet_address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ, result = HViolas.UpdateSSOUserInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/user")
def GetSSOUserInfo():
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetSSOUserInfo(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    if info["id_photo_positive_url"] is not None:
        info["id_photo_positive_url"] = PHOTO_URL + info["id_photo_positive_url"]

    if info["id_photo_back_url"] is not None:
        info["id_photo_back_url"] = PHOTO_URL + info["id_photo_back_url"]

    return MakeResp(ErrorCode.ERR_OK, info)

def VerifyCodeExist(receiver, code):
    value = rdsVerify.get(receiver)

    if value is None:
        return False
    elif value.decode("utf8") != str(code):
        return False

    rdsVerify.delete(receiver)

    return True

@app.route("/1.0/violas/sso/bind", methods = ["POST"])
def BindUserInfo():
    params = request.get_json()
    receiver = params["receiver"]
    verifyCode = params["code"]
    address = params["address"]
    local_number = params.get("phone_local_number")

    receiver = receiver.lower()
    address = address.lower()

    if receiver.find("@") >= 0:
        match = VerifyCodeExist(receiver, verifyCode)
    else:
        match = VerifyCodeExist(local_number + receiver, verifyCode)

    if not match:
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)
    else:
        data = {}
        data["wallet_address"] = address
        if receiver.find("@") >= 0:
            data["email_address"] = receiver
        else:
            data["phone_local_number"] = local_number
            data["phone_number"] = receiver

        succ, result = HViolas.UpdateSSOUserInfo(data)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        if not result:
            return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, userInfo = HViolas.GetSSOUserInfo(params["wallet_address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if userInfo is None:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    if userInfo["phone_number"] is None:
        return MakeResp(ErrorCode.ERR_PHONE_NUMBER_UNBOUND)

    if not VerifyCodeExist(userInfo["phone_local_number"] + userInfo["phone_number"], params["phone_verify_code"]):
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)

    if userInfo["email_address"] is None:
        return MakeResp(ErrorCode.ERR_EMAIL_UNBOUND)

    if not VerifyCodeExist(userInfo["email_address"], params["email_verify_code"]):
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)

    succ, result = HViolas.AddSSOInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if result:
        return MakeResp(ErrorCode.ERR_OK)
    else:
        return MakeResp(ErrorCode.ERR_TOKEN_NAME_DUPLICATE)

@app.route("/1.0/violas/sso/token/status")
def GetTokenApprovalStatus():
    address = request.args.get("address")
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 10, type = int)
    address = address.lower()

    succ, info = HViolas.GetSSOApprovalStatus(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    if info["approval_status"] == 0:
        timestamp = int(time.time())
        if timestamp > info["expiration_date"]:
            info["approval_status"] = -1
            HViolas.SetApprovalStatus(info["id"], -1)

    data = {"id": info["id"],
            "token_name": info["token_name"] + info["token_type"],
            "approval_status": info["approval_status"],
            "token_id": info["token_id"]}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/sso/token")
def GetTokenDetailInfo():
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetTokenDetailInfo(address)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    if info["account_info_photo_positive_url"] is not None:
        info["account_info_photo_positive_url"] = PHOTO_URL + info["account_info_photo_positive_url"]

    if info["account_info_photo_back_url"] is not None:
        info["account_info_photo_back_url"] = PHOTO_URL + info["account_info_photo_back_url"]

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    if info["approval_status"] == 0:
        timestamp = int(time.time())
        if timestamp > info["expiration_date"]:
            info["approval_status"] = -1
            HViolas.SetApprovalStatus(info["id"], -1)

    if info["approval_status"] == -2:
        info["failed_reason"] = GovernorFailedReason[info["failed_reason"]]
    if info["approval_status"] == -3:
        info["failed_reason"] = ChairmanFailedReason[info["failed_reason"]]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/sso/token/status/publish", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.SetTokenPublished(params["address"], params["id"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/governors")
def GetGovernors():
    succ, infos = HViolas.GetGovernorInfoForSSO()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

# GOVERNOR
@app.route("/1.0/violas/governor/<address>")
def GetGovernorInfoAboutAddress(address):
    address = address.lower()

    succ, info = HViolas.GetGovernorInfoAboutAddress(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.1/violas/governor", methods=["POST"])
def AddGovernorInfoV2():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddGovernorInfoForFrontEnd(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["POST"])
def AddInvestmentInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["PUT"])
def MakeInvestmentHandled():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/status/published", methods = ["PUT"])
def MakeGovernorStatusToPublished():
    params = request.get_json()
    params["is_handle"] = 3
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/token/status")
def GetUnapprovalTokenInfoList():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetGovernorInfoAboutAddress(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    if info["status"] != 4:
        return MakeResp(ErrorCode.ERR_VSTAKE)

    succ, infos = HViolas.GetUnapprovalSSOList(address, limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for info in infos:
        if info["approval_status"] == 0:
            timestamp = int(time.time())
            if timestamp > info["expiration_date"]:
                info["approval_statsu"] = -1
                HViolas.SetApprovalStatus(info["id"], -1)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/governor/token")
def GetUnapprovalTokenDetailInfo():
    address = request.args.get("address")
    id = request.args.get("id", type = int)
    address = address.lower()

    succ, info = HViolas.GetUnapprovalTokenDetailInfo(address, id)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    if info["account_info_photo_positive_url"] is not None:
        info["account_info_photo_positive_url"] = PHOTO_URL + info["account_info_photo_positive_url"]

    if info["account_info_photo_back_url"] is not None:
        info["account_info_photo_back_url"] = PHOTO_URL + info["account_info_photo_back_url"]

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    if info["approval_status"] == 0:
        timestamp = int(time.time())
        if timestamp > info["expiration_date"]:
            info["approval_status"] = -1
            HViolas.SetApprovalStatus(info["id"], -1)

    if info["approval_status"] == -2:
        info["failed_reason"] = GovernorFailedReason[info["failed_reason"]]
    if info["approval_status"] == -3:
        info["failed_reason"] = ChairmanFailedReason[info["failed_reason"]]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor/token/status", methods = ["PUT"])
def ModifyApprovalStatusV2():
    params = request.get_json()

    if params["status"] > 0:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"])
    else:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"], params["reason"], params["remarks"])

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not info:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/vstake/address")
def GetVstakeAddress():
    succ, address = HViolas.GetVstakeModuleAddress()

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if address is None:
        return MakeResp(ErrorCode.ERR_VSTAKE_ADDRESS)

    data = {"address": address}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/governor/authority")
def CheckGovernorAuthority():
    address = request.args.get("address")
    module = request.args.get("module")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        result = cli.get_balance(address, module)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if result != 1:
        data = {"authority": 0}
        return MakeResp(ErrorCode.ERR_OK, data)

    data = {"authority": 1}
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/governor/singin", methods = ["POST"])
def VerifySinginSessionID():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.CheckBind(params["address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_CHAIRMAN_UNBIND)

    succ, info = HViolas.GetGovernorInfoAboutAddress(params["address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    value = rdsAuth.get("SessionID")

    if value is None:
        return MakeResp(ErrorCode.ERR_SINGIN_TIMEOUT)

    data = hashlib.sha3_256()
    data.update(value)

    verify_key = nacl.signing.VerifyKey(info["violas_public_key"], encoder=nacl.encoding.HexEncoder)
    try:
        verify_key.verify(data.hexdigest(), params["session_id"], encoder=nacl.encoding.HexEncoder)
    except nacl.exceptions.BadSignatureError:
        rdsAuth.set("SessionID", "Failed")
        return MakeResp(ErrorCode.ERR_SIG_ERROR)

    rdsAuth.set("SessionID", "Success")
    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/reason")
def GetGovernorFailReason():
    return MakeResp(ErrorCode.ERR_OK, GovernorFailedReason)

# CHAIRMAN
@app.route("/1.0/violas/chairman", methods = ["POST"])
def AddGovernorInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddGovernorInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/governors")
def GetGovernorInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    succ, infos = HViolas.GetGovernorInfoList(offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/chairman/governors/investmented")
def GetGovernorInvestmentInfo():
    succ, info = HViolas.GetInvestmentedGovernorInfo()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/chairman/investment/status", methods = ["PUT"])
def SetGovernorInvestmentStatus():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.SetGovernorStatus(params["wallet_address"], params["is_handle"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/governor/transactions")
def GetTransactionsAboutGovernor():
    address = request.args.get("address")
    limit = request.args.get("limit", default = 10, type = int)
    start_version = request.args.get("start_version", default = 0, type = int)
    address = address.lower()

    succ, datas = HViolas.GetTransactionsAboutGovernor(address, start_version, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/chairman/bind/governor", methods = ["POST"])
def ChairmanBindGovernor():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.ChairmanBindGovernor(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/singin/qrcode")
def GetSinginQRCodeInfo():
    bSessionId = os.urandom(32)

    data = {}
    data["timestamp"] = int(time.time())
    data["expiration_time"] = 60
    qr = {}
    qr["type"] = 1
    qr["session_id"] = bSessionId.hex()
    data["qr_code"] = qr
    rdsAuth.setex("SessionID", 60, bSessionId.hex())

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/chairman/singin/status")
def GetSinginStatus():
    value = rdsAuth.get("SessionID")
    if value is None:
        data = {"status": 3}
        return MakeResp(ErrorCode.ERR_OK, data)

    et = rdsAuth.ttl("SessionID")
    if et != -1:
        data = {"status": 0}
        return MakeResp(ErrorCode.ERR_OK, data)

    if str(value, "utf-8") == "Success":
        data = {"status": 1}
    else:
        data = {"status": 2}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/chairman/token/status")
def GetUnapprovalTokenInfoListFromGovernor():
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 0, type = int)

    succ, infos = HViolas.GetUnapprovalSSOListForChairman(offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/chairman/token")
def GetUnapprovalTokenDetailInfoFromGovernor():
    address = request.args.get("address")
    id = request.args.get("id", type = int)
    address = address.lower()

    succ, info = HViolas.GetTokenDetailInfoForChairman(address, id)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/chairman/token/status", methods = ["PUT"])
def ChairmanSetTokenStatus():
    params = request.get_json()

    if params["status"] > 0:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"])
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        succ, info = HViolas.SetTokenID(params["id"], params["token_id"])
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"], params["reason"], params["remarks"])

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/reason")
def GetChairmanFailReason():
    return MakeResp(ErrorCode.ERR_OK, ChairmanFailedReason)

# EXPLORER
@app.route("/explorer/libra/recent")
def LibraGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, datas = HLibra.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/explorer/libra/recent/<currency>")
def LibraGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HLibra.GetRecentTransactionAboutCurrency(limit, offset, module)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/libra/address/<address>")
def LibraGetAddressInfo(address):
    currency = request.args.get("currency")
    limit = request.args.get("limit", 10, type = int)
    offset = request.args.get("offset", 0, type = int)
    address = address.lower()

    succ, addressInfo = HLibra.GetAddressInfo(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if addressInfo is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    cli = MakeLibraClient()
    try:
        result = cli.get_balances(address)
        print(result)
        balances = []
        for key, value in result.items():
            item = {}
            item["name"] = key
            item["balance"] = value
            if key == "Coin1":
                showName = "USD"
            elif key == "Coin2":
                showName = "EUR"
            else:
                showName = key

            item["show_name"] = key
            item["show_icon"] = f"{ICON_URL}libra.png"

            balances.append(item)

        addressInfo["balance"] = balances
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if currency is None:
        succ, addressTransactions = HLibra.GetTransactionsByAddress(address, limit, offset)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, addressTransactions = HLibra.GetTransactionsByAddressAboutCurrency(address, limit, offset, currency)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = {}
    data["status"] = addressInfo
    data["transactions"] = addressTransactions

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/libra/version/<int:version>")
def LibraGetTransactionsByVersion(version):
    succ, transInfo = HLibra.GetTransactionByVersion(version)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, transInfo)

@app.route("/explorer/violas/recent")
def ViolasGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HViolas.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/recent/<currency>")
def ViolasGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HViolas.GetRecentTransactionAboutCurrency(limit, offset, currency)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/address/<address>")
def ViolasGetAddressInfo(address):
    currency = request.args.get("currency")
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 10, type = int)
    address = address.lower()

    succ, addressInfo = HViolas.GetAddressInfo(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if addressInfo is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    cli = MakeViolasClient()
    try:
        result = cli.get_balances(address)
        print(result)
        balances = []
        for key, value in result.items():
            item = {}
            item["name"] = key
            item["balance"] = value
            item["show_name"] = key[3:] if len(key) > 3 else key
            item["show_icon"] = f"{ICON_URL}violas.png"

            balances.append(item)

        addressInfo["balance"] = balances
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if currency is None:
        succ, addressTransactions = HViolas.GetTransactionsByAddress(address, limit, offset)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, addressTransactions = HViolas.GetTransactionsByAddressAboutCurrency(address, limit, offset, currency)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = {}
    data["status"] = addressInfo
    data["transactions"] = addressTransactions

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/version/<int:version>")
def ViolasGetTransactionsByVersion(version):
    succ, transInfo = HViolas.GetTransactionByVersion(version)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, transInfo)

@app.route("/explorer/violas/singin/qrcode")
def GetSinginSessionID():
    bSessionId = os.urandom(32)

    data = {}
    data["timestamp"] = int(time.time())
    data["expiration_time"] = 60
    qr = {}
    qr["type"] = 2
    qr["session_id"] = bSessionId.hex()
    data["qr_code"] = qr
    rdsAuth.setex(bSessionId.hex(), 60, json.JSONEncoder().encode({"status": "unknow"}))

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/singin")
def GetExplorerSinginStatus():
    sessionid = request.args.get("session_id")
    if sessionid is None:
        return MakeResp(ErrorCode.ERR_NEED_REQUEST_PARAM)

    value = rdsAuth.get(sessionid)

    if value is None:
        data = {"status": 3}
        return MakeResp(ErrorCode.ERR_OK, data)

    et = rdsAuth.ttl(sessionid)
    if et != -1:
        data = {"status": 0}
        return MakeResp(ErrorCode.ERR_OK, data)

    v = json.loads(str(value, "utf-8"))

    if v["status"] == "Success":
        data = {"status": 1, "wallets": v["wallets"]}
        rdsAuth.delete(sessionid)
    else:
        data = {"status": 2}
        rdsAuth.delete(sessionid)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/faucet")
def FaucetCoin():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_prefix")
    currency = request.args.get("currency")
    address = address.lower()

    # wallet = Wallet.recover(WalletRecoverFile)
    # account = wallet.accounts[0]

    cli = MakeViolasClient()

    cli.mint_coin(address, 100000, is_blocking = True, auth_key_prefix = authKey ,currency_code = currency)

    return MakeResp(ErrorCode.ERR_OK)

# corss chain
@app.route("/1.0/crosschain/address")
def GetAddressOfCrossChainTransaction():
    addressName = request.args.get("type")

    address = rdsCoinMap.hget(addressName, "address").decode("utf8")
    return MakeResp(ErrorCode.ERR_OK, address)

@app.route("/1.0/crosschain/module")
def GetModuleOfCrossChainTransaction():
    moduleName = request.args.get("type")

    module = rdsCoinMap.hget(moduleName, "id").decode("utf8")
    return MakeResp(ErrorCode.ERR_OK, module)

@app.route("/1.0/crosschain/rate")
def GetRateOfCrossChainTransaction():
    exchangeName = request.args.get("type")

    data = {}
    data["exchange_name"] = exchangeName
    data["exchange_rate"] = int(rdsCoinMap.hget(exchangeName, "rate").decode("utf8"))

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/crosschain/transactions/count")
def GetCountOfCrossChainTransaction():
    transactionType = request.args.get("type")
    address = request.args.get("address")
    address = address.lower()

    exchangeAddress = rdsCoinMap.hget(transactionType, "address").decode("utf8")
    exchangeModule = int(rdsCoinMap.hget(transactionType, "id").decode("utf8"))

    if transactionType == "vbtc" or transactionType == "vlibra":
        succ, count = HViolas.GetExchangeTransactionCountFrom(address, exchangeAddress, exchangeModule)
    elif transactionType == "btc" or transactionType == "libra":
        succ, count = HViolas.GetExchangeTransactionCountTo(address, exchangeAddress, exchangeModule)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, count)

@app.route("/1.0/crosschain/info")
def GetMapInfoOfCrossChainTransaction():
    coinType = request.args.get("type")

    info = {}
    info["name"] = rdsCoinMap.hget(coinType, "map_name").decode("utf8")
    info["address"] = rdsCoinMap.hget(coinType, "address").decode("utf8")
    info["token_id"] = int(rdsCoinMap.hget(coinType, "id").decode("utf8"))
    info["rate"] = int(rdsCoinMap.hget(coinType, "rate").decode("utf8"))

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/crosschain/transactions")
def GetCrossChainTransactionInfo():
    address = request.args.get("address")
    walletType = request.args.get("type", 0, int)
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = address.lower()

    url = "http://52.231.52.107/?opt=record"
    if walletType == 0:
        wallet = "violas"
    elif walletType == 1:
        wallet = "libra"
    elif walletType == 2:
        wallet = "btc"
    else:
        return MakeResp(ErrorCode.ERR_UNKNOW_WALLET_TYPE)

    url = f"{url}&chain={wallet}&cursor={offset}&limt={limit}&sender={address}"

    resp = requests.get(url)
    respInfos = resp.json()["datas"]

    data = {}
    data["offset"] = respInfos["cursor"]
    infos = []
    for i in respInfos["datas"]:
        info = {}
        if i["state"] == "start":
            info["status"] = 0
        elif i["state"] == "end":
            info["status"] = 1
        else:
            info["status"] = 2

        info["address"] = i["to_address"][32:64]
        info["amount"] = i["amount"]

        if i["type"] == "V2B":
            info["coin"] = "btc"
        elif i["type"] == "V2L":
            info["coin"] = "libra"
        elif i["type"] == "B2V":
            info["coin"] = "vbtc"
        elif i["type"] == "L2V":
            info["coin"]= "vlibra"

        info["date"] = i.get("expiration_time") if i.get("expiration_time") is not None else 0

        infos.append(info)

    data["infos"] = infos

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/crosschain/transactions/btc", methods = ["POST"])
def ForwardBtcTransaction():
    params = request.get_json()
    rawHex = params["rawhex"]

    resp = requests.post("https://tchain.api.btc.com/v3/tools/tx-publish", params = {"rawhex": rawHex})
    if resp.json()["err_no"] != 0:
        logging.error(f"ERROR: Forward BTC request failed, msg: {resp.json()['error_msg']}")
        return MakeResp(ErrorCode.ERR_BTC_FORWARD_REQUEST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/crosschain/modules")
def GetMapedCoinModules():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        info = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if not info.exists():
        return MakeResp(ErrorCode.ERR_ACCOUNT_DOES_NOT_EXIST)
    modus = []
    try:
        for key in info.get_scoin_resources(ContractAddress).tokens:
            modus.append(key)
    except:
        return MakeResp(ErrorCode.ERR_OK, [])

    infos = []
    coins = ["vbtc", "vlibra"]
    for coin in coins:
        if int(rdsCoinMap.hget(coin, "id").decode("utf8")) in modus:
            info = {}
            info["name"] = coin
            info["address"] = rdsCoinMap.hget(coin, "address").decode("utf8")
            info["token_id"] = int(rdsCoinMap.hget(coin, "id").decode("utf8"))
            info["map_name"] = rdsCoinMap.hget(coin, "map_name").decode("utf8")
            info["rate"] = int(rdsCoinMap.hget(coin, "rate").decode("utf8"))

            infos.append(info)

    return MakeResp(ErrorCode.ERR_OK, infos)

# BTC
@app.route("/1.0/btc/balance")
def GetBtcBalance():
    address = request.args.get("address")

    reqUrl = f"https://btc1.trezor.io/api/v2/address/{address}"
    resp = requests.get(reqUrl)

    balance = resp.json()["balance"]

    data = [{"BTC": balance, "name": "BTC", "show_name": "BTC", "show_icon": f"{ICON_URL}btc.png"}]
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/btc/transaction", methods = ["POST"])
def BroadcastBtcTransaction():
    params = request.get_json()
    rawHex = params["rawhex"]

    resp = requests.post("https://btc1.trezor.io/api/v2/sendtx", params = {"rawhex": rawHex})
    if resp.json().get("error") is not None:
        logging.error(f"ERROR: Forward BTC request failed, msg: {resp.json()['error']['message']}")
        return MakeResp(ErrorCode.ERR_BTC_FORWARD_REQUEST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/btc/utxo")
def GetBtcUTXO():
    address = request.args.get("address")
    reqUrl = f"https://btc1.trezor.io/api/v2/utxo/{address}"
    resp = requests.get(reqUrl)

    return MakeResp(ErrorCode.ERR_OK, resp.json())

# MARKET
@app.route("/1.0/market/exchange/currency")
def GetMarketExchangeCurrencies():
    cli = MakeExchangeClient()

    try:
        currencies = cli.swap_get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception=e)

    if currencies is None:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "There is no currency has registered!")

    filtered = {}
    filtered["violas"] = []
    filtered["libra"] = []
    filtered["btc"] = []
    for i in currencies:
        if i[0:3] == "VLS":
            cInfo = {}
            cInfo["name"] = i
            cInfo["module"] = i
            cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
            cInfo["show_name"] = i
            cInfo["index"] = currencies.index(i)
            cInfo["icon"] = f"{ICON_URL}violas.png"
            filtered["violas"].append(cInfo)
        elif i == "BTC":
            cInfo = {}
            cInfo["name"] = i
            cInfo["module"] = i
            cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
            cInfo["show_name"] = i
            cInfo["index"] = currencies.index(i)
            cInfo["icon"] = f"{ICON_URL}btc.png"
            filtered["btc"].append(cInfo)
        else:
            cInfo = {}
            cInfo["name"] = i
            cInfo["module"] = i
            cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
            cInfo["show_name"] = i
            cInfo["index"] = currencies.index(i)
            cInfo["icon"] = f"{ICON_URL}libra.png"
            filtered["libra"].append(cInfo)

    return MakeResp(ErrorCode.ERR_OK, filtered)

@app.route("/1.0/market/exchange/trial")
def GetExchangeTrial():
    amount = request.args.get("amount", type = int)
    currencyIn = request.args.get("currencyIn")
    currencyOut = request.args.get("currencyOut")

    cli = MakeExchangeClient()
    try:
        amountOut = cli.swap_get_swap_output_amount(currencyIn, currencyOut, amount)
        path = cli.get_currency_max_output_path(currencyIn, currencyOut, amount)
    except AssertionError:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "Exchange path too deep!")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"amount": amountOut[0],
            "fee": amountOut[1],
            "rate": amount / amountOut[0] if amountOut[0] > 0 else 0,
            "path": path}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/exchange/transaction")
def GetMarketExchangeTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, infos = HViolas.GetMarketExchangeTransaction(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/market/exchange/crosschain/address/info")
def GetMarketCrosschainMapInfo():
    baseMapInfos = [
        {
            "type": "v2b",
            "chain": "violas",
            "address": "4f93ec275410e8be891ff0fd5da41c43aee27591e222fb466654b4f983d8adbb"
        },
        {
            "type": "v2lusd",
            "chain": "violas",
            "address": "7cd40d7664d5523d360e8a1e0e2682a2dc49a7c8979f83cde4bc229fb35fd27f"
        },
        {
            "type": "v2leur",
            "chain": "violas",
            "address": "a239632a99a92e38eeade27b5e3023e22ab774f228b719991463adf0515688a9"
        },
        {
            "type": "l2vusd",
            "chain": "libra",
            "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
        },
        {
            "type": "l2veur",
            "chain": "libra",
            "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
        },
        {
            "type": "l2vgbp",
            "chain": "libra",
            "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
        },
        {
            "type": "l2vsgd",
            "chain": "libra",
            "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
        }
    ]

    data = []
    for i in baseMapInfos:
        flow = i["type"][0:3]
        cIn, cOut = flow.split("2")
        currency = i["type"][3:] if len(i["type"]) > 3 else None

        item = {}
        item["lable"] = i["type"]
        item["input_coin_type"] = i["chain"]
        item["receiver_address"] = i["address"]

        if cOut == "v":
            coinType = "violas"
            assets = {"module": "VLS" + currency.upper(),
                      "address": VIOLAS_CORE_CODE_ADDRESS.hex(),
                      "name": "VLS" + currency.upper()}
        elif cOut == "l":
            coinType = "libra"
            assets = {"module": currency.upper(),
                      "address": VIOLAS_CORE_CODE_ADDRESS.hex(),
                      "name": currency.upper()}
        elif cOut == "b":
            coinType = "btc"
            assets = {"module": "BTC",
                      "address": VIOLAS_CORE_CODE_ADDRESS.hex(),
                      "name": "BTC"}

        item["to_coin"] = {"coin_type": coinType,
                           "assets": assets}
        data.append(item)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/pool/info")
def GetPoolInfoAboutAccount():
    address = request.args.get("address")

    cli = MakeExchangeClient()

    try:
        currencies = cli.swap_get_registered_currencies()
        balance = cli.swap_get_liquidity_balances(address)
    except AttributeError as e:
        return MakeResp(ErrorCode.ERR_OK, {})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    total = 0
    balancePair = []
    for i in balance:
        item = {}
        for k, v in i.items():
            if k == "liquidity":
                item["token"] = v
                total += v
            else:
                if item.get("coin_a_name") is None:
                    item["coin_a_name"] = k
                    item["coin_a_value"] = v
                    item["coin_a_index"] = currencies.index(k)
                else:
                    item["coin_b_name"] = k
                    item["coin_b_value"] = v
                    item["coin_b_index"] = currencies.index(k)

        balancePair.append(item)

    data = {}
    data["total_token"] = total
    data["balance"] = balancePair
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/pool/deposit/trial")
def GetPoolCurrencyRate():
    amount = request.args.get("amount", type = int)
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        amountB = cli.swap_get_liquidity_output_amount(coinA, coinB, amount)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, {"amount": amountB, "rate": float(amount) / amountB})

@app.route("/1.0/market/pool/withdrawal/trial")
def GetPoolWithdrawalTrial():
    address = request.args.get("address")
    tokenAmount = request.args.get("amount", type = int)
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        balance = cli.swap_get_liquidity_balances(address)
        for i in balance:
            if coinA in i and coinB in i:
                if tokenAmount > i["liquidity"]:
                    return MakeResp(ErrorCode.ERR_OK, {})
                else:
                    break
            else:
                continue

        trialResult = cli.swap_get_liquidity_out_amounts(coinA, coinB, tokenAmount)
        item = {"coin_a_name": coinA, "coin_a_value": trialResult[0],
                "coin_b_name": coinB, "coin_b_value": trialResult[1]}
    except AttributeError as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "No funds in pool!")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, item)

@app.route("/1.0/market/pool/transaction")
def GetMarketPoolTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, infos = HViolas.GetMarketPoolTransaction(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/market/pool/reserve/info")
def GetReserve():
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        currencies = cli.swap_get_registered_currencies()
        indexA = currencies.index(coinA)
        indexB = currencies.index(coinB)
        reserves = cli.swap_get_reserves_resource()
        reserve = cli.get_reserve(reserves, indexA, indexB)
    except ValueError:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "Coin not exist.")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception=e)
    reserve = json.loads(reserve.to_json())
    reserve["coina"]["name"] = currencies[reserve["coina"]["index"]]
    reserve["coinb"]["name"] = currencies[reserve["coinb"]["index"]]

    return MakeResp(ErrorCode.ERR_OK, reserve)
