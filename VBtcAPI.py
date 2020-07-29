from ViolasWebservice import app
from common import *
from util import MakeResp

@app.route("/1.0/violas/vbtc/transaction")
def GetVBtcTransactionInfo():
    receiverAddress = request.args.get("receiver_address")
    moduleAddress = request.args.get("module_address")
    startVersion = request.args.get("start_version", type = int)

    receiverAddress = receiverAddress.lower()
    moduleAddress = moduleAddress.lower()

    succ, datas = HViolas.GetTransactionsAboutVBtc(receiverAddress, moduleAddress, startVersion)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/vbtc/transaction", methods = ["POST"])
def VerifyVBtcTransactionInfo():
    params = request.get_json()

    params["sender_address"] = params["sender_address"].lower()
    params["receiver"] = params["receiver"].lower()
    params["module"] = params["module"].lower()

    succ, result = HViolas.VerifyTransactionAboutVBtc(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_VBTC_TRANSACTION_INFO)

    return MakeResp(ErrorCode.ERR_OK)
