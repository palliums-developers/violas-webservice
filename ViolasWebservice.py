import os, random, logging, configparser, datetime, requests, json
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from libra import Client, AccountError, TransactionTimeoutError, LibraNetError, TransactionIllegalError
from libra.transaction import SignedTransaction
from redis import Redis

from ViolasPGHandler import ViolasPGHandler
from PushServerHandler import PushServerHandler

logging.basicConfig(filename = "ViolasWebservice.log", level = logging.DEBUG)
config = configparser.ConfigParser()
config.read("./config.ini")

app = Flask(__name__)
CORS(app, resources = r"/*")

LIBRA_HOST = "testnet"
VIOLAS_HOST = "violas_testnet"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
PHOTO_FOLDER = os.path.abspath("/var/www/violas_wallet/photo")
PHOTO_URL = "http://52.27.228.84:4000/1.0/violas/photo/"

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"
# HLibra = LibraPGHandler(libraDBUrl)

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"
HViolas = ViolasPGHandler(violasDBUrl)

pushInfo = config["PUSH SERVER"]
pushh = PushServerHandler(pushInfo["HOST"], int(pushInfo["PORT"]))

cachingInfo = config["CACHING SERVER"]
rds = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["DB"], cachingInfo["PASSWORD"])

EXPLORER_HOST = "http://52.27.228.84:4001"
TRANSACTIONS_FOR_WALLET = "/violas/transaction/wallet"
TRANSACTION_ABOUT_VBTC = "/violas/transaction/vbtc"
TRANSACTION_ABOUT_GOVERNOR = "/violas/transaction/governor"

def MakeLibraClient():
    return Client(LIBRA_HOST)

def MakeViolasClient():
    return Client(VIOLAS_HOST, "/tmp/consensus_peers.config.toml", "/tmp/faucet_keys")

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeLibraClient()
    try:
        result = cli.get_balance(address)
        info = {}
        info["address"] = address
        info["balance"] = result
        resp["data"] = info
    except AccountError:
        info = {}
        info["address"] = address
        info["balance"] = 0
        resp["data"] = info

    return resp

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    modules = request.args.get("modu", "")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeViolasClient()
    try:
        result = cli.get_balance(address)
        info = {}
        info["address"] = address
        info["balance"] = result
    except AccountError:
        info  = {}
        info["address"] = address
        info["balance"] = 0
        resp["data"] = info
        return resp

    if len(modules) != 0:
        modulesBalance = []
        moduleList = modules.split(",")
        for i in moduleList:
            try:
                result = cli.violas_get_balance(bytes.fromhex(address), bytes.fromhex(i))
            except AccountError:
                resp["code"] = 2000
                resp["message"] = "Account Error."
                return resp

            print(result)
            moduleInfo = {}
            moduleInfo["address"] = i
            moduleInfo["balance"] = result

            modulesBalance.append(moduleInfo)

        info["modules"] = modulesBalance

    resp["data"] = info
    return resp

@app.route("/1.0/libra/seqnum")
def GetLibraSequenceNumbert():
    address = request.args.get("addr")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = 0
        return resp

    resp["data"] = seqNum

    return resp

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeViolasClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = 0
        return resp

    resp["data"] = seqNum

    return resp

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    cli = MakeLibraClient()

    params = request.get_json()
    signedtxn = params["signedtxn"]

    sigTxn = SignedTransaction.deserialize(bytes.fromhex(signedtxn))
    print(sigTxn.to_json_serializable())
    print(sigTxn.raw_txn.serialize().hex())
    pubKey = "".join(["{:02x}".format(i) for i in sigTxn.public_key])
    print(pubKey)
    signature = "".join(["{:02x}".format(i) for i in sigTxn.signature])
    print(signature)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    try:
        cli.submit_signed_txn(signedtxn, True)
    except TransactionTimeoutError as e:
        resp["code"] = 2002
        resp["message"] = "Error: Waiting for background response timeout!"
    except TransactionIllegalError as e:
        resp["code"] = 2011
        resp["message"] = f"Error: {e.error_msg}"

    return resp

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    cli = MakeViolasClient()

    params = request.get_json()
    signedtxn = params["signedtxn"]

    sigTxn = SignedTransaction.deserialize(bytes.fromhex(signedtxn))
    print(sigTxn.to_json_serializable())
    print(sigTxn.raw_txn.serialize().hex())
    pubKey = "".join(["{:02x}".format(i) for i in sigTxn.public_key])
    print(pubKey)
    signature = "".join(["{:02x}".format(i) for i in sigTxn.signature])
    print(signature)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    try:
        cli.submit_signed_txn(signedtxn, True)
    except TransactionTimeoutError as e:
        resp["code"] = 2002
        resp["message"] = "Error: Waiting for background response timeout!"
    except TransactionIllegalError as e:
        resp["code"] = 2011
        resp["message"] = f"Error: {e.error_msg}"

    return resp

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = []
        return resp

    if offset > seqNum:
        resp["data"] = []
        return resp

    transactions = []

    for i in range(offset, seqNum):
        if (i - offset) >= limit:
            break

        try:
            tran = cli.get_account_transaction(address, i)
        except AccountError:
            resp["data"] = []
            return resp

        print(tran)

        info = {}
        info["version"] = tran.get_version()
        info["address"] = tran.get_sender_address()
        info["sequence_number"] = tran.get_sender_sequence()
        info["value"] = tran.raw_txn.payload.args[1]
        info["expiration_time"] = tran.get_expiration_time()

        transactions.append(info)

    resp["data"] = transactions

    return resp

