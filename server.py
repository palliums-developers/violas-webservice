from flask import Flask, request, redirect, url_for, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources = r"/*")

@app.route("/1.0/wallet")
def GetAuth():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/wallet/name", methods = ["POST"])
def ModifyWalletName():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/wallet/balance")
def GetBalance():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    balance = []
    info = {}
    info["address"] = "0703a61585597d9b56a46a658464738dff58222b4393d32dd9899bedb58666e9"
    info["currency"] = "libra"
    info["balance"] = 32320000
    balance.append(info)

    resp["balance"] = balance
    return resp

@app.route("/1.0/wallet/currency")
def GetCurrency():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"
    currencies = []
    info = {}
    info["name"] = "Xcoin"
    info["description"] = "desc of Xcoin"

    currencies.append(info)

    resp["currencies"] = info
    return resp

@app.route("/1.0/wallet/currency", methods = ["PUT"])
def AddCurrency():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/transaction", methods = ["POST"])
def MakeTransaction():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/transaction")
def GetTransactionInfo():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    transactions = []
    info = {}
    info["address"] = "0703a61585597d9b56a46a658464738dff58222b4393d32dd9899bedb58666e9"
    info["value"] = 100000
    info["date"] = 1572771944
    info["type"] = 1
    transactions.append(info)

    info["address"] = "0703a61585597d9b56a46a658464738dff58222b4393d32dd9899bedb58666e9"
    info["value"] = 20000
    info["date"] = 1572772342
    info["type"] = 2
    transactions.append(info)

    resp["transactions"] = transactions

    return resp

@app.route("/1.0/contacts")
def GetContacts():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    contacts = []
    info = {}
    info["name"] = "name1"
    info["address"] = "70cc09a5565432b0a69f8a3308c6fba669c1471830133b065fb27e82d07db6b4"
    contacts.append(info)

    info["name"] = "name2"
    info["address"] = "a3f842b771f8833c8550a3ce9933d5330ebb5ff9e17dad04a901fa377615d815"
    contacts.append(info)

    resp["contacts"] = contacts
    return resp

@app.route("/1.0/contacts", methods = ["POST"])
def AddContact():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp

@app.route("/1.0/authenticate", methods = ["POST"])
def Authenticate():
    resp = {}
    resp["code"] = 2000
    resp["message"] = "ok"

    return resp
