import os, random, logging, configparser
from flask import Flask, request, send_file
from flask_cors import CORS
from libra import Client, AccountError, TransactionTimeoutError
from libra.transaction import SignedTransaction

from ViolasPGHandler import ViolasPGHandler

logging.basicConfig(filename = "log.out", level = logging.DEBUG)
config = configparser.ConfigParser()
config.read("./config.ini")

app = Flask(__name__)
CORS(app, resources = r"/*")

LIBRA = "testnet"
VIOLAS_HOST = "52.27.228.84"
VIOLAS_PORT = 40001
PHOTO_FOLDER = os.path.abspath(".")

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"
# HLibra = LibraPGHandler(libraDBUrl)

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"
HViolas = ViolasPGHandler(violasDBUrl)

def MakeLibraClient():
    return Client(LIBRA)

def MakeViolasClient():
    return Client(LIBRA)
    # return Client.new(VIOLAS_HOST, VIOLAS_PORT, "../../documents/consensus_peers.config.toml")

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")

    resp = {}n
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
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeViolasClient()
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
            print(tran)
        except AccountError:
            resp["data"] = []
            return resp

        print(tran.raw_txn.type)
        print(tran.raw_txn.type.type)

        if tran.raw_txn.type.type == "violas_init":
            info = {}
            info["type"] = 1
            info["version"] = tran.get_version()
            info["sequence_number"] = tran.get_sender_sequence()
            info["expiration_time"] = tran.get_expiration_time()
            info["gas"] = tran.get_gas_unit_price()
            info["sender"] = tran.raw_txn.type.sender
            info["receiver"] = tran.raw_txn.type.receiver
            info["sender_module"] = tran.raw_txn.type.sender_module_address
            info["receiver_module"] = ""
            info["amount"] = 0

            transactions.append(info)
        elif tran.raw_txn.type.type == "violas_peer_to_peer_transfer":
            info = {}
            info["type"] = 2
            info["version"] = tran.get_version()
            info["sequence_number"] = tran.get_sender_sequence()
            info["expiration_time"] = tran.get_expiration_time()
            info["gas"] = tran.get_gas_unit_price()
            info["sender"] = tran.raw_txn.type.sender
            info["receiver"] = tran.raw_txn.type.receiver
            info["sender_module"] = tran.raw_txn.type.sender_module_address
            info["receiver_module"] = tran.raw_txn.type.receiver_module_address
            info["amount"] = tran.raw_txn.type.amount

            transactions.append(info)

    resp["data"] = transactions

    return resp

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
    info1["name"] = "Ycoin"
    info1["description"] = "desc of Ycoin"
    info1["address"] = "xxxxxxxxxxxxxxxxxxxxxxxx"
    currencies.append(info1)
    info2 = {}
    info2["name"] = "Zcoin"
    info2["description"] = "desc of Zcoin"
    info2["address"] = "xxxxxxxxxxxxxxxxxxxxxxxx"
    currencies.append(info2)

    resp["data"] = currencies
    return resp

@app.route("/1.0/violas/module")
def CheckMoudleExise():
    addr = request.args.get("addr")

    cli = MakeViolasClient()
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    info = cli.violas_get_info(addr)
    modus = []
    for key in info.keys():
        modus.append(key)

    resp["data"] = modus
    return resp

@app.route("/1.0/violas/sso/user", methods = ["POST"])
def SSORegister():
    params = request.get_json()
    HViolas.AddSSOUserInfo(params)

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
    resp["data"] = info

    return resp

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()
    HViolas.AddSSOInfo(params)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/sso/token", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()
    HViolas.ModifySSOPublishStatus(params["address"], 1)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/photo", methods = ["POST"])
def UploadPhoto():
    photo = request.files["photo"]
    photoName = photo.filename
    path = os.path.join(PHOTO_FOLDER, photoName)
    photo.save(path)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = path

    return resp

@app.route("/1.0/violas/photo")
def DownloadPhoto():
    path = request.args.get("path")

    return send_file(path, attachment_filename = os.path.basename(path))

@app.route("/1.0/violas/verify_code")
def SendVerifyCode():
    receiver = request.args.get("receiver")
    verifyCode = random.randint(100000, 999999)

    if receiver.find("@") >= 0:
        # email
    else:
        # phone

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/verify_code", methods = ["POST"])
def CheckVerifyCode():
    receiver = request.args.get("receiver")
    verifyCode = request.args.get("code")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    if not VerifyCodeExist():
        resp["code"] = 2003
        resp["message"] = "Verify error!"

    return resp

@app.route("/1.0/violas/governor")
def GetGovernorInfo():
    resp = {}
    return resp

@app.route("/1.0/violas/governor", methods = ["POST"])
def AddGovernorInfo():
    resp = {}
    return resp

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    resp = {}
    return resp
