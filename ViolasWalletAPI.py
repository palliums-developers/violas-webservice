from ViolasWebservice import app
from common import *
from util import MakeLibraClient, MakeViolasClient, MakeResp, AllowedType, GetRates, GetAccount, MakeTransfer
from violas_client.lbrtypes.transaction import SignedTransaction

@app.route("/1.0/violas/balance")
def GetViolasBalance():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    address = address.lower()

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()
    try:
        if currency is None:
            balances = cli.get_balances(address)

            data = []
            for key, value in balances.items():
                item = {}
                item["name"] = key
                item["balance"] = value
                item["show_name"] = key
                item["show_icon"] = f"{ICON_URL}violas.png"
                item["address"] = address

                data.append(item)
        else:
            balance = cli.get_balance(address, currency_code = currency)
            showName = currency[3:] if len(currency) > 3 else currency
            data = [{currency: balance, "name": currency, "show_name": currency, "show_icon": f"{ICON_URL}violas.png"}]

    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK, {"balances": data})

@app.route("/1.0/violas/seqnum")
def GetViolasSequenceNumbert():
    address = request.args.get("addr")
    address = address.lower()

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()
    try:
        seqNum = cli.get_sequence_number(address)
        return MakeResp(ErrorCode.ERR_OK, {"seqnum": seqNum})
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

@app.route("/1.0/violas/transaction", methods = ["POST"])
def MakeViolasTransaction():
    params = request.get_json()
    signedtxn = params["signedtxn"]

    if not all([signedtxn]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()
    transactionInfo = bytes.fromhex(signedtxn)
    transactionInfo = SignedTransaction.deserialize(transactionInfo)
    sender = transactionInfo.get_sender()
    seqNum = transactionInfo.get_sequence_number()
    timestamp = int(time.time())

    try:
        cli.submit_signed_transaction(signedtxn, True)
    except Exception as e:
        if not e.on_chain:
            return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)
        HViolas.AddTransactionInfo(sender, seqNum, timestamp, transactionInfo.to_json())
        return MakeResp(ErrorCode.ERR_CLIENT_UNKNOW_ERROR)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/transaction")
def GetViolasTransactionInfo():
    address = request.args.get("addr")
    currency = request.args.get("currency")
    flows = request.args.get("flows", type = int)
    limit = request.args.get("limit", 10, int)
    offset = request.args.get("offset", 0, int)
    address = address.lower()

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, datas = HViolas.GetTransactionsForWallet(address, currency, flows, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, datas)

@app.route("/1.0/violas/currency")
def GetViolasCurrency():
    cli = MakeViolasClient()

    try:
        currencies = cli.get_registered_currencies()
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    filtered = []
    for i in currencies:
        # if i == "VLS":
        #     filtered.append(i)
        # elif i != "Coin1" and i != "Coin2" and len(i) > 3:
        #     filtered.append(i)
        if i != "Coin1" and i != "Coin2":
            filtered.append(i)

    data = []
    for i in filtered:
        cInfo = {}
        cInfo["name"] = i
        cInfo["module"] = i
        cInfo["address"] = VIOLAS_CORE_CODE_ADDRESS.hex()
        cInfo["show_icon"] = f"{ICON_URL}violas.png"
        cInfo["show_name"] = i

        data.append(cInfo)

    return MakeResp(ErrorCode.ERR_OK, {"currencies": data})

