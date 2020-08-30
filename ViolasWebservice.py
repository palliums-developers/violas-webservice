import logging, configparser
from flask import Flask
from flask_cors import CORS

logging.basicConfig(filename = "ViolasWebservice.log", level = logging.DEBUG)
config = configparser.ConfigParser()
config.read("./config.ini")

app = Flask(__name__)
CORS(app, resources = r"/*")

# LIBRA WALLET
import LibraWalletAPI
# VIOLAS WALLET
import ViolasWalletAPI
# VBTC
import VBtcAPI
# SSO
import SSOWalletAPI
# GOVERNOR
import GovernorWalletAPI
# CHAIRMAN
import ChairmanWalletAPI
# EXPLORER
import LibraExplorerAPI
import ViolasExplorerAPI
# corss chain
import CrossChainAPI
# BTC
import BtcAPI
# MARKET
import MarketAPI
import CrossChainWalletApi
# BANK
import BankAPI

# test
import index