@app.route("/1.0/violas/transaction")
def GetViolasTransactionInfo():
    address = request.args.get("addr")
    module = request.args.get("modu", "0000000000000000000000000000000000000000000000000000000000000000")
    limit = request.args.get("limit", 10, int)
    offset = request.args.get("offset", 0, int)

    reqURL = f"{EXPLORER_HOST}{TRANSACTIONS_FOR_WALLET}?address={address}&module={module}&limit={limit}&offset={offset}"

    response = requests.get(reqURL)
    result = json.loads(response.text)

    return result

@app.route("/1.0/violas/currency")
def GetCurrency():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    currencies = []
    info = {}
    info["name"] = "Xcoin"
    info["description"] = "desc of Xcoin"
    info["address"] = "05599ef248e215849cc599f563b4883fc8aff31f1e43dff1e3ebe4de1370e054"
    currencies.append(info)
    info1 = {}
    info1["name"] = "ABCUSD"
    info1["description"] = "desc"
    info1["address"] = "b9e3266ca9f28103ca7c9bb9e5eb6d0d8c1a9d774a11b384798a3c4784d5411e"
    currencies.append(info1)
    info2 = {}
    info2["name"] = "HIJUSD"
    info2["description"] = "desc"
    info2["address"] = "75bea7a9c432fe0d94f13c6d73543ea8758940e9b622b70dbbafec5ffbf74782"
    currencies.append(info2)
    info3 = {}
    info3["name"] = "XYZUSD"
    info3["description"] = "desc"
    info3["address"] = "f013ea4acf944fa6edafe01fae10713d13928ca5dff9e809dbcce8b12c2c45f1"
    currencies.append(info3)
    info4 = {}
    info4["name"] = "BCDCAD"
    info4["description"] = "desc"
    info4["address"] = "ad8e9520399689822b55bc783f03951c00fa2ae9eb997d477a2ff0bdc702a568"
    currencies.append(info4)
    info5 = {}
    info5["name"] = "CDESGD"
    info5["description"] = "desc"
    info5["address"] = "15d3e4bea615b78c3782553df712a4f86d85280f11939e0b35756422575fc622"
    currencies.append(info5)
    info6 = {}
    info6["name"] = "DEFHKD"
    info6["description"] = "desc"
    info6["address"] = "e90e4f077bef23b32a6694a18a1fa34244532400869e4e8c87ce66d0b6c004bd"
    currencies.append(info6)

    resp["data"] = currencies
    return resp

@app.route("/1.0/violas/module")
def CheckMoudleExise():
    addr = request.args.get("addr")

    cli = MakeViolasClient()
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    try:
        info = cli.violas_get_info(addr)
    except AccountError:
        resp["data"] = []
        return resp

    modus = []
    for key in info.keys():
        modus.append(key)

    resp["data"] = modus
    return resp

