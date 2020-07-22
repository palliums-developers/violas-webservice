from ViolasWebservice import app
from common import *
from util import MakeResp

@app.route("/1.0/violas/chairman", methods = ["POST"])
def AddGovernorInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddGovernorInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/governors")
def GetGovernorInfo():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    succ, infos = HViolas.GetGovernorInfoList(offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/chairman/governors/investmented")
def GetGovernorInvestmentInfo():
    succ, info = HViolas.GetInvestmentedGovernorInfo()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/chairman/investment/status", methods = ["PUT"])
def SetGovernorInvestmentStatus():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.SetGovernorStatus(params["wallet_address"], params["is_handle"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/governor/transactions")
def GetTransactionsAboutGovernor():
    address = request.args.get("address")
    limit = request.args.get("limit", default = 10, type = int)
    start_version = request.args.get("start_version", default = 0, type = int)
    address = address.lower()

    succ, datas = HViolas.GetTransactionsAboutGovernor(address, start_version, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/chairman/bind/governor", methods = ["POST"])
def ChairmanBindGovernor():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.ChairmanBindGovernor(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/singin/qrcode")
def GetSinginQRCodeInfo():
    bSessionId = os.urandom(32)

    data = {}
    data["timestamp"] = int(time.time())
    data["expiration_time"] = 60
    qr = {}
    qr["type"] = 1
    qr["session_id"] = bSessionId.hex()
    data["qr_code"] = qr
    rdsAuth.setex("SessionID", 60, bSessionId.hex())

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/chairman/singin/status")
def GetSinginStatus():
    value = rdsAuth.get("SessionID")
    if value is None:
        data = {"status": 3}
        return MakeResp(ErrorCode.ERR_OK, data)

    et = rdsAuth.ttl("SessionID")
    if et != -1:
        data = {"status": 0}
        return MakeResp(ErrorCode.ERR_OK, data)

    if str(value, "utf-8") == "Success":
        data = {"status": 1}
    else:
        data = {"status": 2}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/chairman/token/status")
def GetUnapprovalTokenInfoListFromGovernor():
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 0, type = int)

    succ, infos = HViolas.GetUnapprovalSSOListForChairman(offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/chairman/token")
def GetUnapprovalTokenDetailInfoFromGovernor():
    address = request.args.get("address")
    id = request.args.get("id", type = int)
    address = address.lower()

    succ, info = HViolas.GetTokenDetailInfoForChairman(address, id)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/chairman/token/status", methods = ["PUT"])
def ChairmanSetTokenStatus():
    params = request.get_json()

    if params["status"] > 0:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"])
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

        succ, info = HViolas.SetTokenID(params["id"], params["token_id"])
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    else:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"], params["reason"], params["remarks"])

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/chairman/reason")
def GetChairmanFailReason():
    return MakeResp(ErrorCode.ERR_OK, ChairmanFailedReason)
