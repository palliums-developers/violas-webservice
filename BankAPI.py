from ViolasWebservice import app
from common import *
from util import MakeBankClient, MakeResp, GetIDNumber
from violas_client.lbrtypes.transaction import SignedTransaction

@app.route("/1.0/violas/bank/account/info")
def GetViolasBankAccountInfo():
    address = request.args.get("address")

    cli = MakeBankClient()
    amounts = cli.bank_get_lock_amounts(address)
    totalAmount = 0
    for value in amounts.values():
        totalAmount += value

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

    data = {
        "amount": totalAmount,
        "yesterday": yesterday,
        "total": total,
        "borrow": totalBorrow
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
    limit = request.args.get("limit", type = int, default = 10)

    succ, products = HViolas.GetOrderedProducts(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = []
    for product in products:
        succ, order = HViolas.GetDepositOrderInfo(address, product)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        if order is None:
            continue

        order['logo'] = ICON_URL + order['logo']
        data.append(order)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/order/list")
def GetDepositOrderDetailInfo():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    succ, orders = HViolas.GetDepositOrderList(address, offset, limit, currency, status)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in orders:
        i['logo'] = ICON_URL + i['logo']

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
    limit = request.args.get("limit", type = int, default = 10)

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
        data.append(order)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/order/list")
def GetBorrowOrderList():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    succ, orders = HViolas.GetBorrowOrderList(address, offset, limit, currency, status)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for i in orders:
        i['logo'] = ICON_URL + i['logo']

    return MakeResp(ErrorCode.ERR_OK, orders)

@app.route("/1.0/violas/bank/borrow/order/detail")
def GetBorrowOrderDetail():
    address = request.args.get("address")
    productId = request.args.get("id")
    q = request.args.get("q", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

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
    value = params["value"]
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
    except LibraError as e:
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
    value = params["value"]
    sigtxn = params["sigtxn"]

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value * -1,
        "order_type": 1,
        "status": 0
    }
    cli = MakeBankClient()
    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddDepositOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except LibraError as e:
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
    value = params["value"]
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
    except LibraError as e:
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
    orderId = request.args.get("id")

    succ, data = HViolas.GetBorrowOrderRepayInfo(address, orderId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if data is None:
        return MakeResp(ErrorCode.ERR_OK, {})

    data['logo'] = ICON_URL + data['logo']
    data['token_address'] = VIOLAS_CORE_CODE_ADDRESS.hex()
    data['token_name'] = data['token_module']
    data['token_show_name'] = data['token_module']

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/repayment", methods = ["POST"])
def PostBorrowRepayTransaction():
    params = request.get_json()
    address = params["address"]
    productId = params["product_id"]
    value = params["value"]
    sigtxn = params["sigtxn"]

    orderInfo = {
        "order_id": GetIDNumber(),
        "product_id": productId,
        "address": address,
        "value": value * -1,
        "order_type": 1,
        "status": 0
    }
    cli = MakeBankClient()
    try:
        cli.submit_signed_transaction(sigtxn, True)
        succ = HViolas.AddBorrowOrder(orderInfo)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except LibraError as e:
        orderInfo["status"] = -1
        succ = HViolas.AddBorrowOrder(orderInfo)

        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)
