from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeExchangeClient, MakeResp

@app.route("/1.0/market/exchange/currency")
def GetMarketExchangeCurrencies():
    cli = MakeExchangeClient()
    libraCli = MakeLibraClient()

    try:
        currencies = cli.swap_get_registered_currencies()
        libraCurrencies = libraCli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception=e)

    if currencies is None:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "There is no currency has registered!")

    filtered = {}
    filtered["violas"] = []
    filtered["libra"] = []
    filtered["btc"] = []
    for i in currencies:
        if i[0:3] == "VLS" and len(i) > 3:
            cInfo = {}
            cInfo["name"] = i
            cInfo["module"] = i
            cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
            cInfo["show_name"] = i
            cInfo["index"] = currencies.index(i)
            cInfo["icon"] = f"{ICON_URL}violas.png"
            filtered["violas"].append(cInfo)
        elif i == "BTC":
            cInfo = {}
            cInfo["name"] = i
            cInfo["module"] = ""
            cInfo["address"] = ""
            cInfo["show_name"] = i
            cInfo["index"] = 0
            cInfo["icon"] = f"{ICON_URL}btc.png"
            filtered["btc"].append(cInfo)
        else:
            if i == "USD":
                c = "Coin1"
            elif i == "EUR":
                c = "Coin2"
            else:
                c = i

            if c in libraCurrencies:
                cInfo = {}
                cInfo["name"] = c
                cInfo["module"] = c
                cInfo["address"] = LIBRA_CORE_CODE_ADDRESS.hex()
                cInfo["show_name"] = i
                cInfo["index"] = currencies.index(i)
                cInfo["icon"] = f"{ICON_URL}libra.png"
                filtered["libra"].append(cInfo)

    print(filtered)
    return MakeResp(ErrorCode.ERR_OK, filtered)

@app.route("/1.0/market/exchange/currency/available")
def GetMarketExchangeCurrencyAvailable():
    currencyIn = request.args.get("currency")

@app.route("/1.0/market/exchange/trial")
def GetExchangeTrial():
    amount = request.args.get("amount", type = int)
    currencyIn = request.args.get("currencyIn")
    currencyOut = request.args.get("currencyOut")

    cli = MakeExchangeClient()
    try:
        amountOut = cli.swap_get_swap_output_amount(currencyIn, currencyOut, amount)
        path = cli.get_currency_max_output_path(currencyIn, currencyOut, amount)
    except AssertionError:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "Exchange path too deep!")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"amount": amountOut[0],
            "fee": amountOut[1],
            "rate": amount / amountOut[0] if amountOut[0] > 0 else 0,
            "path": path}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/exchange/transaction")
def GetMarketExchangeTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, infos = HViolas.GetMarketExchangeTransaction(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

BASEMAPINFOS = [
    {
        "type": "v2b",
        "chain": "violas",
        "address": "4f93ec275410e8be891ff0fd5da41c43aee27591e222fb466654b4f983d8adbb"
    },
    {
        "type": "v2lusd",
        "chain": "violas",
        "address": "7cd40d7664d5523d360e8a1e0e2682a2dc49a7c8979f83cde4bc229fb35fd27f"
    },
    {
        "type": "v2leur",
        "chain": "violas",
        "address": "a239632a99a92e38eeade27b5e3023e22ab774f228b719991463adf0515688a9"
    },
    {
        "type": "l2vusd",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2veur",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2vgbp",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2vsgd",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    }
]

@app.route("/1.0/market/exchange/crosschain/address/info")
def GetMarketCrosschainMapInfo():
    data = []
    for i in BASEMAPINFOS:
        flow = i["type"][0:3]
        cIn, cOut = flow.split("2")
        currency = i["type"][3:] if len(i["type"]) > 3 else None

        item = {}
        item["lable"] = i["type"]
        item["input_coin_type"] = i["chain"]
        item["receiver_address"] = i["address"][33:]

        if cOut == "v":
            coinType = "violas"
            assets = {"module": "VLS" + currency.upper(),
                      "address": VIOLAS_CORE_CODE_ADDRESS.hex(),
                      "name": "VLS" + currency.upper()}
        elif cOut == "l":
            coinType = "libra"
            if currency == "usd":
                module = "Coin1"
            elif currency == "eur":
                module = "Coin2"

            assets = {"module": module,
                      "address": LIBRA_CORE_CODE_ADDRESS.hex(),
                      "name": module}
        elif cOut == "b":
            coinType = "btc"
            assets = {"module": "",
                      "address": "",
                      "name": "BTC"}

        item["to_coin"] = {"coin_type": coinType,
                           "assets": assets}
        data.append(item)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/exchange/crosschain/map/relation")
def GetExchangeCrosschainMapInfo():
    cli = MakeExchangeClient()
    libCli = MakeLibraClient()

    try:
        currencies = cli.swap_get_registered_currencies()
        libCurrencies = libCli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    libraCurrency = []
    for i in libCurrencies:
        item = {}
        if i == "Coin1":
            item["name"] = "USD"
        elif i == "Coin2":
            item["name"] = "EUR"
        else:
            continue

        item["module"] = i
        libraCurrency.append(item)

    relation = []
    for i in libraCurrency:
        item = {}
        try:
            item["map_name"] = i["module"]
            item["module"] = i["name"]
            item["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
            item["name"] = i["name"]
            item["index"] = currencies.index(i["name"])

            if i == "BTC":
                item["chain"] = "BTC"
            else:
                item["chain"] = "libra"
            print(item)
        except Exception as e:
            continue

        relation.append(item)

    return MakeResp(ErrorCode.ERR_OK, relation)

@app.route("/1.0/market/pool/info")
def GetPoolInfoAboutAccount():
    address = request.args.get("address")

    cli = MakeExchangeClient()

    try:
        currencies = cli.swap_get_registered_currencies()
        balance = cli.swap_get_liquidity_balances(address)
    except AttributeError as e:
        return MakeResp(ErrorCode.ERR_OK, {})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    total = 0
    balancePair = []
    for i in balance:
        item = {}
        for k, v in i.items():
            if k == "liquidity":
                item["token"] = v
                total += v
            else:
                coin = {}
                coin["name"] = k
                coin["module"] = k
                coin["show_name"] = k
                coin["value"] = v
                coin["index"] = currencies.index(k)
                coin["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
                if item.get("coin_a") is None:
                    item["coin_a"] = coin
                else:
                    item["coin_b"] = coin

        balancePair.append(item)

    data = {}
    data["total_token"] = total
    data["balance"] = balancePair
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/market/pool/deposit/trial")
def GetPoolCurrencyRate():
    amount = request.args.get("amount", type = int)
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        amountB = cli.swap_get_liquidity_output_amount(coinA, coinB, amount)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, amountB)

@app.route("/1.0/market/pool/withdrawal/trial")
def GetPoolWithdrawalTrial():
    address = request.args.get("address")
    tokenAmount = request.args.get("amount", type = int)
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        balance = cli.swap_get_liquidity_balances(address)
        for i in balance:
            if coinA in i and coinB in i:
                if tokenAmount > i["liquidity"]:
                    return MakeResp(ErrorCode.ERR_OK, {})
                else:
                    break
            else:
                continue

        trialResult = cli.swap_get_liquidity_out_amounts(coinA, coinB, tokenAmount)
        item = {"coin_a_name": coinA, "coin_a_value": trialResult[0],
                "coin_b_name": coinB, "coin_b_value": trialResult[1]}
    except AttributeError as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "No funds in pool!")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, item)

@app.route("/1.0/market/pool/transaction")
def GetMarketPoolTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, infos = HViolas.GetMarketPoolTransaction(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/market/pool/reserve/info")
def GetReserve():
    coinA = request.args.get("coin_a")
    coinB = request.args.get("coin_b")

    cli = MakeExchangeClient()
    try:
        currencies = cli.swap_get_registered_currencies()
        indexA = currencies.index(coinA)
        indexB = currencies.index(coinB)
        reserves = cli.swap_get_reserves_resource()
        reserve = cli.get_reserve(reserves, indexA, indexB)
    except ValueError:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "Coin not exist.")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception=e)
    reserve = json.loads(reserve.to_json())
    reserve["coina"]["name"] = currencies[reserve["coina"]["index"]]
    reserve["coinb"]["name"] = currencies[reserve["coinb"]["index"]]

    return MakeResp(ErrorCode.ERR_OK, reserve)
