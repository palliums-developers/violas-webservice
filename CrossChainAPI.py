from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp

@app.route("/1.0/crosschain/address")
def GetAddressOfCrossChainTransaction():
    addressName = request.args.get("type")

    address = rdsCoinMap.hget(addressName, "address").decode("utf8")
    return MakeResp(ErrorCode.ERR_OK, address)

@app.route("/1.0/crosschain/module")
def GetModuleOfCrossChainTransaction():
    moduleName = request.args.get("type")

    module = rdsCoinMap.hget(moduleName, "id").decode("utf8")
    return MakeResp(ErrorCode.ERR_OK, module)

@app.route("/1.0/crosschain/rate")
def GetRateOfCrossChainTransaction():
    exchangeName = request.args.get("type")

    data = {}
    data["exchange_name"] = exchangeName
    data["exchange_rate"] = int(rdsCoinMap.hget(exchangeName, "rate").decode("utf8"))

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/crosschain/transactions/count")
def GetCountOfCrossChainTransaction():
    transactionType = request.args.get("type")
    address = request.args.get("address")
    address = address.lower()

    exchangeAddress = rdsCoinMap.hget(transactionType, "address").decode("utf8")
    exchangeModule = int(rdsCoinMap.hget(transactionType, "id").decode("utf8"))

    if transactionType == "vbtc" or transactionType == "vlibra":
        succ, count = HViolas.GetExchangeTransactionCountFrom(address, exchangeAddress, exchangeModule)
    elif transactionType == "btc" or transactionType == "libra":
        succ, count = HViolas.GetExchangeTransactionCountTo(address, exchangeAddress, exchangeModule)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, count)

@app.route("/1.0/crosschain/info")
def GetMapInfoOfCrossChainTransaction():
    coinType = request.args.get("type")

    info = {}
    info["name"] = rdsCoinMap.hget(coinType, "map_name").decode("utf8")
    info["address"] = rdsCoinMap.hget(coinType, "address").decode("utf8")
    info["token_id"] = int(rdsCoinMap.hget(coinType, "id").decode("utf8"))
    info["rate"] = int(rdsCoinMap.hget(coinType, "rate").decode("utf8"))

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/crosschain/transactions")
def GetCrossChainTransactionInfo():
    address = request.args.get("address")
    walletType = request.args.get("type", 0, int)
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = address.lower()

    url = f"{crosschainInfo['HOST']}/?opt=record"
    if walletType == 0:
        wallet = "violas"
    elif walletType == 1:
        wallet = "libra"
    elif walletType == 2:
        wallet = "btc"
    else:
        return MakeResp(ErrorCode.ERR_UNKNOW_WALLET_TYPE)

    url = f"{url}&chain={wallet}&cursor={offset}&limt={limit}&sender={address}"

    resp = requests.get(url)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    respInfos = resp.json()["datas"]

    data = {}
    data["offset"] = respInfos["cursor"]
    infos = []
    for i in respInfos["datas"]:
        info = {}
        if i["state"] == "start":
            info["status"] = 0
        elif i["state"] == "end":
            info["status"] = 1
        else:
            info["status"] = 2

        info["address"] = i["to_address"][32:64]
        info["amount"] = i["amount"]

        if i["type"] == "V2B":
            info["coin"] = "btc"
        elif i["type"] == "V2L":
            info["coin"] = "libra"
        elif i["type"] == "B2V":
            info["coin"] = "vbtc"
        elif i["type"] == "L2V":
            info["coin"]= "vlibra"

        info["date"] = i.get("expiration_time") if i.get("expiration_time") is not None else 0

        infos.append(info)

    data["infos"] = infos

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/crosschain/transactions/btc", methods = ["POST"])
def ForwardBtcTransaction():
    params = request.get_json()
    rawHex = params["rawhex"]

    resp = requests.post("https://tchain.api.btc.com/v3/tools/tx-publish", params = {"rawhex": rawHex})
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)

    if resp.json()["err_no"] != 0:
        logging.error(f"ERROR: Forward BTC request failed, msg: {resp.json()['error_msg']}")
        return MakeResp(ErrorCode.ERR_BTC_FORWARD_REQUEST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/crosschain/modules")
def GetMapedCoinModules():
    address = request.args.get("address")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        info = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if not info.exists():
        return MakeResp(ErrorCode.ERR_ACCOUNT_DOES_NOT_EXIST)
    modus = []
    try:
        for key in info.get_scoin_resources(ContractAddress).tokens:
            modus.append(key)
    except:
        return MakeResp(ErrorCode.ERR_OK, [])

    infos = []
    coins = ["vbtc", "vlibra"]
    for coin in coins:
        if int(rdsCoinMap.hget(coin, "id").decode("utf8")) in modus:
            info = {}
            info["name"] = coin
            info["address"] = rdsCoinMap.hget(coin, "address").decode("utf8")
            info["token_id"] = int(rdsCoinMap.hget(coin, "id").decode("utf8"))
            info["map_name"] = rdsCoinMap.hget(coin, "map_name").decode("utf8")
            info["rate"] = int(rdsCoinMap.hget(coin, "rate").decode("utf8"))

            infos.append(info)

    return MakeResp(ErrorCode.ERR_OK, infos)
