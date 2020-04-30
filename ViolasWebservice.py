import os, random, logging, configparser, datetime, json, time
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from redis import Redis
import requests
import nacl.signing
import hashlib

from violas import Client as ViolasClient
from violas.error.error import ViolasError

from libra_client import Client as LibraClient
from libra_client.error.error import LibraError

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

def MakeLibraClient():
    return LibraClient("libra_testnet")

def MakeViolasClient():
    return ViolasClient.new(config["NODE INFO"]["VIOLAS_HOST"], int(config["NODE INFO"]["VIOLAS_PORT"]), faucet_file = "./mint_external.key")

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

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except LibraError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, seqNum)

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
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    succ, datas = HLibra.GetTransactionsForWallet(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/libra/mint")
def MintLibraToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")

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
    modules = request.args.get("modu", "")

    cli = MakeViolasClient()
    try:
        accState = cli.get_account_state(address)
        info = {}
        info["address"] = address
        info["balance"] = accState.get_balance()
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)


    if len(modules) != 0:
        moduleState = cli.get_account_state(ContractAddress)

        modulesBalance = []
        moduleList = modules.split(",")
        for i in moduleList:
            try:
                result = cli.get_balance(address, int(i), ContractAddress)
            except ViolasError as e:
                return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

            moduleInfo = {}
            moduleInfo["id"] = int(i)
            moduleInfo["name"] = moduleState.get_token_data(int(i), ContractAddress)
            moduleInfo["balance"] = result

            modulesBalance.append(moduleInfo)

        info["modules"] = modulesBalance

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")

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
    token_id = request.args.get("modu")
    limit = request.args.get("limit", 10, int)
    offset = request.args.get("offset", 0, int)

    if token_id is None:
        module = "00000000000000000000000000000000"
    else:
        module = ContractAddress

    print(module)
    vbtcTokenId = int(rdsCoinMap.hget("vbtc", "id").decode("utf8"))
    vlibraTokenId = int(rdsCoinMap.hget("vlibra", "id").decode("utf8"))

    moduleMap = {vbtcTokenId: "vbtc",
                 vlibraTokenId: "vlibra"}

    succ, datas = HViolas.GetTransactionsForWallet(address, module, token_id, offset, limit, moduleMap)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/currency")
def GetCurrency():
    cli = MakeViolasClient()

    try:
        info = cli.get_account_state(ContractAddress)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    if not info.exists():
        return MakeResp(ErrorCode.ERR_ACCOUNT_DOES_NOT_EXIST)

    currencies = []
    tokenNum = info.get_scoin_resources(ContractAddress).get_token_num()

    for i in range(tokenNum):
        name = info.get_token_data(i, ContractAddress)
        tokenInfo = {"id": i, "name": name}
        currencies.append(tokenInfo)

    data = {"module": ContractAddress, "currencies": currencies}
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/module")
def CheckMoudleExise():
    addr = request.args.get("addr")

    cli = MakeViolasClient()

    try:
        info = cli.get_account_state(addr)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    if not info.exists():
        return MakeResp(ErrorCode.ERR_ACCOUNT_DOES_NOT_EXIST)

    if info.is_published(ContractAddress):
        data = {"is_published": 1}
    else:
        data = {"is_published": 0}

    return MakeResp(ErrorCode.ERR_OK, data)

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

    value = rdsAuth.get(params["session_id"])

    if value is None:
        return MakeResp(ErrorCode.ERR_SESSION_NOT_EXIST)

    data = {"status": "Success", "wallets":params["wallets"]}

    rdsAuth.set(params["session_id"], json.JSONEncoder().encode(data))

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/mint")
def MintViolasToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")

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

    cli = MakeViolasClient()

    try:
        state = cli.get_account_state(address)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_authentication_key(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_delegated_key_rotation_capability(),
            "delegated_withdrawal_capability": state.get_delegated_withdrawal_capability(),
            "delegated_withdrawal_capability": state.get_delegated_withdrawal_capability(),
            "received_events_key": state.get_received_events_key(),
            "sent_events_key": state.get_sent_events_key()}

    return MakeResp(ErrorCode.ERR_OK, data)

# VBTC
@app.route("/1.0/violas/vbtc/transaction")
def GetVBtcTransactionInfo():
    receiverAddress = request.args.get("receiver_address")
    moduleAddress = request.args.get("module_address")
    startVersion = request.args.get("start_version", type = int)

    succ, datas = HViolas.GetTransactionsAboutVBtc(receiverAddress, moduleAddress, startVersion)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/vbtc/transaction", methods = ["POST"])
