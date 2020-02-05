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

    ERR_GRPC_CONNECT = 3000

    ERR_NODE_RUNTIME = 4000

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

    ErrorCode.ERR_GRPC_CONNECT: "Grpc call failed.",

    ErrorCode.ERR_NODE_RUNTIME: "Node runtime error."
}
