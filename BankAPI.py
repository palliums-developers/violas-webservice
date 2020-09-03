from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp
from violas_client.lbrtypes.transaction import SignedTransaction

@app.route("/1.0/violas/bank/account/info")
def GetViolasBankAccountInfo():
    address = request.args.get("address")

    data = {"amount": 2000.34,
            "yesterday": 0.3,
            "total": 42.76,
            "borrow": 1403.23,
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/product/deposit")
def GetDepositProductList():
    data = [
        {
            "id": "100001",
            "logo": "http://xxxxxxxxx",
            "name": "aaaaaa",
            "desc": "aaaaaaaaaaaaaaaaaaaaaaaaaa",
            "rate": 0.032,
            "rate_desc": "年化利率",
            "token_module": "BTC"
        },
        {
            "id": "100002",
            "logo": "http://xxxxxxxxx",
            "name": "bbbbbb",
            "desc": "bbbbbbbbbbbbbbbbbbbbbbbbbb",
            "rate": 0.042,
            "rate_desc": "7日年化利率",
            "token_module": "LBR"
        }
    ]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/product/borrow")
def GetBorrowProductsList():
    data = [
        {
            "id": "200001",
            "logo": "http://xxxxxxxxxx",
            "name": "ccccccc",
            "desc": "cccccccccccccccccccccccccc",
            "rate": 0.038,
            "rate_desc": "年化利率",
            "token_module": "BTC"
        },
        {
            "id": "200002",
            "logo": "http://xxxxxxxxxx",
            "name": "ddddddd",
            "desc": "dddddddddddddddddddddddddd",
            "rate": 0.05,
            "rate_desc": "7日年化利率",
            "token_module": "LBR"
        }
    ]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/info")
def GetDepositDetailInfo():
    address = request.args.get("address")
    productId = request.args.get("id")

    data = {
        "id": "100001",
        "name": "xxxxxx",
        "logo": "http://xxxxxxxxxx",
        "minimum_amount": 500,
        "quota_used": 0,
        "quota_limit": 1500,
        "rate": 0.03,
        "pledge_rate": 0.05,
        "intor": [
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"},
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"}
        ],
        "question": [
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"},
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"}
        ],
        "token_module": "BTC",
        "token_address": "00000000000000000000000000000001",
        "token_name": "BTC",
        "token_show_name": "BTC"
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/orders")
def GetDepositOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    data = [
        {
            "id": "2000001",
            "logo": "http://xxxxxxxxxxx",
            "currency": "LBR",
            "status": 1,
            "principal": 1500,
            "earnings": 22,
            "rate": 0.039
        },
        {
            "id": "2000001",
            "logo": "http://xxxxxxxxxxx",
            "currency": "LBR",
            "status": 1,
            "principal": 1500,
            "earnings": 22,
            "rate": 0.039
        }
    ]
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/withdrawal")
def DepositWithdrawal():
    address = request.args.get("address")
    orderId = request.args.get("id")

    data = {
        "available_quantity": 100,
        "token_name": "BTC",
        "token_module": "BTC",
        "token_address": "00000000000000000000000000000001",
        "token_show_name": "BTC"
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/deposit/order/list")
def GetDepositOrderDetailInfo():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    data = [
        {
            "id": "200001",
            "logo": "http://xxxxxxxxxxxx",
            "currency": "LBR",
            "date": 1518391892,
            "value": 182.22,
            "status": 1
        },
        {
            "id": "200001",
            "logo": "http://xxxxxxxxxxxx",
            "currency": "LBR",
            "date": 1518391892,
            "value": 182.22,
            "status": 1
        }
    ]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/info")
def GetBorrowDetailInfo():
    productId = request.args.get("id")

    data = {
        "id": "100001",
        "name": "xxxxxx",
        "logo": "http://xxxxxxxxxxxx",
        "minimum_amount": 500,
        "quota_used": 0,
        "quota_limit": 1500,
        "rate": 0.03,
        "pledge_rate": 0.05,
        "intor": [
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"},
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"}
        ],
        "question": [
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"},
            {"tital":"aaaaaaaaaaa", "text":"xxxxxxxxxxxxxxxxxxxxxx"}
        ],
        "token_module": "BTC",
        "token_address": "00000000000000000000000000000001",
        "token_name": "BTC",
        "token_show_name": "BTC"
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/orders")
def GetBorrowOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    data = [
        {
            "id": "2000001",
            "logo": "http://xxxxxxxxxxx",
            "name": "LBR",
            "amount": 1500,
            "available_borrow":15000
        },
        {
            "id": "2000001",
            "logo": "http://xxxxxxxxxxx",
            "name": "LBR",
            "amount": 1500,
            "available_borrow":1500
        }
    ]
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/order/list")
def GetBorrowOrderList():
    address = request.args.get("address")
    currency = request.args.get("currency")
    status = request.args.get("status", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    data = [
        {
            "id": "200001",
            "logo": "http://xxxxxxxxxxxxxxxx",
            "currency": "LBR",
            "date": 1518391892,
            "value": 182.22,
            "status": 1
        },
        {
            "id": "200001",
            "logo": "http://xxxxxxxxxxxxxxxx",
            "currency": "LBR",
            "date": 1518391892,
            "value": 182.22,
            "status": 1
        }
    ]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/order/detail")
def GetBorrowOrderDetail():
    address = request.args.get("address")
    productId = request.args.get("id")
    q = request.args.get("q", type = int)
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 10)

    data = {
        "id": "100001",
        "name": "BTC",
        "balance": 2000
    }

    if q == 1:
        data["list"] = [
            {
                "date": 159888010,
                "amount": 1000,
                "status": 2
            },
            {
                "date": 159888010,
                "amount": 1000,
                "status": 2
            }
        ]
    elif q == 2:
        data["list"] = [
            {
                "date": 159888010,
                "cleared": 1000,
                "deductioned": 1000,
                "status": 3,
                "deductioned_currency": "LBR"
            },
            {
                "date": 159888010,
                "cleared": 1000,
                "deductioned": 1000,
                "status": 3,
                "deductioned_currency": "BTC"
            }
        ]
    else:
        data["list"] = [
            {
                "date": 159992342,
                "amount": 823,
                "status": 1
            },
            {
                "date": 159992342,
                "amount": 823,
                "status": 1
            }
        ]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/borrow/repayment")
def RepaymentBorrow():
    address = request.args.get("address")
    orderId = request.args.get("id")

    data = {
        "balance": 2000,
        "rate": 0.05,
        "token_module": "BTC",
        "token_address": "00000000000000000000000000000001",
        "token_name": "BTC",
        "token_show_name": "BTC"
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/bank/transaction", methods = ["POST"])
def MakeBankTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    cli = MakeViolasClient()
    # transactionInfo = bytes.fromhex(signedtxn)
    # transactionInfo = SignedTransaction.deserialize(transactionInfo)
    # sender = transactionInfo.get_sender()
    # seqNum = transactionInfo.get_sequence_number()
    # timestamp = int(time.time())

    try:
        cli.submit_signed_transaction(signedtxn, True)
    except Exception as e:
        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)
        # HViolas.AddTransactionInfo(sender, seqNum, timestamp, transactionInfo.to_json())
        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)
