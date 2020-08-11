import os, random, logging, datetime, json, time, datetime
from flask import request, send_file
from werkzeug.utils import secure_filename
from redis import Redis
import requests
import nacl.signing
import hashlib

from ViolasWebservice import config
from libra_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS as LIBRA_CORE_CODE_ADDRESS
from violas_client.lbrtypes.account_config.constants.lbr import CORE_CODE_ADDRESS as VIOLAS_CORE_CODE_ADDRESS
from violas_client.lbrtypes.account_config import association_address

from libra_client.error.error import LibraError
from violas_client.error.error import LibraError as ViolasError 

from ViolasPGHandler import ViolasPGHandler
from LibraPGHandler import LibraPGHandler
from PushServerHandler import PushServerHandler
from CrossChainHandler import CrossChainHandler
from ErrorCode import ErrorCode

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
PHOTO_FOLDER = os.path.abspath("/var/www/violas_wallet/photo")
PHOTO_URL = f"{config['IMAGE SERVER']['HOST']}/1.0/violas/photo/"
ICON_URL = f"{config['IMAGE SERVER']['HOST']}/1.0/violas/icon/"

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"
HLibra = LibraPGHandler(libraDBUrl)

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"
HViolas = ViolasPGHandler(violasDBUrl)

crosschainInfo = config["CROSSCHAIN SERVER"]
HCrossChain = CrossChainHandler(crosschainInfo["HOST"])

pushInfo = config["PUSH SERVER"]
pushh = PushServerHandler(pushInfo["HOST"], int(pushInfo["PORT"]))

cachingInfo = config["CACHING SERVER"]
rdsVerify = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["VERIFYDB"], cachingInfo["PASSWORD"])
rdsCoinMap = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["COINMAPDB"], cachingInfo["PASSWORD"])
rdsAuth = Redis(cachingInfo["HOST"], cachingInfo["PORT"], cachingInfo["AUTH"], cachingInfo["PASSWORD"])

ContractAddress = "e1be1ab8360a35a0259f1c93e3eac736"

GovernorFailedReason = {
    -1: "其他",
    0: "信息不全面"
}

ChairmanFailedReason = {
    -1: "其他",
    0: "信息不全面"
}

BASEMAPINFOS = [
    {
        "type": "v2lusd",
        "chain": "violas",
        "address": "8b4ff62db5b643571507f732ae5c710068e830016798aaa8f27daf1abd5f3c4c"
    },
    {
        "type": "v2leur",
        "chain": "violas",
        "address": "e20124639b047de7285d8b733279c4750ef253cace5bf9505658a7b904a0a2c1"
    },

    {
        "type": "l2vusd",
        "chain": "libra",
        "address": "9da9b3888a469223005830a81624882456dfe238b35e1cb468d6e98a70252c00"
    },
    {
        "type": "l2veur",
        "chain": "libra",
        "address": "9da9b3888a469223005830a81624882456dfe238b35e1cb468d6e98a70252c00"
    },
    {
        "type": "l2vgbp",
        "chain": "libra",
        "address": "9da9b3888a469223005830a81624882456dfe238b35e1cb468d6e98a70252c00"
    },
    {
        "type": "l2vsgd",
        "chain": "libra",
        "address": "9da9b3888a469223005830a81624882456dfe238b35e1cb468d6e98a70252c00"
    },
    # {
    #     "type": "b2v",
    #     "lable": "",
    #     "chain": "btc",
    #     "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    # },
    {
        "type": "b2vusd",
        "lable": "0x4000",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
    {
        "type": "b2veur",
        "lable": "0x4010",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
    {
        "type": "b2vsgd",
        "lable": "0x4020",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
    {
        "type": "b2vgbp",
        "lable": "0x4030",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
    {
        "type": "b2lusd",
        "lable": "0x5000",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
    {
        "type": "b2leur",
        "lable": "0x5010",
        "chain": "btc",
        "address": "2N94SmLyWdM4TehJERqKmA2mtZ5zbbdDCTS"
    },
]
