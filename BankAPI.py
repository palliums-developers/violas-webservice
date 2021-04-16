from ViolasWebservice import app
from common import *
from util import MakeBankClient, MakeResp, GetIDNumber, ConvertToUSD
from violas_client.lbrtypes.transaction import SignedTransaction

@app.route("/1.0/violas/bank/account/info")
def GetViolasBankAccountInfo():
    address = request.args.get("address")

    cli = MakeBankClient()
    amount = cli.bank_get_lock_amounts_to_currency(address, "vUSDT")
    max_borrow = cli.bank_get_max_borrow_amount(address, "vUSDT")
    succ, income = HViolas.GetYesterdayIncome(address)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    yesterday = 0
    total = 0

    for y, t in income:
        yesterday += y
        total += t

    succ, borrowed = HViolas.GetBorrowedToday(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    totalBorrow = 0
    for b in borrowed:
        totalBorrow += b[0]

    succ, repaymented = HViolas.GetRepaymentedToday(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    for r in repaymented:
        totalBorrow -= r[0]

    data = {
        "amount": ConvertToUSD(amount),
        "yesterday": ConvertToUSD(yesterday),
        "total": ConvertToUSD(total),
        "borrow": ConvertToUSD(totalBorrow),
        "borrow_limit": ConvertToUSD(max_borrow)
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/product/deposit")
def GetDepositProductList():
    succ, infos = HViolas.GetDepositProductList()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in infos:
        i['logo'] = ICON_URL+i['logo']

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/bank/product/borrow")
def GetBorrowProductsList():
    succ, infos = HViolas.GetBorrowProductList()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in infos:
        i['logo'] = ICON_URL+i['logo']

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/bank/deposit/info")
def GetDepositDetailInfo():
    address = request.args.get("address")
    productId = request.args.get("id")

    succ, info = HViolas.GetDepositProductDetail(productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    succ, quota = HViolas.GetDepositQuotaToday(address, productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    info['quota_used'] = quota
    info['logo'] = ICON_URL + info['logo']
    info['token_address'] = VIOLAS_CORE_CODE_ADDRESS.hex()
    info['token_name'] = info['token_module']
    info['token_show_name'] = info['token_module']

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/bank/deposit/orders")
def GetDepositOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, products = HViolas.GetOrderedProducts(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    cli = MakeBankClient()
    data = []
    for product in products:
        succ, order = HViolas.GetDepositOrderInfo(address, product)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if order is None:
            continue

        order['logo'] = ICON_URL + order['logo']
        order['total_count'] = len(products)
        order["principal"] = cli.bank_get_lock_amount(address, order["currency"])
        if order["principal"] != 0:
            data.append(order)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/order/list")
def GetDepositOrderDetailInfo():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)
    startTime = request.args.get("start", type = int)
    endTime = request.args.get("end", type = int)

    succ, orders, count = HViolas.GetDepositOrderList(address, offset, limit, currency, status, startTime, endTime)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in orders:
        i['logo'] = ICON_URL + i['logo']
        i['total_count'] = count

    return MakeResp(ErrorCode.ERR_OK, orders)

@app.route("/1.0/violas/bank/borrow/info")
def GetBorrowDetailInfo():
    address = request.args.get("address")
    productId = request.args.get("id")

    succ, info = HViolas.GetBorrowProductDetail(productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    succ, quota = HViolas.GetBorrowQuotaToday(address, productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    info['quota_used'] = quota
    info['logo'] = ICON_URL + info['logo']
    info['token_address'] = VIOLAS_CORE_CODE_ADDRESS.hex()
    info['token_name'] = info['token_module']
    info['token_show_name'] = info['token_module']

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/bank/borrow/orders")
def GetBorrowOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    cli = MakeBankClient()

    succ, products = HViolas.GetBorrowOrderedProducts(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = []
    for product in products:
        succ, order = HViolas.GetBorrowOrderInfo(address, product)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        if order is None:
            continue

        order['logo'] = ICON_URL + order['logo']
        order['available_borrow'] = cli.bank_get_max_borrow_amount(address, order['name'])
        order['total_count'] = len(products)
        order["amount"] = cli.bank_get_borrow_amount(address, order["name"])
        if order["amount"] != 0:
            data.append(order)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/order/list")
def GetBorrowOrderList():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)
    startTime = request.args.get("start", type = int)
    endTime = request.args.get("end", type = int)

    succ, orders, count = HViolas.GetBorrowOrderList(address, offset, limit, currency, status, startTime, endTime)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in orders:
        i['logo'] = ICON_URL + i['logo']
        i['total_count'] = count

    return MakeResp(ErrorCode.ERR_OK, orders)

@app.route("/1.0/violas/bank/borrow/order/detail")
def GetBorrowOrderDetail():
    address = request.args.get("address")
    productId = request.args.get("id")
    q = request.args.get("q", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, info = HViolas.GetBorrowOrderDetail(address, productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    succ, orderList = HViolas.GetBorrowOrderDetailList(address, productId, q, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    info['list'] = orderList

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/bank/deposit", methods = ["POST"])
def PostDepositTransaction():
    params = request.get_json()
    address = params["address"]
    productId = params["product_id"]
    value = int(params["value"])
    sigtxn = params["sigtxn"]

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value,
        "order_type": 0,
        "status": 0
    }
    cli = MakeBankClient()
    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddDepositOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except ViolasError as e:
        orderInfo["status"] = -1
        succ = HViolas.AddDepositOrder(orderInfo)

        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/bank/deposit/withdrawal")
def DepositWithdrawal():
    address = request.args.get("address")
    productId = request.args.get("id")

    succ, quantity, currency = HViolas.GetAllDepositOfProduct(address, productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if quantity is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    data = {
        "available_quantity": quantity,
        "product_id": productId,
        "token_name": currency,
        "token_module": currency,
        "token_address": VIOLAS_CORE_CODE_ADDRESS.hex(),
        "token_show_name": currency
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/withdrawal", methods = ["POST"])
def PostDepositWithdrawal():
    params = request.get_json()
    address = params["address"]
    productId = params["product_id"]
    value = int(params["value"])
    sigtxn = params["sigtxn"]

    cli = MakeBankClient()

    if value == 0:
        succ, productInfo = HViolas.GetDepositProductDetail(productId)
        value = cli.bank_get_lock_amount(address, productInfo.get("token_module"))

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value,
        "order_type": 1,
        "status": 0
    }

    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddDepositOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except ViolasError as e:
        orderInfo["status"] = -1
        succ = HViolas.AddDepositOrder(orderInfo)

        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/bank/borrow", methods = ["POST"])
def PostBorrowTransaction():
    params = request.get_json()
    address = params["address"]
    productId = params["product_id"]
    value = int(params["value"])
    sigtxn = params["sigtxn"]

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value,
        "order_type": 0,
        "status": 0
    }
    cli = MakeBankClient()
    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddBorrowOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except ViolasError as e:
        orderInfo["status"] = -1
        succ = HViolas.AddBorrowOrder(orderInfo)

        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/bank/borrow/repayment")
def RepaymentBorrow():
    address = request.args.get("address")
    productId = request.args.get("id")

    succ, data = HViolas.GetBorrowOrderRepayInfo(address, productId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if data is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    data['logo'] = ICON_URL + data['logo']
    data['product_id'] = productId
    data['token_address'] = VIOLAS_CORE_CODE_ADDRESS.hex()
    data['token_name'] = data['token_module']
    data['token_show_name'] = data['token_module']

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/repayment", methods = ["POST"])
def PostBorrowRepayTransaction():
    params = request.get_json()
    address = params["address"]
    productId = params["product_id"]
    value = int(params["value"])
    sigtxn = params["sigtxn"]

    cli = MakeBankClient()

    if value == 0:
        succ, productInfo = HViolas.GetBorrowProductDetail(productId)
        value = cli.bank_get_borrow_amount(address, productInfo.get("token_module"))

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value,
        "order_type": 1,
        "status": 0
    }

    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddBorrowOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except ViolasError as e:
        orderInfo["status"] = -1
        succ = HViolas.AddBorrowOrder(orderInfo)

        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)
