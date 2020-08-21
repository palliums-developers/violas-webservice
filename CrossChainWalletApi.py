from flask import request

from ViolasWebservice import app
from common import HCrossChain, MAPPING_ADDRESS_INFOS, requests
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
        lable = i.get("lable")
        info = AddressInfo(type, address, lable)
        data.append(info.to_mapping_json())

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/mapping/transaction")
def GetMappingTransactions():
    address = request.args.get("addresses")
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=5)

    params = {
        "opt": "records",
        "senders": address,
        "opttype": "map",
        "cursor": offset,
        "limit": limit
    }

    resp = requests.get("http://18.136.139.151", params = params)
    datas = resp.json()["datas"]["datas"]

    return MakeResp(ErrorCode.ERR_OK, datas)
