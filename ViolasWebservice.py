import os, random, logging, configparser, datetime, json, time, datetime
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from redis import Redis
import requests
import nacl.signing
import hashlib

from libra_client import Client as LibraClient
from libra_client.error import LibraError

from violas_client import Client as ViolasClient
from violas_client.error import LibraError as ViolasError

from violas_client import Wallet

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
WalletRecoverFile = "./account_recovery"

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
    return ViolasClient.new(config['NODE INFO']['VIOLAS_HOST'], faucet_file = "./mint_test.key")

def MakeResp(code, data = None, exception = None):
    resp = {}

    resp["code"] = code
    if exception is not None:
        resp["message"] = f"Node runtime error: {exception.msg}"
    else:
        resp["message"] = ErrorMsg[code]

    if data is not None:
        resp["data"] = data

    return resp

# LIBRA WALLET
@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        result = cli.get_balance(address)
        info = {}
        info["address"] = address
        info["balance"] = result
        return MakeResp(ErrorCode.ERR_OK, info)
    except LibraError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

@app.route("/1.0/libra/seqnum")
def GetLibraSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
        info = {"address": address, "seqnum": seqNum}
        return MakeResp(ErrorCode.ERR_OK, info)
    except LibraError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeLibraClient()
    try:
        cli.submit_signed_transaction(signedtxn, True)
    except LibraError as e:
        if e.code == 6011:
            return MakeResp(ErrorCode.ERR_GRPC_CONNECT)
        else:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    flows = request.args.get("flows", type = int)
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)
    address = address.lower()

    succ, datas = HLibra.GetTransactionsForWallet(address, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/libra/mint")
def MintLibraToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        cli.mint_coin(address, 100, is_blocking = True, receiver_auth_key_prefix_opt = authKey)
    except LibraError as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)
    except ValueError:
        return MakeResp(ErrorCode.ERR_INVAILED_ADDRESS)

    return MakeResp(ErrorCode.ERR_OK)

# VIOLAS WALLET
@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeViolasClient()
    try:
        if currency is None:
            balance = cli.get_balances(address)
            data = {"balances": balance}
        else:
            balance = cli.get_balance(address, currency)
            data = {"balances": {currency: balance}}
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeViolasClient()
    try:
        seqNum = cli.get_account_sequence_number(address)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, seqNum)

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeViolasClient()

    try:
        cli.submit_signed_transaction(signedtxn, True)
    except ViolasError as e:
        if e.code == 6011:
            return MakeResp(ErrorCode.ERR_GRPC_CONNECT)
        else:
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

    vbtcTokenId = int(rdsCoinMap.hget("vbtc", "id").decode("utf8"))
    vlibraTokenId = int(rdsCoinMap.hget("vlibra", "id").decode("utf8"))

    succ, datas = HViolas.GetTransactionsForWallet(address, currency, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/currency")
def GetCurrency():
    cli = MakeViolasClient()

    try:
        currencies = cli.get_registered_currencies()
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, {"currencies": currencies})

@app.route("/1.0/violas/currency/published")
def CheckCurrencyPublished():
    addr = request.args.get("addr")
    addr = addr.lower()

    cli = MakeViolasClient()

    try:
        balances = cli.get_balances(addr)
        print(balances)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

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

    return MakeResp(ErrorCode.ERR_OK, uuid)

@app.route("/1.0/violas/verify_code", methods = ["POST"])
def SendVerifyCode():
    params = request.get_json()
    receiver = params["receiver"]
    address = params["address"]
    verifyCode = random.randint(100000, 999999)
    local_number = params.get("phone_local_number")
    receiver = receiver.lower()
    address = address.lower()

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

def VerifyCodeExist(receiver, code):
    value = rdsVerify.get(receiver)

    if value is None:
        return False
    elif value.decode("utf8") != str(code):
        return False

    rdsVerify.delete(receiver)

    return True

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
    address = address.lower()
    authKey = authKey.lower()

    cli = MakeViolasClient()
    try:
        cli.mint_coin(address, 100, is_blocking = True, auth_key_prefix = authKey)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)
    except ValueError:
        return MakeResp(ErrorCode.ERR_INVAILED_ADDRESS)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/account/info")
def GetAccountInfo():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        state = cli.get_account_state(address)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_account_resource().get_authentication_key(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_account_resource().get_delegated_key_rotation_capability(),
            "delegated_withdrawal_capability": state.get_account_resource().get_delegated_withdrawal_capability(),
            "received_events_key": state.get_account_resource().get_received_events().get_key(),
            "sent_events_key": state.get_account_resource().get_sent_events().get_key()}


    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/rates")
def GetRates():
    yesterday = datetime.date.fromtimestamp(time.time() - 24 * 60 * 60)
    today = datetime.date.today()
    start = f"{yesterday.year}-{yesterday.month if yesterday.month > 9 else '0' + str(yesterday.month)}-{yesterday.day if yesterday.day > 9 else '0' + str(yesterday.day)}"
    end = f"{today.year}-{today.month if today.month > 9 else '0' + str(today.month)}-{today.day if today.day > 9 else '0' + str(today.day)}"
    url = f"https://api.exchangeratesapi.io/history?base=USD&start_at={start}&end_at={end}"
    resp = requests.get(url)
    rates = resp.json()["rates"][start]

    return MakeResp(ErrorCode.ERR_OK, rates)

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
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

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

@app.route("/explorer/libra/address/<address>")
def LibraGetAddressInfo(address):
    limit = request.args.get("limit", 10, type = int)
    offset = request.args.get("offset", 0, type = int)
    address = address.lower()

    succ, addressInfo = HLibra.GetAddressInfo(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeLibraClient()
    finish = 0
    while finish < 3:
        try:
            result = cli.get_balance(address)
            addressInfo["balance"] = result
            finish = 3
        except ViolasError as e:
            finish += 1

    succ, addressTransactions = HLibra.GetTransactionsByAddress(address, limit, offset)
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

@app.route("/explorer/violas/recent/<module>")
def ViolasGetRecentTxAboutToken(module):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HViolas.GetRecentTransactionAboutModule(limit, offset, module)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/address/<address>")
def ViolasGetAddressInfo(address):
    module = request.args.get("module")
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 10, type = int)
    address = address.lower()

    succ, addressInfo = HViolas.GetAddressInfo(address)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if addressInfo is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    cli = MakeViolasClient()
    moduleState = cli.get_account_state(ContractAddress)

    modulesBalance = []
    tokenNum = moduleState.get_scoin_resources(ContractAddress).get_token_num()
    for i in range(tokenNum):
        try:
            result = cli.get_balance(address, i, ContractAddress)
        except ViolasError as e:
            return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

        moduleInfo = {}
        moduleInfo["id"] = i
        moduleInfo["name"] = moduleState.get_token_data(i, ContractAddress)
        moduleInfo["balance"] = result

        modulesBalance.append(moduleInfo)

    addressInfo["balance"] = cli.get_balance(address)
    addressInfo["module_balande"] = modulesBalance

    if module is None:
        succ, addressTransactions = HViolas.GetTransactionsByAddress(address, limit, offset)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, addressTransactions = HViolas.GetTransactionsByAddressAboutModule(address, limit, offset, module)
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
    token_id = request.args.get("token_id", type = int)
    address = address.lower()

    wallet = Wallet.recover(WalletRecoverFile)
    account = wallet.accounts[0]

    cli = MakeViolasClient()

    if token_id is None:
        cli.transfer_coin(account, address, 1000)
    else:
        cli.transfer_coin(account, address, 1000, token_id, ContractAddress)

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
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

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
