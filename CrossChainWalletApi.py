from flask import request

from ViolasWebservice import app
from common import HCrossChain, requests
from ErrorCode import ErrorCode
from util import MakeResp, AddressInfo, get_show_name

@app.route("/1.0/market/crosschain/transaction")
def GetMarketCrosschainTransactions():
    address = request.args.get("addresses")
    offset = request.args.get("offset", type = int, default = 0)
    limit = request.args.get("limit", type = int, default = 5)

    succ, infos = HCrossChain.getCrosschainTransactions(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_CROSSCHAIN_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/mapping/address/info")
def GetMappingAddressInfo():
    payload = {
        "opt": "receivers",
        "opttype": "map"
    }

    resp = requests.get("http://52.231.52.107", params= payload)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    mapInfos = resp.json().get("datas")

    data = []
    for i in mapInfos:
        type = i.get("type")
        if type == "e2vm":
            continue
        address = i.get("address")
        lable = i.get("code")
        for coinPair in i.get("from_to_token"):
            scoin = coinPair.get("from_coin")
            rcoin = coinPair.get("to_coin")
            info = AddressInfo(type, address, scoin, rcoin, lable)

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

    resp = requests.get("http://52.231.52.107", params = params)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    datas = resp.json()["datas"]["datas"]
    for i in datas:
        i["in_show_name"] = get_show_name(i["in_token"])
        i["out_show_name"] = get_show_name(i["out_token"])

    return MakeResp(ErrorCode.ERR_OK, datas)
