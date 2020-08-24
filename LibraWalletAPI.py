from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeResp

@app.route("/1.0/libra/balance")
def GetLibraBalance():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        if currency is None:
            balances = cli.get_balances(address)
            data = {"balances": balances}
            data = []
            for key, value in balances.items():
                item = {}
                item["name"] = key
                item["balance"] = value

                if key == "Coin1":
                    showName = "USD"
                elif key == "Coin2":
                    showName = "EUR"
                else:
                    showName = key

                item["show_name"] = showName
                item["show_icon"] = f"{ICON_URL}libra.png"
                item["address"] = address

                data.append(item)
        else:
            balance = cli.get_balance(address, currency_code = currency)
            if currency == "Coin1":
                showName = "USD"
            elif currency == "Coin2":
                showName = "EUR"
            else:
                showName = currency

            data = [{currency: balance, "name": currency, "show_name": showName, "show_icon": f"{ICON_URL}libra.png"}]

    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, {"balances": data})

@app.route("/1.0/libra/seqnum")
def GetLibraSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        seqNum = cli.get_sequence_number(address)
        return MakeResp(ErrorCode.ERR_OK, {"seqnum": seqNum})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

@app.route("/1.0/libra/transaction", methods = ["POST"])
def MakeLibraTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeLibraClient()
    try:
        cli.submit_signed_transaction(signedtxn, True)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/transaction")
def GetLibraTransactionInfo():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    flows = request.args.get("flows", type = int)
    limit = request.args.get("limit", 5, int)
    offset = request.args.get("offset", 0, int)
    address = address.lower()

    succ, datas = HLibra.GetTransactionsForWallet(address, currency, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/libra/mint")
def MintLibraToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")
    currency = request.args.get("currency")
    address = address.lower()

    cli = MakeLibraClient()
    try:
        cli.mint_coin(address, 100, auth_key_prefix = authKey, is_blocking = True, currency_code=currency)
    except ValueError:
        return MakeResp(ErrorCode.ERR_INVAILED_ADDRESS)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/libra/currency")
def GetLibraCurrency():
    cli = MakeLibraClient()

    try:
        currencies = cli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = []
    for i in currencies:
        cInfo = {}
        cInfo["name"] = i
        cInfo["module"] = i
        cInfo["address"] = LIBRA_CORE_CODE_ADDRESS.hex()
        cInfo["show_icon"] = f"{ICON_URL}libra.png"
        if i == "Coin1":
            cInfo["show_name"] = "USD"
        elif i == "Coin2":
            cInfo["show_name"] = "EUR"
        else:
            cInfo["show_name"] = i

        data.append(cInfo)

    return MakeResp(ErrorCode.ERR_OK, {"currencies": data})

@app.route("/1.0/libra/account/info")
def GetLibraAccountInfo():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeLibraClient()

    try:
        state = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_account_resource().authentication_key.hex(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_account_resource().key_rotation_capability.value.account_address.hex(),
            "delegated_withdrawal_capability": state.get_account_resource().withdrawal_capability.value.account_address.hex(),
            "received_events_key": state.get_account_resource().received_events.get_key(),
            "sent_events_key": state.get_account_resource().sent_events.get_key()}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/libra/currency/published")
def CheckLibraCurrencyPublished():
    addr = request.args.get("addr")
    addr = addr.lower()

    cli = MakeLibraClient()

    try:
        balances = cli.get_balances(addr)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    keys = []
    for key in balances:
        keys.append(key)

    return MakeResp(ErrorCode.ERR_OK, {"published": keys})
