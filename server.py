from flask import Flask, request, redirect, url_for, jsonify
from flask_cors import CORS
from libra import Client
from libra.transaction import SignedTransaction

app = Flask(__name__)
CORS(app, resources = r"/*")

LIBRA = "testnet"
VIOLAS = ""

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    balance = []

    cli = Client(LIBRA)
    result = cli.get_balance(address)
    print(result)
    info = {}
    info["address"] = address
    info["balance"] = result

    balance.append(info)

    resp["balance"] = balance
    return resp

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    modules = request.args.get("modu")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    balance = []

    cli = Client(VIOLAS)
    for i in modules:
        result = cli.violas_get_balance(address, i)
        print(result)
        info = {}
        info["address"] = address
        inof["module"] = i
        info["balance"] = result

        balance.append(info)

    resp["balance"] = balance
    return resp

@app.route("/1.0/libra/seqnum")
def GetSequenceNumbert():
    address = request.args.get("addr")
    cli = Client(LIBRA)
    seqNum = cli.get_sequence_number(address)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["sequence_number"] = seqNum

    return resp

@app.route("/1.0/violas/seqnum")
def GetSequenceNumbert():
    address = request.args.get("addr")
    cli = Client(VIOLAS)
    seqNum = cli.get_sequence_number(address)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    resp["sequence_number"] = seqNum

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
    cli = Client(VIOLAS)

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

    resp["transactions"] = transactions

    return resp

@app.route("/1.0/violas/transaction")
def GetViolasTransactionInfo():
    address = request.args.get("addr")
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = Client(VIOLAS)
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

    resp["transactions"] = transactions

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

    resp["currencies"] = currencies
    return resp
