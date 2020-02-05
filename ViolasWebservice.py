import os, random, logging, configparser, datetime, json
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from redis import Redis

from violas import Client
from violas.error.error import ViolasError
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
PHOTO_URL = "http://52.27.228.84:4000/1.0/violas/photo/"

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"
HLibra = LibraPGHandler(libraDBUrl)

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"
HViolas = ViolasPGHandler(violasDBUrl)

pushInfo = config["PUSH SERVER"]
pushh = PushServerHandler(pushInfo["HOST"], int(pushInfo["PORT"]))

cachingInfo = config["CACHING SERVER"]
rds = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["DB"], cachingInfo["PASSWORD"])

def MakeLibraClient():
    return Client("libra_testnet")

def MakeViolasClient():
    # return Client("violas_testnet")
    return Client.new(config["NODE INFO"]["VIOLAS_HOST"], config["NODE INFO"]["VIOLAS_PORT"])

def MakeResp(code, data = None, exception = None):
    resp = {}

    resp["code"] = code
    if exception is not None:
        resp["message"] = e.msg()
    else:
        resp["message"] = ErrorMsg[code]

    if data is not None:
        resp["data"] = data

    return resp

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
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    modules = request.args.get("modu", "")

    cli = MakeViolasClient()
    try:
        result = cli.get_balance(address)
        info = {}
        info["address"] = address
        info["balance"] = result
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    if len(modules) != 0:
        modulesBalance = []
        moduleList = modules.split(",")
        for i in moduleList:
            try:
                result = cli.get_balance(address, i)
            except ViolasError as e:
                return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

            print(result)
            moduleInfo = {}
            moduleInfo["address"] = i
            moduleInfo["balance"] = result

            modulesBalance.append(moduleInfo)

        info["modules"] = modulesBalance

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/libra/seqnum")
def GetLibraSequenceNumbert():
    address = request.args.get("addr")

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_account_sequence_number(address)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, seqNum)

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")

    cli = MakeViolasClient()
    try:
        seqNum = cli.get_account_sequence_number(address)
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_GRPC_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, seqNum)

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeLibraClient()
    try:
        cli.submit_signed_transaction(signedtxn, True)
    except ViolasError as e:
        if e.code() == 6011:
            return MakeResp(ErrorCode.ERR_GRPC_CONNECT)
        else:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeViolasClient()

    try:
        cli.submit_signed_transaction(signedtxn, True)
    except ViolasError as e:
        if e.code() == 6011:
            return MakeResp(ErrorCode.ERR_GRPC_CONNECT)
        else:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    datas = HLibra.GetTransactionsForWallet(address, offset, limit)
