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

from ViolasPGHandler import ViolasPGHandler
from LibraPGHandler import LibraPGHandler
from PushServerHandler import PushServerHandler

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
