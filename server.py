from flask import Flask, request, redirect, url_for, jsonify
from flask_cors import CORS
from libra import Client
from libra import AccountError
from libra.transaction import SignedTransaction

app = Flask(__name__)
CORS(app, resources = r"/*")

LIBRA = "testnet"
VIOLAS_HOST = "52.27.228.84"
VIOLAS_PORT = 40001

def MakeClient():
    return Client.new(VIOLAS_HOST, VIOLAS_PORT, "/tmp/consensus_peers.config.toml")
    # return Client.new(VIOLAS_HOST, VIOLAS_PORT)

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeClient()
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
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

    return resp

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    modules = request.args.get("modu", "")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeClient()
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
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

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
            except Exception as e:
                resp["code"] = 3000
                resp["message"] = "Error:{0}".format(e);

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

    cli = MakeClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = 0

        return resp

    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

        return resp

    resp["data"] = seqNum

    return resp

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = 0

        return resp

    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

        return resp

    resp["data"] = seqNum

    return resp

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    cli = MakeClient()

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
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

    return resp

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    cli = MakeClient()

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
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

    return resp

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)

    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    cli = MakeClient()
    try:
        seqNum = cli.get_sequence_number(address)
    except AccountError:
        resp["data"] = []

        return resp
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

        return resp

    print(seqNum)
    if offset > seqNum:
        resp["data"] = []

        return resp

    transactions = []

    for i in range(offset, seqNum):
        if (i - offset) >= limit:
            break;

        try:
            tran = cli.get_account_transaction(address, i)
        except AccountError:
            resp["data"] = []

            return resp
        except Exception as e:
            resp["code"] = 3000
            resp["message"] = "Error:{0}".format(e);

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

    cli = MakeClient()
    try:
        seqNum = cli.get_sequence_number(address)
        print(seqNum)
    except AccountError:
        resp["data"] = []

        return resp
    except Exception as e:
        resp["code"] = 3000
        resp["message"] = "Error:{0}".format(e);

        return resp

    if offset > seqNum:
        resp["data"] = []

        return resp

    transactions = []

    for i in range(offset, seqNum):
        if (i - offset) >= limit:
            break;

        try:
            tran = cli.get_account_transaction(address, i)
            print(tran)
        except AccountError:
            resp["data"] = []
            return resp
        except Exception as e:
            resp["code"] = 3000
            resp["message"] = "Error:{0}".format(e);
            return resp


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
