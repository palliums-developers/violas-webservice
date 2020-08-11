from flask import request

from ViolasWebservice import app
from common import HCrossChain, MAPPING_ADDRESS_INFOS
from ErrorCode import ErrorCode
from util import MakeResp, AddressInfo

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

@app.route("/1.0/mapping/address/info")
def GetMappingAddressInfo():
    data = []
    for i in MAPPING_ADDRESS_INFOS:
        type = i.get("type")
        address = i.get("address")
        print(address)
        lable = i.get("lable")
        info = AddressInfo(type, address, lable)
        data.append(info.to_mapping_json())

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/mapping/transaction")

def GetMappingTransactions():
    address = request.args.get("address")
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=5)

    data = [
        {
            "amount_from":{
                "chain": "violas",
                "name": "BTC",
                "show_name": "BTC",
                "amount": 100
            },
            "amount_to": {
                "chain": "btc",
                "name": "BTC",
                "show_name": "BTC",
                "amount": 100
            },
            "confirmed_time": 1596492602,
            "status": 4001,
            "version_or_block_height": 12345689
        },
        {
            "amount_from": {
                "chain": "violas",
                "name": "USD",
                "show_name": "USD",
                "amount": 100
            },
            "amount_to": {
                "chain": "libra",
                "name": "Coin1",
                "show_name": "USD",
                "amount": 100
            },
            "confirmed_time": 1596392602,
            "status": 4001,
            "version_or_block_height": 123456834
        },
        ]
    return MakeResp(ErrorCode.ERR_OK, data)