`
    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/transaction")
def GetViolasTransactionInfo():
    address = request.args.get("addr")
    module = request.args.get("modu", "0000000000000000000000000000000000000000000000000000000000000000")
    limit = request.args.get("limit", 10, int)
    offset = request.args.get("offset", 0, int)

    datas = HViolas.GetTransactionsForWallet(address, module, offset, limit)
    resp["data"] = datas

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/currency")
def GetCurrency():
    currencies = HViolas.GetCurrencies()

    resp["data"] = currencies
    return MakeResp(ErrorCode.ERR_OK, currencies)

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

    modus = []
    for key in info.get_scoin_resources():
        modus.append(key)

    return MakeResp(ErrorCode.ERR_OK, modus)

@app.route("/1.0/violas/vbtc/transaction")
def GetVBtcTransactionInfo():
    receiverAddress = request.args.get("receiver_address")
    moduleAddress = request.args.get("module_address")
    startVersion = request.args.get("start_version", type = int)

    datas = HViolas.GetTransactionsAboutVBtc(receiverAddress, moduleAddress, startVersion)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/vbtc/transaction", methods = ["POST"])
def VerifyVBtcTransactionInfo():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    if not HViolas.VerifyTransactionAboutVBtc(params):
        return MakeResp(ErrorCode.ERR_VBTC_TRANSACTION_INFO)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/user")
def GetSSOUserInfo():
    address = request.args.get("address")

    info = HViolas.GetSSOUserInfo(address)

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
    HViolas.AddSSOUser(params["wallet_address"])
    HViolas.UpdateSSOUserInfo(params)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token")
def GetTokenApprovalStatus():
    address = request.args.get("address")
    info = HViolas.GetSSOApprovalStatus(address)

    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()

    userInfo = HViolas.GetSSOUserInfo(params["wallet_address"])
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

    if HViolas.AddSSOInfo(params):
        return MakeResp(ErrorCode.ERR_OK)
    else:
        return MakeResp(ErrorCode.ERR_TOKEN_NAME_DUPLICATE)

@app.route("/1.0/violas/sso/token", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()
    HViolas.SetTokenPublished(params["address"])

    return MakeResp(ErrorCode.ERR_OK)

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

    HViolas.AddSSOUser(address)

    if receiver.find("@") >= 0:
        succ = pushh.PushEmailSMSCode(verifyCode, receiver, 5)
        rds.setex(receiver, 600, str(verifyCode))
    else:
        succ = pushh.PushPhoneSMSCode(verifyCode, local_number + receiver, 5)
        rds.setex(local_number + receiver, 600, str(verifyCode))

    if not succ:
        return MakeResp(ErrorCode.ERR_SEND_VERIFICATION_CODE)

    return MakeResp(ErrorCode.ERR_OK)

def VerifyCodeExist(receiver, code):
    value = rds.get(receiver)

    if value is None:
        return False
    elif value.decode("utf8") != str(code):
        return False

    rds.delete(receiver)

    return True

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
        resp["code"] = 2003
        resp["message"] = "Verify error!"
    else:
        data = {}
        data["wallet_address"] = address
        if receiver.find("@") >= 0:
            data["email_address"] = receiver
        else:
            data["phone_local_number"] = local_number
            data["phone_number"] = receiver

        HViolas.UpdateSSOUserInfo(data)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token/approval")
def GetUnapprovalTokenInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = request.args.get("address")

    infos = HViolas.GetUnapprovalSSO(address, offset, limit)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/sso/token/approval", methods = ["PUT"])
def ModifyApprovalStatus():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    if not HViolas.SetMintInfo(params):
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token/minted", methods = ["PUT"])
def SetTokenMinted():
    params = request.get_json()

    if not HViolas.SetTokenMinted(params):
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/governors")
def GetGovernors():
    infos = HViolas.GetGovernorInfoForSSO()

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/governor")
def GetGovernorInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    infos = HViolas.GetGovernorInfo(offset, limit)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/governor/<address>")
def GetGovernorInfoAboutAddress(address):
    info = HViolas.GetGovernorInfoAboutAddress(address)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor", methods = ["POST"])
def AddGovernorInfo():
    params = request.get_json()

    HViolas.AddGovernorInfo(params)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    params = request.get_json()

    if not HViolas.ModifyGovernorInfo(params):
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment")
def GetGovernorInvestmentInfo():
    info = HViolas.GetInvestmentedGovernorInfo()

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor/investment", methods = ["POST"])
def AddInvestmentInfo():
    params = request.get_json()

    if not HViolas.ModifyGovernorInfo(params):
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["PUT"])
def MakeInvestmentHandled():
    params = request.get_json()

    if not HViolas.ModifyGovernorInfo(params):
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/transactions")
def GetTransactionsAboutGovernor():
    address = request.args.get("address")
    limit = request.args.get("limit", default = 10, type = int)
    start_version = request.args.get("start_version", default = 0, type = int)

    datas = HViolas.GetTransactionsAboutGovernor(address, start_version, limit)

    return MakeResp(ErrorCode.ERR_OK, datas)

# explorer API

@app.route("/explorer/libra/recent")
def LibraGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    datas = HLibra.GetRecentTransaction(limit, offset)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/explorer/libra/address/<address>")
def LibraGetAddressInfo(address):
    limit = request.args.get("limit", 10, type = int)
    offset = request.args.get("offset", 0, type = int)

    addressInfo = HLibra.GetAddressInfo(address)

    cli = MakeLibraClient()
    finish = 0
    while finish < 3:
        try:
            result = cli.get_balance(address)
            addressInfo["balance"] = result
            finish = 3
        except ViolasError as e:
            finish += 1

    addressTransactions = HLibra.GetTransactionsByAddress(address, limit, offset)

    data = {}
    data["status"] = addressInfo
    data["transactions"] = addressTransactions

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/libra/version/<int:version>")
def LibraGetTransactionsByVersion(version):
    transInfo = HLibra.GetTransactionByVersion(version)

    return MakeResp(ErrorCode.ERR_OK, transInfo)

@app.route("/explorer/violas/recent")
def ViolasGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    data = HViolas.GetRecentTransaction(limit, offset)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/recent/<module>")
def ViolasGetRecentTxAboutToken(module):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    data = HViolas.GetRecentTransactionAboutModule(limit, offset, module)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/address/<address>")
def ViolasGetAddressInfo(address):
    module = request.args.get("module")
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 10, type = int)

    addressInfo = HViolas.GetAddressInfo(address)
    if addressInfo is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    cli = MakeViolasClient()
    account_state = cli.get_account_state(address)
    info = account_state.get_scoin_resources()

    module_balance = []
    for key in info.keys():
        item = {}
        item["module"] = key
        item["balance"] = cli.get_balance(address, key)
        module_balance.append(item)

    addressInfo["balance"] = cli.get_balance()
    addressInfo["module_balande"] = module_balance

    if module is None:
        addressTransactions = HViolas.GetTransactionsByAddress(address, limit, offset)
    else:
        addressTransactions = HViolas.GetTransactionsByAddressAboutModule(address, limit, offset, module)

    data = {}
    data["status"] = addressInfo
    data["transactions"] = addressTransactions

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/version/<int:version>")
def ViolasGetTransactionsByVersion(version):
    transInfo = HViolas.GetTransactionByVersion(version)

    return MakeResp(ErrorCode.ERR_OK, transInfo)
