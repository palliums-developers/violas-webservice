from enum import IntEnum

class ErrorCode(IntEnum):
    ERR_OK = 2000
    ERR_ACCOUNT_DOES_NOT_EXIST = 2001
    ERR_VERIFICATION_CODE = 2002
    ERR_SEND_VERIFICATION_CODE = 2003
    ERR_SSO_INFO_DOES_NOT_EXIST = 2004
    ERR_TOKEN_INFO_DOES_NOT_EXIST = 2005
    ERR_PHONE_NUMBER_UNBOUND = 2006
    ERR_EMAIL_UNBOUND = 2007
    ERR_IMAGE_FORMAT = 2008
    ERR_VBTC_TRANSACTION_INFO = 2009
    ERR_TOKEN_NAME_DUPLICATE = 2010
    ERR_GOV_INFO_DOES_NOT_EXIST = 2011
    ERR_DATABASE_CONNECT = 2012
    ERR_INVAILED_COIN_TYPE = 2013
    ERR_UNKNOW_WALLET_TYPE = 2014
    ERR_GOV_INFO_EXISTED = 2015
    ERR_VSTAKE_ADDRESS = 2016
    ERR_VSTAKE = 2017
    ERR_CHAIRMAN_UNBIND = 2018
    ERR_SINGIN_TIMEOUT = 2019
    ERR_SIG_ERROR = 2020
    ERR_SESSION_NOT_EXIST = 2021
    ERR_NEED_REQUEST_PARAM = 2022
    ERR_CROSSCHAIN_CONNECT = 2023
    ERR_MISSING_PARAM = 2024
    ERR_INCENTIVE_RECEIVED = 2025
    ERR_REGISTER_COUNT = 2026

    ERR_GRPC_CONNECT = 3000
    ERR_INVAILED_ADDRESS = 3001

    ERR_NODE_RUNTIME = 4000

    ERR_BTC_FORWARD_REQUEST = 5000

    ERR_CLIENT_UNKNOW_ERROR = 9000

ErrorMsg = {
    ErrorCode.ERR_OK: "ok",
    ErrorCode.ERR_ACCOUNT_DOES_NOT_EXIST: "Account does not exist.",
    ErrorCode.ERR_VERIFICATION_CODE: "Verification code error.",
    ErrorCode.ERR_SEND_VERIFICATION_CODE: "Verification code send failed.",
    ErrorCode.ERR_SSO_INFO_DOES_NOT_EXIST: "SSO info does not exist.",
    ErrorCode.ERR_TOKEN_INFO_DOES_NOT_EXIST: "Token info does not exist.",
    ErrorCode.ERR_PHONE_NUMBER_UNBOUND: "Phone number unbound.",
    ErrorCode.ERR_EMAIL_UNBOUND: "Email unbound.",
    ErrorCode.ERR_IMAGE_FORMAT: "Image format is not allowed.",
    ErrorCode.ERR_VBTC_TRANSACTION_INFO: "The transaction information is incorrect.",
    ErrorCode.ERR_TOKEN_NAME_DUPLICATE: "Token name duplicate.",
    ErrorCode.ERR_GOV_INFO_DOES_NOT_EXIST: "Governor info does not exist.",
    ErrorCode.ERR_DATABASE_CONNECT: "Database connect error.",
    ErrorCode.ERR_INVAILED_COIN_TYPE: "Invailed coin type.",
    ErrorCode.ERR_UNKNOW_WALLET_TYPE: "Unknow wallet type.",
    ErrorCode.ERR_GOV_INFO_EXISTED: "Governor info had existed.",
    ErrorCode.ERR_VSTAKE_ADDRESS: "Vstake module address does not exist.",
    ErrorCode.ERR_VSTAKE: "User review process is not complete.",
    ErrorCode.ERR_CHAIRMAN_UNBIND: "Not the chairman bind account.",
    ErrorCode.ERR_SINGIN_TIMEOUT: "Timeout, session id invailed.",
    ErrorCode.ERR_SIG_ERROR: "Signature verify failed.",
    ErrorCode.ERR_SESSION_NOT_EXIST: "Session ID does not exist.",
    ErrorCode.ERR_NEED_REQUEST_PARAM: "Need request params.",
    ErrorCode.ERR_CROSSCHAIN_CONNECT: "Cross chain server connect failed.",
    ErrorCode.ERR_MISSING_PARAM: "Missing prarmeters.",
    ErrorCode.ERR_INCENTIVE_RECEIVED: "Incentive received.",
    ErrorCode.ERR_REGISTER_COUNT: "The phone number no chance.",

    ErrorCode.ERR_GRPC_CONNECT: "Grpc call failed.",
    ErrorCode.ERR_INVAILED_ADDRESS: "Invailed address.",

    ErrorCode.ERR_NODE_RUNTIME: "Node runtime error.",

    ErrorCode.ERR_BTC_FORWARD_REQUEST: "Forward BTC request failed.",

    ErrorCode.ERR_CLIENT_UNKNOW_ERROR: "Client unknow error."
}
