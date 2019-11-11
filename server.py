from flask import Flask, request, redirect, url_for, jsonify
from flask_cors import CORS
from libra import Client
from libra.transaction import SignedTransaction

app = Flask(__name__)
CORS(app, resources = r"/*")

LIBRA = "testnet"
VIOLAS_HOST = "125.39.5.57"
VIOLAS_PORT = 46454

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = Client(LIBRA)
    result = cli.get_balance(address)
    print(result)
    info = {}
    info["address"] = address
    info["balance"] = result

    resp["data"] = info
    return resp

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    modules = request.args.get("modu", "")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = Client(LIBRA)
    result = cli.get_balance(address)
    info = {}
    info["address"] = address
    info["balance"] = result

    if len(modules) != 0:
        modulesBalance = []
        cli = Client.new(VIOLAS_HOST, VIOLAS_PORT)
        moduleList = modules.split(",")
        for i in moduleList:
            result = cli.violas_get_balance(address, i)
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
    cli = Client(LIBRA)
    seqNum = cli.get_sequence_number(address)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = seqNum

    return resp

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")
    cli = Client.new(VIOLAS_HOST, VIOLAS_PORT)
    seqNum = cli.get_sequence_number(address)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["data"] = seqNum

    return resp

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    cli = Client(LIBRA)

    params = request.get_json()
    signedtxn = params["signedtxn"]

    sigTxn = SignedTransaction.deserialize(bytes.fromhex(signedtxn))
    print(sigTxn.to_json_serializable())
    print(sigTxn.raw_txn.serialize().hex())
    pubKey = "".join(["{:02x}".format(i) for i in sigTxn.public_key])
    print(pubKey)
    signature = "".join(["{:02x}".format(i) for i in sigTxn.signature])
    print(signature)

    cli.submit_signed_txn(signedtxn, True)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    cli = Client.new(VIOLAS_HOST, VIOLAS_PORT)

    params = request.get_json()
    signedtxn = params["signedtxn"]

    sigTxn = SignedTransaction.deserialize(bytes.fromhex(signedtxn))
    print(sigTxn.to_json_serializable())
    print(sigTxn.raw_txn.serialize().hex())
    pubKey = "".join(["{:02x}".format(i) for i in sigTxn.public_key])
    print(pubKey)
    signature = "".join(["{:02x}".format(i) for i in sigTxn.signature])
    print(signature)

    cli.submit_signed_txn(signedtxn, True)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = Client(LIBRA)
    seqNum = cli.get_sequence_number(address)
    print(seqNum)
    if offset > seqNum:
        resp["code"] = 2001
        resp["message"] = "Error offset"
        return resp

    transactions = []

    for i in range(offset, seqNum):
        if (i - offset) >= limit:
            break;

        tranInfo = cli.get_account_transaction_info(address, i)
        tran = cli.get_account_transaction(address, i)
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

    cli = Client.new(VIOLAS_HOST, VIOLAS_PORT)
    seqNum = cli.get_sequence_number(address)
    print(seqNum)
    if offset > seqNum:
        resp["code"] = 2001
        resp["message"] = "Error offset"
        return resp

    transactions = []

    for i in range(offset, seqNum):
        if (i - offset) >= limit:
            break;

        tranInfo = cli.get_account_transaction_info(address, i)
        tran = cli.get_account_transaction(address, i)
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

@app.route("/1.0/violas/currency")
def GetCurrency():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    currencies = []
    info = {}
    info["name"] = "Xcoin"
    info["description"] = "desc of Xcoin"
    currencies.append(info)
    info["name"] = "Ycoin"
    info["description"] = "desc of Ycoin"
    currencies.append(info)
    info["name"] = "Zcoin"
    info["description"] = "desc of Zcoin"
    currencies.append(info)

    resp["data"] = currencies
    return resp
