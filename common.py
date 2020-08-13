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
        "type": "v2bbtc",
        "chain": "violas",
        "address": "4f93ec275410e8be891ff0fd5da41c43aee27591e222fb466654b4f983d8adbb"
    },
    {
        "type": "v2lusd",
        "chain": "violas",
        "address": "7cd40d7664d5523d360e8a1e0e2682a2dc49a7c8979f83cde4bc229fb35fd27f"
    },
    {
        "type": "v2leur",
        "chain": "violas",
        "address": "a239632a99a92e38eeade27b5e3023e22ab774f228b719991463adf0515688a9"
    },
    {
        "type": "l2bbtc",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2vusd",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2veur",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2vgbp",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "l2vsgd",
        "chain": "libra",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
    {
        "type": "b2vbtc",
        "lable": "0x3000",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2vusd",
        "lable": "0x4000",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2veur",
        "lable": "0x4010",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2vsgd",
        "lable": "0x4020",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2vgbp",
        "lable": "0x4030",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2lusd",
        "lable": "0x5000",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2leur",
        "lable": "0x5010",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2lsgd",
        "lable": "0x5020",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },
    {
        "type": "b2lgbp",
        "lable": "0x5030",
        "chain": "btc",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    }
]


MAPPING_ADDRESS_INFOS = [
    {
        "type": "v2bbtc",
        "address": "4f93ec275410e8be891ff0fd5da41c43aee27591e222fb466654b4f983d8adbb"
    },

    {
        "type": "b2vbtc",
        "lable": "0x2000",
        "address": "2N2YasTUdLbXsafHHmyoKUYcRRicRPgUyNB"
    },

    {
        "type": "l2vusd",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },

    {
        "type": "l2veur",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },

    {
        "type": "v2lusd",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },

    {
        "type": "v2leur",
        "address": "da4250b95f4d7f82d9f95ac45ea084b3c5e53097c9f82f81513d02eeb515ecce"
    },
]