@app.route("/1.0/violas/currency/published")
def CheckCurrencyPublished():
    addr = request.args.get("addr")
    addr = addr.lower()

    if not all([addr]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()

    try:
        balances = cli.get_balances(addr)
        print(balances)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    keys = []
    for key in balances:
        keys.append(key)

    return MakeResp(ErrorCode.ERR_OK, {"published": keys})

@app.route("/1.0/violas/photo", methods = ["POST"])
def UploadPhoto():
    photo = request.files["photo"]

    if not AllowedType(photo.filename):
        return MakeResp(ErrorCode.ERR_IMAGE_FORMAT)

    ext = secure_filename(photo.filename).rsplit(".", 1)[1]
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    randomNum = random.randint(1000, 9999)
    uuid = str(nowTime) + str(randomNum) + "." + ext
    path = os.path.join(PHOTO_FOLDER, uuid)
    photo.save(path)

    return MakeResp(ErrorCode.ERR_OK, {"image": uuid})

@app.route("/1.0/violas/verify_code", methods = ["POST"])
def SendVerifyCode():
    params = request.get_json()
    address = params["address"]
    local_number = params.get("phone_local_number")
    receiver = params["receiver"]

    receiver = receiver.lower()
    address = address.lower()

    if not all([address, local_number, receiver]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    verifyCode = random.randint(100000, 999999)

    succ, result = HViolas.AddSSOUser(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    if receiver.find("@") >= 0:
        succ = pushh.PushEmailSMSCode(verifyCode, receiver, 5)
        rdsVerify.setex(receiver, 600, str(verifyCode))
    else:
        succ = pushh.PushPhoneSMSCode(verifyCode, local_number + receiver, 5)
        rdsVerify.setex(local_number + receiver, 600, str(verifyCode))

    if not succ:
        return MakeResp(ErrorCode.ERR_SEND_VERIFICATION_CODE)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/singin", methods = ["POST"])
def UploadWalletInfo():
    params = request.get_json()
    wallets = []
    for i in params["wallets"]:
        wallets.append(i)

    value = rdsAuth.get(params["session_id"])

    if value is None:
        return MakeResp(ErrorCode.ERR_SESSION_NOT_EXIST)

    data = {"status": "Success", "wallets": wallets}

    rdsAuth.set(params["session_id"], json.JSONEncoder().encode(data))

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/mint")
def MintViolasToAccount():
    address = request.args.get("address")
    authKey = request.args.get("auth_key_perfix")
    currency = request.args.get("currency")
    address = address.lower()

    if not all([address, authKey]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    account = GetAccount()
    cli = MakeViolasClient()
    try:
        state = cli.get_account_state(address)
        if state is not None:
            return MakeResp(ErrorCode.ERR_OK)

        cli.create_child_vasp_account(account, address, authKey, currency_code = "VLS", child_initial_balance=100000, gas_currency_code="VLS")
    except ViolasError as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/account/info")
def GetAccountInfo():
    address = request.args.get("address")
    address = address.lower()

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()

    try:
        state = cli.get_account_state(address)
    except Exception as e:
        return MakeResp(ErrorCode.ERR_NODE_RUNTIME, exception = e)

    data = {"balance": state.get_balance(),
            "authentication_key": state.get_account_resource().authentication_key.hex(),
            "sequence_number": state.get_sequence_number(),
            "delegated_key_rotation_capability": state.get_account_resource().key_rotation_capability.value.account_address.hex(),
            "delegated_withdrawal_capability": state.get_account_resource().withdrawal_capability.value.account_address.hex(),
            "received_events_key": state.get_account_resource().received_events.get_key(),
            "sent_events_key": state.get_account_resource().sent_events.get_key()}

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/value/btc")
def GetBTCValue():
    url = "https://api.coincap.io/v2/assets/bitcoin"
    resp = requests.get(url)
    if not resp.ok:
        return MakeResp(ErrorCode.ERR_EXTERNAL_REQUEST)
    rate = resp.json()["data"]["priceUsd"]

    data = [{"name": "BTC", "rate": float(rate)}]

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/value/violas")
def GetViolasValue():
    address = request.args.get("address")

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeViolasClient()

    balances = cli.get_balances(address)
    currencies = []
    for currency in balances.keys():
        currencies.append(currency)

    values = []
    for currency in currencies:
        item = {}
        item["name"] = currency
        value = cli.oracle_get_exchange_rate(currency)
        item["rate"] = value.value / (2 ** 32) if value is not None else 0

        values.append(item)

    return MakeResp(ErrorCode.ERR_OK, values)

@app.route("/1.0/violas/value/libra")
def GetLibraValue():
    address = request.args.get("address")

    if not all([address]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    cli = MakeLibraClient()

    balances = cli.get_balances(address)
    currencies = []
    for currency in balances.keys():
        currencies.append(currency)

    rates = GetRates()
    values = []
    for currency in currencies:
        item = {}
        if currency == "Coin1":
            name = "USD"
        elif currency == "Coin2":
            name = "EUR"
        else:
            name = currency

        item["name"] = currency
        item["rate"] = rates.get(name) if rates.get(name) is not None else 0

        values.append(item)

    return MakeResp(ErrorCode.ERR_OK, values)

@app.route("/1.0/violas/device/info", methods = ["POST"])
def RegisterDeviceInfo():
    params = request.get_json()
    address= params.get("address")
    token = params.get("token")
    device_type = params.get("device_type")
    language = params.get("language")

    if not all([address, token, device_type, language]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ = HViolas.AddDeviceInfo(address, token, device_type, language)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    try:
        requests.post(
            "http://127.0.0.1:4006/violas/push/subscribe/topic",
            json = {"token": token, "topic": "notification"}
        )
    except:
        logging.error(f"Device: [{token}] subscribe to topic failed!")

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/messages")
def GetMessages():
    address = request.args.get("address")
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, messages = HViolas.GetMessages(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, messages)

@app.route("/1.0/violas/messages/readed", methods=["PUT"])
def SetMessagesReaded():
    params = request.get_json()
    address = params.get("address")
    messageIds = params.get("msg_ids")

    if not all([address, messageIds]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ = HViolas.SetMessagesReaded(address, messageIds)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/messages/unread/count")
def GetMessagesUnreadcount():
    address = request.args.get("address")

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, count = HViolas.GetUnreadMessagesCount(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, count)

@app.route("/1.0/violas/message/content")
def GetMessageContent():
    version = request.args.get("version", type = int)
    address = request.args.get("address")

    if not all([version]):
        MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, data = HViolas.GetTransactionByVersion(version)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    succ = HViolas.SetMessageReaded(version, address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, data)

@app.route("/1.0/violas/message", methods = ["DELETE"])
def DeleteMessage():
    messageId = request.args.get("message_id", type = int)

    succ = HViolas.DeleteMessage(messageId)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/notifications")
def GetNotifications():
    address = request.args.get("address")
    offset = request.args.get("offset", 0, int)
    limit = request.args.get("limit", 10, int)

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, messages = HViolas.GetNotifications(address, offset, limit)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, messages)

@app.route("/1.0/violas/notifications/unread/count")
def GetUnreadNotificationCount():
    address = request.args.get("address")

    if not all([address]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ, count = HViolas.GetUnreadNotificationCount(address)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK, count)

@app.route("/1.0/violas/notifications/readed", methods = ["PUT"])
def MakeNotificationReaded():
    params = request.get_json()
    address = params.get("address")
    messageIds = params.get("ids")

    if not all([address, messageIds]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    succ = HViolas.SetNotificationReaded(address, messageIds)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)

@app.route("/1.0/violas/notifications", methods = ["DELETE"])
def DeleteNotification():
    address = request.args.get("address")
    messageIds = request.args.get("ids")

    if not all([address, messageIds]):
        return MakeResp(ErrorCode.ERR_MISSING_PARAM)

    messageIds = list(map(int, messageIds.split(",")))
    succ = HViolas.DeleteNotification(address, messageIds)
    if not succ:
        return MakeResp(ErrorCode.ERR_DATABASE_CONNECT)

    return MakeResp(ErrorCode.ERR_OK)
