from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeResp

@app.route("/explorer/libra/recent")
def LibraGetRecentTx():
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, datas = HLibra.GetRecentTransaction(limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/explorer/libra/recent/<currency>")
def LibraGetRecentTxAboutToken(currency):
    limit = request.args.get("limit", 30, type = int)
    offset = request.args.get("offset", 0, type = int)

    succ, data = HLibra.GetRecentTransactionAboutCurrency(limit, offset, module)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

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
        print(result)
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

    if currency is None:
        succ, addressTransactions = HLibra.GetTransactionsByAddress(address, limit, offset)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, addressTransactions = HLibra.GetTransactionsByAddressAboutCurrency(address, limit, offset, currency)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = {}
    data["status"] = addressInfo
    data["transactions"] = addressTransactions

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/explorer/libra/version/<int:version>")
def LibraGetTransactionsByVersion(version):
    succ, transInfo = HLibra.GetTransactionByVersion(version)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, transInfo)
