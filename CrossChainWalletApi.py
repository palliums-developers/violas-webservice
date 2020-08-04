from flask import request

from ViolasWebservice import app
from common import HCrossChain
from ErrorCode import ErrorCode
from util import MakeResp

@app.route("/1.0/market/crosschain/transaction")
def GetMarketCrosschainTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)
    chain = request.args.get("chain")
    succ, infos = HCrossChain.getCrosschainTransactions(address, offset, limit, chain)
    if not succ:
        return MakeResp(ErrorCode.ERR_CROSSCHAIN_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)
