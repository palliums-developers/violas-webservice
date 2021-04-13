from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp

@app.route("/explorer/violas/recent")
def ViolasGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, txnIdxs = HViolas.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeViolasClient()
    datas = []
    for i in txnIdxs:
        txn = cli.get_transaction(i.get("version"), True)
        data = {
            "version": i.get("version"),
            "sender": txn.get_sender(),
            "receiver": txn.get_receiver(),
            "currency": txn.get_currency_code() if txn.get_currency_code() is not None else txn.get_gas_currency(),
            "amount": txn.get_amount(),
            "gas": txn.get_gas_used_price(),
            "type": txn.get_code_type().name,
            "expiration_time": txn.get_expiration_time(),
            "status": txn.get_vm_status().enum_name
        }
        datas.append(data)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/explorer/violas/recent/<currency>")
def ViolasGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, txnIdxs = HViolas.GetRecentTransactionAboutCurrency(limit, offset, currency)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeViolasClient()
    datas = []
    for i in txnIdxs:
        txn = cli.get_transaction(i.get("version"), True)
        data = {
            "version": i.get("version"),
            "sender": txn.get_sender(),
            "receiver": txn.get_receiver(),
            "currency": txn.get_currency_code() if txn.get_currency_code() is not None else txn.get_gas_currency(),
            "amount": txn.get_amount(),
            "gas": txn.get_gas_used_price(),
            "type": txn.get_code_type().name,
            "expiration_time": txn.get_expiration_time(),
            "status": txn.get_vm_status().enum_name
        }
        datas.append(data)

    return MakeResp(ErrorCode.ERR_OK, datas)

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

    succ, addressTransactions = HViolas.GetTransactionsByAddress(address, currency, limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    addressTransactions = []
    for i in txnIdxs:
        txn = cli.get_transaction(i.get("version"))
        info = {
            "version": i.get("version"),
            "sender": i.get("sender"),
            "receiver": txn.get_receiver(),
            "amount": txn.get_amount(),
            "currency": txn.get_currency_code() if txn.get_currency_code() is not None else txn.get_gas_currency(),
            "gas": txn.get_gas_used_price(),
            "expiration_time": txn.get_expiration_time(),
            "type": txn.get_code_type().name,
            "status": txn.get_vm_status().enum_name,
            "confirmed_time": HLibra.GetTransactionTime(i.get("sender"), i.get("sequence_number"))
        }

        addressTransactions.append(info)

    data = {
        "status": addressInfo,
        "transactions": addressTransactions
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/version/<int:version>")
def ViolasGetTransactionsByVersion(version):
    cli = MakeViolasClient()
    txn = cli.get_transaction(version, True)
    txnInfo = {
        "version": version,
        "sender": txn.get_sender(),
        "sequence_number": txn.get_sequence_number(),
        "receiver": txn.get_receiver(),
        "amount": txn.get_amount(),
        "currency": txn.get_currency_code() if txn.get_currency_code() is not None else txn.get_gas_currency(),
        "gas_currency": txn.get_gas_currency(),
        "gas": txn.get_gas_used_price(),
        "expiration_time": txn.get_expiration_time(),
        "type": txn.get_code_type().name,
        "status": txn.get_vm_status().enum_name,
        "gas_unit_price": txn.get_gas_unit_price(),
        "max_gas_amount": txn.transaction.value.get_max_gas_amount(),
        "public_key": txn.get_public_key(),
        "signature": txn.get_signature(),
        "data": txn.get_data(),
        "confirmed_time": HViolas.GetTransactionTime(txn.get_sender(), txn.get_sequence_number())
    }

    return MakeResp(ErrorCode.ERR_OK, txnInfo)

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
