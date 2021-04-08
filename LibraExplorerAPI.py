from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeResp

@app.route("/explorer/libra/recent")
def LibraGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, txnIdxs = HLibra.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeLibraClient()
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

@app.route("/explorer/libra/recent/<currency>")
def LibraGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, txnIdxs = HLibra.GetRecentTransactionAboutCurrency(limit, offset, currency)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeLibraClient()
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

    succ, txnIdxs = HLibra.GetTransactionsByAddress(address, currency, limit, offset)
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

@app.route("/explorer/libra/version/<int:version>")
def LibraGetTransactionsByVersion(version):
    cli = MakeLibraClient()
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
        "confirmed_time": HLibra.GetTransactionTime(txn.get_sender(), txn.get_sequence_number())
    }

    return MakeResp(ErrorCode.ERR_OK, txnInfo)
