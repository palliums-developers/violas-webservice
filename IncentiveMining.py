from ViolasWebservice import app
from common import *
from util import MakeViolasClient, MakeResp, VerifyCodeExist, MakeBankClient, MakeExchangeClient, GetAccount, MakeTransfer

@app.route("/1.0/violas/incentive/mobile/verify", methods = ["POST"])
def VerifyIncentiveMobile():
    params = request.get_json()
    walletAddress = params.get("wallet_address")
    localNumber = params.get("local_number")
    mobileNumber = params.get("mobile_number")
    verifyCode = params.get("verify_code")
    inviterAddress = params.get("inviter_address")

    if not all([walletAddress, localNumber, mobileNumber, verifyCode]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    value = rdsVerify.get(localNumber + mobileNumber)

    if value is None:
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)
    elif value.decode("utf8") != str(verifyCode):
        return MakeResp(ErrorCode.ERR_VERIFICATION_CODE)

    rdsVerify.delete(localNumber + mobileNumber)

    orderInfo = {
        "walletAddress": walletAddress,
        "phoneNumber": localNumber + mobileNumber,
        "inviterAddress": inviterAddress
    }

    succ, isNew = HViolas.CheckRegistered(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if isNew == 1:
        return MakeResp(ErrorCode.ERR_INCENTIVE_RECEIVED)

    succ, regCount = HViolas.GetPhoneRegisterCount(localNumber + mobileNumber)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    if regCount == 3:
        return MakeResp(ErrorCode.ERR_REGISTER_COUNT)

    account = GetAccount()
    try:
        MakeTransfer(account, walletAddress, 10 * 1000000, "VLS")
        succ = HViolas.AddNewIncentiveRecord(walletAddress, 10 * 1000000, 1, 0)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    except ViolasError as e:
        succ = HViolas.AddNewIncentiveRecord(walletAddress, 10 * 1000000, 0, 0)
        if not succ:
            return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    if inviterAddress is not None and len(inviterAddress) > 0:
        try:
            MakeTransfer(account, walletAddress, 1 * 1000000, "VLS")
            succ = HViolas.AddNewIncentiveRecord(walletAddress, 1 * 1000000, 1, 2)
            if not succ:
                return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        except ViolasError as e:
            succ = HViolas.AddNewIncentiveRecord(walletAddress, 1 * 1000000, 0, 2)
            if not succ:
                return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

        try:
            MakeTransfer(account, inviterAddress, 2 * 1000000, "VLS")
            succ = HViolas.AddNewIncentiveRecord(inviterAddress, 2 * 1000000, 1, 1)
            if not succ:
                return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
        except ViolasError as e:
            succ = HViolas.AddNewIncentiveRecord(inviterAddress, 2 * 1000000, 0, 1)
            if not succ:
                return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    succ = HViolas.AddNewRegisteredRecord(orderInfo)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/incentive/check/verified")
def CheckWalletIsVerified():
    walletAddress = request.args.get("address")

    if not all([walletAddress]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, isNew = HViolas.CheckRegistered(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, {"is_new": isNew})

@app.route("/1.0/violas/incentive/orders/invite")
def GetInviteOrders():
    walletAddress = request.args.get("address")
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=10, type=int)

    if not all([walletAddress]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, orders = HViolas.GetInviteOrders(walletAddress, limit, offset)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, orders)

@app.route("/1.0/violas/incentive/inviter/top20")
def GetInviteTop20():
    succ, infos = HViolas.GetTop20Invite()

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/incentive/inviter/info")
def GetInviterInfo():
    walletAddress = request.args.get("address")

    if not all([walletAddress]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, count = HViolas.GetInviteCount(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, {"invite_count": count, "incentive": 2 * count})

@app.route("/1.0/violas/incentive/mint/info")
def GetIncentiveMintInfo():
    walletAddress = request.args.get("address")

    if not all([walletAddress]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, total = HViolas.GetTotalIncentive(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ, bankTotal = HViolas.GetBankTotalIncenntive(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ, poolTotal = HViolas.GetPoolTotalIncenntive(walletAddress)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    bankCli = MakeBankClient()
    bankIncentive = bankCli.bank_get_sum_incentive_amount(walletAddress)
    poolCli = MakeExchangeClient()
    poolIncentive = poolCli.swap_get_reward_balance(walletAddress)

    succ, ranking = HViolas.GetIncentiveTop20()
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    data = {
        "total_incentive": total,
        "bank_total_incentive": bankTotal,
        "bank_incentive": bankIncentive if bankIncentive is not None else 0,
        "pool_total_incentive": poolTotal,
        "pool_incentive": poolIncentive if poolIncentive is not None else 0,
        "ranking": ranking
    }

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/incentive/top20")
def GetIncentiveTop20():
    succ, infos = HViolas.GetIncentiveTop20()

    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)
    return MakeResp(ErrorCode.ERR_OK, infos)

@app.route("/1.0/violas/incentive/orders/bank")
def GetBankIncentiveOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=10, type=int)

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, orders = HViolas.GetBankIncentiveOrders(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, orders)

@app.route("/1.0/violas/incentive/orders/pool")
def GetPoolIncentiveOrders():
    address = request.args.get("address")
    offset = request.args.get("offset", default=0, type=int)
    limit = request.args.get("limit", default=10, type=int)

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, orders = HViolas.GetPoolIncentiveOrders(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, orders)