def VerifyVBtcTransactionInfo():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    succ, result = HViolas.VerifyTransactionAboutVBtc(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_VBTC_TRANSACTION_INFO)

    return MakeResp(ErrorCode.ERR_OK)

# SSO
@app.route("/1.0/violas/sso/user")
def GetSSOUserInfo():
    address = request.args.get("address")

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

@app.route("/1.0/violas/sso/user", methods = ["POST"])
def SSOUserRegister():
    params = request.get_json()

    succ, result = HViolas.AddSSOUser(params["wallet_address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ, result = HViolas.UpdateSSOUserInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token")
def GetTokenApprovalStatus():
    address = request.args.get("address")

    succ, info = HViolas.GetSSOApprovalStatus(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()

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

@app.route("/1.0/violas/sso/token", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()

    succ, result = HViolas.SetTokenPublished(params["address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/bind", methods = ["POST"])
def BindUserInfo():
    params = request.get_json()
    receiver = params["receiver"]
    verifyCode = params["code"]
    address = params["address"]
    local_number = params.get("phone_local_number")

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

@app.route("/1.0/violas/sso/token/approval")
def GetUnapprovalTokenInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = request.args.get("address")

    succ, infos = HViolas.GetUnapprovalSSO(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.1/violas/sso/token/approval")
def GetUnapprovalTokenInfoList():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = request.args.get("address")

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

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/sso/token/approval/<int:id>")
def GetUnapprovalTokenDetailInfo(id):
    succ, info = HViolas.GetUnapprovalSSOInfo(id)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    if info["account_info_photo_positive_url"] is not None:
        info["account_info_photo_positive_url"] = PHOTO_URL + info["account_info_photo_positive_url"]

    if info["account_info_photo_back_url"] is not None:
        info["account_info_photo_back_url"] = PHOTO_URL + info["account_info_photo_back_url"]

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/sso/token/approval", methods = ["PUT"])
def ModifyApprovalStatus():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    succ, result = HViolas.SetMintInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.1/violas/sso/token/approval", methods = ["PUT"])
def ModifyApprovalStatusV2():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    succ, result = HViolas.SetMintInfoV2(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token/minted", methods = ["PUT"])
def SetTokenMinted():
    params = request.get_json()

    succ, result = HViolas.SetTokenMinted(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.1/violas/sso/token/minted", methods = ["PUT"])
def SetTokenMintedByID():
    params = request.get_json()

    succ, result = HViolas.SetTokenMintedV2(params)
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
@app.route("/1.0/violas/governor")
def GetGovernorInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    succ, infos = HViolas.GetGovernorInfo(offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/governor/<address>")
def GetGovernorInfoAboutAddress(address):
    succ, info = HViolas.GetGovernorInfoAboutAddress(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor", methods = ["POST"])
def AddGovernorInfo():
    params = request.get_json()

    succ, result = HViolas.AddGovernorInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/sso", methods = ["POST"])
def AddGovernorInfoForSSOWallet():
    params = request.get_json()

    succ, result = HViolas.AddGovernorInfoForFrontEnd(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.1/violas/governor", methods=["POST"])
def AddGovernorInfoV2():
    params = request.get_json()

    succ, result = HViolas.AddGovernorInfoForFrontEnd(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    params = request.get_json()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment")
def GetGovernorInvestmentInfo():
    succ, info = HViolas.GetInvestmentedGovernorInfo()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor/investment", methods = ["POST"])
def AddInvestmentInfo():
    params = request.get_json()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["PUT"])
def MakeInvestmentHandled():
    params = request.get_json()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/transactions")
def GetTransactionsAboutGovernor():
    address = request.args.get("address")
    limit = request.args.get("limit", default = 10, type = int)
    start_version = request.args.get("start_version", default = 0, type = int)

    succ, datas = HViolas.GetTransactionsAboutGovernor(address, start_version, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

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

@app.route("/1.0/violas/governor/bind", methods = ["POST"])
def ChairmanBindGovernor():
    params = request.get_json()

    succ, result = HViolas.ChairmanBindGovernor(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/singin/qrcode")
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

@app.route("/1.0/violas/governor/singin")
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

@app.route("/1.0/violas/governor/singin", methods = ["POST"])
def VerifySinginSessionID():
    params = request.get_json()

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

    url = "http://18.136.139.151/?opt=record"
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

        info["address"] = i["to_address"]
        info["amount"] = i["amount"]

        if i["type"] == "V2B":
            info["coin"] = "btc"
        elif i["type"] == "V2L":
            info["coin"] = "libra"
        elif i["type"] == "B2V":
            info["coin"] = "vbtc"
        elif i["type"] == "L2V":
            info["coin"]= "vlibra"

        info["date"] = 1

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
