from ViolasWebservice import app
from common import *
from util import MakeResp, VerifyCodeExist

@app.route("/1.0/violas/sso/user", methods = ["POST"])
def SSOUserRegister():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, result = HViolas.AddSSOUser(params["wallet_address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ, result = HViolas.UpdateSSOUserInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/user")
def GetSSOUserInfo():
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetSSOUserInfo(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if info is None:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    if info["id_photo_positive_url"] is not None:
        info["id_photo_positive_url"] = PHOTO_URL + info["id_photo_positive_url"]

    if info["id_photo_back_url"] is not None:
        info["id_photo_back_url"] = PHOTO_URL + info["id_photo_back_url"]

    return MakeResp(ErrorCode.ERR_OK, info)

@app.route("/1.0/violas/sso/bind", methods = ["POST"])
def BindUserInfo():
    params = request.get_json()
    receiver = params["receiver"]
    verifyCode = params["code"]
    address = params["address"]
    local_number = params.get("phone_local_number")

    receiver = receiver.lower()
    address = address.lower()

    if receiver.find("@") >= 0:
        match = VerifyCodeExist(receiver, verifyCode)
    else:
        match = VerifyCodeExist(local_number + receiver, verifyCode)

    if not match:
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)
    else:
        data = {}
        data["wallet_address"] = address
        if receiver.find("@") >= 0:
            data["email_address"] = receiver
        else:
            data["phone_local_number"] = local_number
            data["phone_number"] = receiver

        succ, result = HViolas.UpdateSSOUserInfo(data)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        if not result:
            return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/token", methods = ["POST"])
def SubmitTokenInfo():
    params = request.get_json()
    params["wallet_address"] = params["wallet_address"].lower()

    succ, userInfo = HViolas.GetSSOUserInfo(params["wallet_address"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if userInfo is None:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    if userInfo["phone_number"] is None:
        return MakeResp(ErrorCode.ERR_PHONE_NUMBER_UNBOUND)

    if not VerifyCodeExist(userInfo["phone_local_number"] + userInfo["phone_number"], params["phone_verify_code"]):
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)

    if userInfo["email_address"] is None:
        return MakeResp(ErrorCode.ERR_EMAIL_UNBOUND)

    if not VerifyCodeExist(userInfo["email_address"], params["email_verify_code"]):
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)

    succ, result = HViolas.AddSSOInfo(params)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if result:
        return MakeResp(ErrorCode.ERR_OK)
    else:
        return MakeResp(ErrorCode.ERR_TOKEN_NAME_DUPLICATE)

@app.route("/1.0/violas/sso/token/status")
def GetTokenApprovalStatus():
    address = request.args.get("address")
    offset = request.args.get("offset", 0, type = int)
    limit = request.args.get("limit", 10, type = int)
    address = address.lower()

    succ, info = HViolas.GetSSOApprovalStatus(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if info is None:
        return MakeResp(ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST)

    if info["approval_status"] == 0:
        timestamp = int(time.time())
        if timestamp > info["expiration_date"]:
            info["approval_status"] = -1
            HViolas.SetApprovalStatus(info["id"], -1)

    data = {"id": info["id"],
            "token_name": info["token_name"] + info["token_type"],
            "approval_status": info["approval_status"],
            "token_id": info["token_id"]}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/sso/token")
def GetTokenDetailInfo():
    address = request.args.get("address")
    address = address.lower()

    succ, info = HViolas.GetTokenDetailInfo(address)

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

@app.route("/1.0/violas/sso/token/status/publish", methods = ["PUT"])
def TokenPublish():
    params = request.get_json()
    params["address"] = params["address"].lower()

    succ, result = HViolas.SetTokenPublished(params["address"], params["id"])
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if not result:
        return MakeResp(ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/sso/governors")
def GetGovernors():
    succ, infos = HViolas.GetGovernorInfoForSSO()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, infos)
