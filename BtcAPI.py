from ViolasWebservice import app
from common import *

@app.route("/1.0/btc/balance")
def GetBtcBalance():
    address = request.args.get("address")

    reqUrl = f"https://btc1.trezor.io/api/v2/address/{address}"
    resp = requests.get(reqUrl)

    balance = resp.json()["balance"]

    data = [{"BTC": balance, "name": "BTC", "show_name": "BTC", "show_icon": f"{ICON_URL}btc.png"}]
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/btc/transaction", methods = ["POST"])
def BroadcastBtcTransaction():
    params = request.get_json()
    rawHex = params["rawhex"]

    resp = requests.post("https://btc1.trezor.io/api/v2/sendtx", params = {"rawhex": rawHex})
    if resp.json().get("error") is not None:
        logging.error(f"ERROR: Forward BTC request failed, msg: {resp.json()['error']['message']}")
        return MakeResp(ErrorCode.ERR_BTC_FORWARD_REQUEST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/btc/utxo")
def GetBtcUTXO():
    address = request.args.get("address")
    reqUrl = f"https://btc1.trezor.io/api/v2/utxo/{address}"
    resp = requests.get(reqUrl)

    return MakeResp(ErrorCode.ERR_OK, resp.json())

@app.route("/1.0/btc/transaction")
def GetBtcTransaction():
    address = request.args.get("address")
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    reqUrl = f"https://btc1.trezor.io/api/v2/address/{address}?page={offset + 1}&pageSize={limit}"
    resp = requests.get(reqUrl)

    txids = resp.json().get("txids")
    for txid in txids:
        reqUrl = f"https://btc1.trezor.io/api/v2/tx/{txid}"
        resp = requests.get(reqUrl)
        print(resp.json())

    return MakeResp(ErrorCode.ERR_OK)
