from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp

@app.route("/1.0/violas/governor/<address>")
def GetGovernorInfoAboutAddress(address):
    address = address.lower()

    succ, info = HViolas.GetGovernorInfoAboutAddress(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.1/violas/governor", methods=["POST"])
def AddGovernorInfoV2():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddGovernorInfoForFrontEnd(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_EXISTED)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor", methods = ["PUT"])
def ModifyGovernorInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["POST"])
def AddInvestmentInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/investment", methods = ["PUT"])
def MakeInvestmentHandled():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/status/published", methods = ["PUT"])
def MakeGovernorStatusToPublished():
    params = request.get_json()
    params["is_handle"] = 3
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.ModifyGovernorInfo(params)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/token/status")
def GetUnapprovalTokenInfoList():
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetGovernorInfoAboutAddress(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST)

    if info["status"] != 4:
        return MakeResp(ErrorCode.ERR_VSTAKE)

    succ, infos = HViolas.GetUnapprovalSSOList(address, limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    for info in infos:
        if info["approval_status"] == 0:
            timestamp = int(time.time())
            if timestamp > info["expiration_date"]:
                info["approval_statsu"] = -1
                HViolas.SetApprovalStatus(info["id"], -1)

    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/governor/token")
def GetUnapprovalTokenDetailInfo():
    address = request.args.get("address")
    id = request.args.get("id", type = int)
    address = address.lower()

    succ, info = HViolas.GetUnapprovalTokenDetailInfo(address, id)

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    if info["account_info_photo_positive_url"] is not None:
        info["account_info_photo_positive_url"] = PHOTO_URL + info["account_info_photo_positive_url"]

    if info["account_info_photo_back_url"] is not None:
        info["account_info_photo_back_url"] = PHOTO_URL + info["account_info_photo_back_url"]

    if info["reserve_photo_url"] is not None:
        info["reserve_photo_url"] = PHOTO_URL + info["reserve_photo_url"]

    if info["approval_status"] == 0:
        timestamp = int(time.time())
        if timestamp > info["expiration_date"]:
            info["approval_status"] = -1
            HViolas.SetApprovalStatus(info["id"], -1)

    if info["approval_status"] == -2:
        info["failed_reason"] = GovernorFailedReason[info["failed_reason"]]
    if info["approval_status"] == -3:
        info["failed_reason"] = ChairmanFailedReason[info["failed_reason"]]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/governor/token/status", methods = ["PUT"])
def ModifyApprovalStatusV2():
    params = request.get_json()

    if params["status"] > 0:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"])
    else:
        succ, info = HViolas.SetApprovalStatus(params["id"], params["status"], params["reason"], params["remarks"])

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not info:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/vstake/address")
def GetVstakeAddress():
    succ, address = HViolas.GetVstakeModuleAddress()

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if address is None:
        return MakeResp(ErrorCode.ERR_VSTAKE_ADDRESS)

    data = {"address": address}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/governor/authority")
def CheckGovernorAuthority():
    address = request.args.get("address")
    module = request.args.get("module")
    address = address.lower()

    cli = MakeViolasClient()

    try:
        result = cli.get_balance(address, module)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if result != 1:
        data = {"authority": 0}
        return MakeResp(ErrorCode.ERR_OK, data)

    data = {"authority": 1}
    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/governor/singin", methods = ["POST"])
def VerifySinginSessionID():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.CheckBind(params["address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if not result:
        return MakeResp(ErrorCode.ERR_CHAIRMAN_UNBIND)

    succ, info = HViolas.GetGovernorInfoAboutAddress(params["address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    value = rdsAuth.get("SessionID")

    if value is None:
        return MakeResp(ErrorCode.ERR_SINGIN_TIMEOUT)

    data = hashlib.sha3_256()
    data.update(value)

    verify_key = nacl.signing.VerifyKey(info["violas_public_key"], encoder=nacl.encoding.HexEncoder)
    try:
        verify_key.verify(data.hexdigest(), params["session_id"], encoder=nacl.encoding.HexEncoder)
    except nacl.exceptions.BadSignatureError:
        rdsAuth.set("SessionID", "Failed")
        return MakeResp(ErrorCode.ERR_SIG_ERROR)

    rdsAuth.set("SessionID", "Success")
    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/governor/reason")
def GetGovernorFailReason():
    return MakeResp(ErrorCode.ERR_OK, GovernorFailedReason)
