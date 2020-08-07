from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp

@app.route("/explorer/violas/recent")
def ViolasGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HViolas.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/violas/recent/<currency>")
def ViolasGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HViolas.GetRecentTransactionAboutCurrency(limit, offset, currency)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

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

    if currency is None:
        succ, addressTransactions = HViolas.GetTransactionsByAddress(address, limit, offset)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, addressTransactions = HViolas.GetTransactionsByAddressAboutCurrency(address, limit, offset, currency)
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