@app.route("/1.0/violas/vbtc/transaction")
def GetVBtcTransactionInfo():
    receiverAddress = request.args.get("receiver_address")
    moduleAddress = request.args.get("module_address")
    startVersion = request.args.get("start_version", type = int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    reqURL = f"{EXPLORER_HOST}{TRANSACTION_ABOUT_VBTC}?receiver_address={receiverAddress}&module_address={moduleAddress}&start_version={startVersion}"

    response = requests.get(reqURL)
    result = json.loads(response.text)
    resp["data"] = result["data"]

    return resp

@app.route("/1.0/violas/vbtc/transaction", methods = ["POST"])
def VerifyVBtcTransactionInfo():
    params = request.get_json()
    logging.debug(f"Get params: {params}")

    reqURL = f"{EXPLORER_HOST}{TRANSACTION_ABOUT_VBTC}"
    response = requests.post(reqURL, json = params)
    result = json.loads(response.text)

    return result

@app.route("/1.0/violas/sso/user")
def GetSSOUserInfo():
    address = request.args.get("address")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    info = HViolas.GetSSOUserInfo(address)

    if info is None:
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"
        return resp

    if info["id_photo_positive_url"] is not None:
        info["id_photo_positive_url"] = PHOTO_URL + info["id_photo_positive_url"]

    if info["id_photo_back_url"] is not None:
        info["id_photo_back_url"] = PHOTO_URL + info["id_photo_back_url"]

    resp["data"] = info

    return resp

@app.route("/1.0/violas/sso/user", methods = ["POST"])
def SSOUserRegister():
    params = request.get_json()
    HViolas.AddSSOUser(params["wallet_address"])
    HViolas.UpdateSSOUserInfo(params)
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/sso/token")
def GetTokenApprovalStatus():
    address = request.args.get("address")
    info = HViolas.GetSSOApprovalStatus(address)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if info is None:
        resp["code"] = 2006
        resp["message"] = "Token info not exists!"

        return resp

    resp["data"] = info

    return resp

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    userInfo = HViolas.GetSSOUserInfo(params["wallet_address"])
    if userInfo is None:
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"
        return resp

    if userInfo["phone_number"] is None:
        resp["code"] = 2007
        resp["message"] = "Phone unbound!"
        return resp

    if not VerifyCodeExist(userInfo["phone_local_number"] + userInfo["phone_number"], params["phone_verify_code"]):
        resp["code"] = 2003
        resp["message"] = "Verify error!"
        return resp

    if userInfo["email_address"] is None:
        resp["code"] = 2008
        resp["message"] = "Email unbound!"
        return resp

    if not VerifyCodeExist(userInfo["email_address"], params["email_verify_code"]):
        resp["code"] = 2003
        resp["message"] = "Verify error!"
        return resp

    HViolas.AddSSOInfo(params)

    return resp

@app.route("/1.0/violas/sso/token", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()
    HViolas.SetTokenPublished(params["address"])

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

def AllowedType(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/1.0/violas/photo", methods = ["POST"])
def UploadPhoto():
    photo = request.files["photo"]
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not AllowedType(photo.filename):
        resp["code"] = 2009
        resp["message"] = "Image type not allowed!"

        return resp

    ext = secure_filename(photo.filename).rsplit(".", 1)[1]
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    randomNum = random.randint(1000, 9999)
    uuid = str(nowTime) + str(randomNum) + "." + ext
    path = os.path.join(PHOTO_FOLDER, uuid)
    photo.save(path)

    resp["data"] = uuid

    return resp

@app.route("/1.0/violas/verify_code", methods = ["POST"])
def SendVerifyCode():
    params = request.get_json()
    receiver = params["receiver"]
    address = params["address"]
    verifyCode = random.randint(100000, 999999)
    local_number = params.get("phone_local_number")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    HViolas.AddSSOUser(address)

    if receiver.find("@") >= 0:
        succ = pushh.PushEmailSMSCode(verifyCode, receiver, 5)
        rds.setex(receiver, 600, str(verifyCode))
    else:
        succ = pushh.PushPhoneSMSCode(verifyCode, local_number + receiver, 5)
        rds.setex(local_number + receiver, 600, str(verifyCode))

    if not succ:
        resp["code"] = 2004
        resp["message"] = "Verify code send failed!"
        return resp

    return resp

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

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

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

    return resp

@app.route("/1.0/violas/sso/token/unapproval")
def GetUnapprovalTokenInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    infos = HViolas.GetUnapprovalSSO(offset, limit)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = infos

    return resp

@app.route("/1.0/violas/sso/token/unapproval", methods = ["PUT"])
def ModifyApprovalStatus():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not HViolas.SetMintInfo(params):
        resp["code"] = 2010
        resp["message"] = "Address info not exists"

    return resp

@app.route("/1.0/violas/sso/token/published")
def GetPublishedTokenInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    infos = HViolas.GetPublishedSSOInfo(offset, limit)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = infos

    return resp

@app.route("/1.0/violas/sso/token/minted", methods = ["PUT"])
def SetTokenMinted():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not HViolas.SetTokenMinted(params):
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"

    return resp

@app.route("/1.0/violas/governor")
def GetGovernorInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    infos = HViolas.GetGovernorInfo(offset, limit)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = infos

    return resp

@app.route("/1.0/violas/governor", methods = ["POST"])
def AddGovernorInfo():
    params = request.get_json()

    HViolas.AddGovernorInfo(params)
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not HViolas.ModifyGovernorInfo(params):
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"

    return resp

@app.route("/1.0/violas/governor/investment")
def GetGovernorInvestmentInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = HViolas.GetInvestmentedGovernorInfo(offset, limit)

    return resp

@app.route("/1.0/violas/governor/investment", methods = ["POST"])
def AddInvestmentInfo():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not HViolas.ModifyGovernorInfo(params):
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"

    return resp

@app.route("/1.0/violas/governor/investment", methods = ["PUT"])
def MakeInvestmentHandled():
    params = request.get_json()

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not HViolas.ModifyGovernorInfo(params):
        resp["code"] = 2005
        resp["message"] = "Address info not exists!"

    return resp

@app.route("/1.0/violas/governor/transactions")
def GetTransactionsAboutGovernor():
    address = request.args.get("address")
    limit = request.args.get("limit", default = 10, type = int)
    start_version = request.args.get("start_version", default = 0, type = int)

    reqURL = f"{EXPLORER_HOST}{TRANSACTION_ABOUT_GOVERNOR}?address={address}&limit={limit}&start_version={start_version}"
    response = requests.get(reqURL)
    result = json.loads(response.text)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = result["data"]

    return resp
