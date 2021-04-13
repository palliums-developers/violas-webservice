from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeExchangeClient, MakeResp, get_show_name

@app.route("/1.0/market/exchange/currency")
def GetMarketExchangeCurrencies():
    cli = MakeExchangeClient()
    libraCli = MakeLibraClient()

    try:
        # to be confirmed
        currencies = cli.swap_get_registered_currencies(update=True)
    except Exception as e:
        logging.error(f"When get violas echange registered currencies: {e}")
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME)

    if currencies is None:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "There is no currency has registered!")

    filtered = []
    for i in currencies:
        cInfo = {}
        cInfo["name"] = i
        cInfo["module"] = i
        cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
        cInfo["show_name"] = i
        cInfo["index"] = currencies.index(i)
        cInfo["icon"] = f"{ICON_URL}violas.png"
        filtered.append(cInfo)

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

@app.route("/1.0/market/exchange/trial/reverse")
def GetExchangeTrialReverse():
    amount = request.args.get("amount", type = int)
    currencyIn = request.args.get("currencyIn")
    currencyOut = request.args.get("currencyOut")

    cli = MakeExchangeClient()
    try:
        amountOut = cli.swap_get_swap_input_amount(currencyIn, currencyOut, amount)
        path = cli.get_currency_max_output_path(currencyIn, currencyOut, amountOut[0])
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

    succ, txnIdxs = HViolas.GetMarketExchangeTransactionIndex(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeExchangeClient()
    infos = []
    for i in txnIdxs:
        txn = cli.get_transaction(i.get("version"), True)
        succ, eventInfo = HViolas.GetMarketExchangeInfo(address, i.get("sequence_number"))
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        info = {
            "version": i.get("version"),
            "date": txn.get_expiration_time(),
            "status": txn.get_vm_status().enum_name,
            "gas_used": txn.get_gas_used_price(),
            "gas_currency": txn.get_gas_currency(),
            "confirmed_time": eventInfo.get("confirmed_time")
        }

        event = txn.get_swap_type_events(txn.get_code_type())[0].get_swap_event().to_json() if txn.get_swap_type_events(txn.get_code_type()) else None

        if event:
            event = json.loads(event)
            info["input_name"] = event.get("input_name")
            info["output_name"] = event.get("output_name")
            info["input_amount"] = event.get("input_amount")
            info["output_amount"] = event.get("output_amount")
            info["input_show_name"] = get_show_name(info["input_name"])
            info["output_show_name"] = get_show_name(info["output_name"])
        else:
            info["input_name"] = eventInfo.get("input_name")
            info["output_name"] = eventInfo.get("output_name")
            info["input_amount"] = eventInfo.get("input_amount")
            info["output_amount"] = eventInfo.get("output_amount")
            info["input_show_name"] = get_show_name(info["input_name"])
            info["output_show_name"] = get_show_name(info["output_name"])

        infos.append(info)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/market/exchange/crosschain/address/info")
def GetMarketCrosschainMapInfo():
    payload = {
        "opt": "receivers",
        "opttype": "swap"
    }

    resp = requests.get("http://52.231.52.107", params = payload)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    mapInfos = resp.json().get("datas")

    data = []
    for i in mapInfos:
        flow = i["type"][0:3]
        cIn, cOut = flow.split("2")
        currency = i["type"][3:] if len(i["type"]) > 3 else None

        item = {}
        if cIn == "b":
            item["lable"] = i["code"]
            item["receiver_address"] = i["address"]
        else:
            item["lable"] = i["type"]
            item["receiver_address"] = i["address"][32:]

        item["input_coin_type"] = i["chain"]

        if cOut == "v":
            coinType = "violas"
            assets = {"module": "VLS" + (currency.upper() if currency is not None else ""),
                      "address": VIOLAS_CORE_CODE_ADDRESS.hex(),
                      "name": "VLS" + (currency.upper() if currency is not None else "")}
        elif cOut == "l":
            coinType = "libra"
            if currency == "usd":
                module = "Coin1"
            elif currency == "eur":
                module = "Coin2"
            else:
                continue

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
        violasCurr = cli.swap_get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)
    try:
        libraCurr = libCli.get_registered_currencies()
    except Exception as e:
        logging.error(f"When get libra registered currencies: {e}")
        libraCurr = []

    filteredCurr = []
    for i in violasCurr:
        if i[:3] == "VLS":
            continue
        else:
            item = {}
            if i == "BTC":
                item["chain"] = "BTC"
                item["index"] = violasCurr.index(i)
                item["map_name"] = "BTC"
                item["module"] = "BTC"
                item["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
                item["name"] = "BTC"
                filteredCurr.append(item)
            elif i == "USD":
                if "Coin1" in libraCurr:
                    item["chain"] = "libra"
                    item["index"] = violasCurr.index(i)
                    item["map_name"] = "Coin1"
                    item["module"] = i
                    item["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
                    item["name"] = i
                    filteredCurr.append(item)
            elif i == "EUR":
                if "Coin2" in libraCurr:
                    item["chain"] = "libra"
                    item["index"] = violasCurr.index(i)
                    item["map_name"] = "Coin2"
                    item["module"] = i
                    item["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
                    item["name"] = i
                    filteredCurr.append(item)
            else:
                if i in libraCurr:
                    item["chain"] = "libra"
                    item["index"] = violasCurr.index(i)
                    item["map_name"] = i
                    item["module"] = i
                    item["module_address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
                    item["name"] = i
                    filteredCurr.append(item)

    return MakeResp(ErrorCode.ERR_OK, filteredCurr)

@app.route("/1.0/market/pool/info")
def GetPoolInfoAboutAccount():
    address = request.args.get("address")

    cli = MakeExchangeClient()

    try:
        currencies = cli.swap_get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    try:
        balance = cli.swap_get_liquidity_balances(address)
    except AttributeError as e:
        return MakeResp(ErrorCode.ERR_OK, {})
    except Exception as e:
        balance = []

    total = 0
    balancePair = []
    for i in balance:
        if i.get("liquidity") == 0:
            continue
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

    succ, txnIdxs = HViolas.GetMarketPoolTransactionIndex(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    infos = []
    cli = MakeExchangeClient()
    for i in txnIdxs:
        txn = cli.get_transaction(i.get("version"), True)
        succ, eventInfo = HViolas.GetMarketExchangeInfo(address, i.get("sequence_number"))
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        info = {
            "version": i.get("version"),
            "date": txn.get_expiration_time(),
            "status": txn.get_vm_status().enum_name,
            "transaction_type": i.get("transaction_type"),
            "gas_used": txn.get_gas_used_price(),
            "gas_currency": txn.get_gas_currency(),
            "confirmed_time": eventInfo.get("confirmed_time")
        }

        event = txn.get_swap_type_events(txn.get_code_type())[0].get_swap_event().to_json() if txn.get_swap_type_events(txn.get_code_type()) else None
        if event:
            event = json.loads(event)
            if i.get("transaction_type") == "REMOVE_LIQUIDITY":
                info["coina"] = event.get("coina")
                info["coinb"] = event.get("coinb")
                info["amounta"] = event.get("withdraw_amounta")
                info["amountb"] = event.get("withdraw_amountb")
                info["coina_show_name"] = get_show_name(info["coina"])
                info["coinb_show_name"] = get_show_name(info["coinb"])
                info["token"] = event.get("burn_amount")
            else:
                info["coina"] = event.get("coina")
                info["coinb"] = event.get("coinb")
                info["amounta"] = event.get("deposit_amounta")
                info["amountb"] = event.get("deposit_amountb")
                info["coina_show_name"] = get_show_name(info["coina"])
                info["coinb_show_name"] = get_show_name(info["coinb"])
                info["token"] = event.get("mint_amount")
        else:
                info["coina"] = eventInfo.get("coina")
                info["coinb"] = eventInfo.get("coinb")
                info["amounta"] = eventInfo.get("amounta")
                info["amountb"] = eventInfo.get("amountb")
                info["coina_show_name"] = eventInfo.get("coina_show_name")
                info["coinb_show_name"] = eventInfo.get("coinb_show_name")
                info["token"] = eventInfo.get("token")

        infos.append(info)

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

@app.route("/1.0/market/pool/reserve/infos")
def GetAllReserve():
    cli = MakeExchangeClient()
    try:
        currencies = cli.swap_get_registered_currencies()
        reserves = cli.swap_get_reserves_resource()
    except ValueError:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, message = "Coin not exist.")
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception=e)

    data = []
    for r in reserves:
        r = json.loads(r.to_json())
        r["coina"]["name"] = currencies[r["coina"]["index"]]
        r["coinb"]["name"] = currencies[r["coinb"]["index"]]
        data.append(r)

    return MakeResp(ErrorCode.ERR_OK, data)
