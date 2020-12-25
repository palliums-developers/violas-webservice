from time import time, sleep
from datetime import date, datetime

from ViolasModules import ViolasSSOInfo, ViolasSSOUserInfo, ViolasGovernorInfo, ViolasTransaction, ViolasAddressInfo, ViolasSignedTransaction, ViolasBankInterestInfo, ViolasBankBorrowOrder, ViolasBankDepositProduct, ViolasBankBorrowProduct, ViolasBankDepositOrder, ViolasNewRegisteredRecord, ViolasIncentiveIssueRecord
import logging
import json

from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists, distinct, join
from sqlalchemy.sql.expression import false
from sqlalchemy.exc import OperationalError
from sqlalchemy import func

from TransferType import TransferType
from util import get_show_name

class ViolasPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def AddSSOUser(self, address):
        s = self.session()

        try:
            if not s.query(exists().where(ViolasSSOUserInfo.wallet_address == address)).scalar():
                info = ViolasSSOUserInfo(wallet_address = address)

                s.add(info)
                s.commit()

            s.close()
            return True, True

        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

    def UpdateSSOUserInfo(self, data):
        s = self.session()

        try:
            result = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == data["wallet_address"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        if "name" in data:
            result.name = data["name"]

        if "country" in data:
            result.country = data["country"]

        if "id_number" in data:
            result.id_number = data["id_number"]

        if "phone_local_number" in data:
            result.phone_local_number = data["phone_local_number"]

        if "phone_number" in data:
            result.phone_number = data["phone_number"]

        if "email_address" in data:
            result.email_address = data["email_address"]

        if "id_photo_positive_url" in data:
            result.id_photo_positive_url = data["id_photo_positive_url"]

        if "id_photo_back_url" in data:
            result.id_photo_back_url = data["id_photo_back_url"]

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetSSOUserInfo(self, address):
        s = self.session()

        try:
            result = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == address).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, None

        info = {}
        info["wallet_address"] = result.wallet_address
        info["public_key"] = result.public_key
        info["name"] = result.name
        info["country"] = result.country
        info["id_number"] = result.id_number
        info["phone_local_number"] = result.phone_local_number
        info["phone_number"] = result.phone_number
        info["email_address"] = result.email_address
        info["id_photo_positive_url"] = result.id_photo_positive_url
        info["id_photo_back_url"] = result.id_photo_back_url

        s.close()
        return True, info

    def AddSSOInfo(self, data):
        s = self.session()
        timestamp = int(time())

        try:
            if not s.query(exists().where(
                    or_(and_(ViolasSSOInfo.wallet_address == data["wallet_address"], ViolasSSOInfo.token_name == data["token_name"], ViolasSSOInfo.token_type == data["token_type"], ViolasSSOInfo.approval_status == 5),
                        and_(ViolasSSOInfo.wallet_address != data["wallet_address"], ViolasSSOInfo.token_name == data["token_name"], ViolasSSOInfo.token_type == data["token_type"])))).scalar():
                info = ViolasSSOInfo(
                    wallet_address = data["wallet_address"],
                    token_type = data["token_type"],
                    amount = data["amount"],
                    token_value = data["token_value"],
                    token_name = data["token_name"],
                    application_date = timestamp,
                    validity_period = 5,
                    expiration_date = timestamp + 60 * 60 * 24 * 5,
                    reserve_photo_url = data["reserve_photo_url"],
                    account_info_photo_positive_url = data["account_info_photo_positive_url"],
                    account_info_photo_back_url = data["account_info_photo_back_url"],
                    approval_status = 0,
                    governor_address = data["governor_address"]
                )
                s.add(info)
                s.commit()
                s.close()
                return True, True
            else:
                s.close()
                return True, False
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

    def GetSSOApprovalStatus(self, address, offset, limit):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).order_by(ViolasSSOInfo.id.desc()).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            return True, None

        info = {}
        info["id"] = result.id
        info["token_type"] = result.token_type
        info["token_name"] = result.token_name
        info["approval_status"] = result.approval_status
        info["expiration_date"] = result.expiration_date
        info["token_id"] = result.token_id

        return True, info

    def GetTokenDetailInfo(self, address):
        s = self.session()

        try:
            userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == address).first()
            ssoInfo = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).order_by(ViolasSSOInfo.id.desc()).first()
            governorInfo = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == ssoInfo.governor_address).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if userInfo is None:
            return True, None
        if ssoInfo is None:
            return True, None
        if governorInfo is None:
            return True, None

        info = {}
        info["id"] = ssoInfo.id
        info["wallet_address"] = userInfo.wallet_address
        info["public_key"] = userInfo.public_key
        info["name"] = userInfo.name
        info["country"] = userInfo.country
        info["id_number"] = userInfo.id_number
        info["phone_local_number"] = userInfo.phone_local_number
        info["phone_number"] = userInfo.phone_number
        info["email_address"] = userInfo.email_address
        info["token_type"] = ssoInfo.token_type
        info["token_id"] = ssoInfo.token_id
        info["amount"] = int(ssoInfo.amount)
        info["token_value"] = int(ssoInfo.token_value)
        info["token_name"] = ssoInfo.token_name
        info["application_date"] = ssoInfo.application_date
        info["validity_period"] = ssoInfo.validity_period
        info["expiration_date"] = ssoInfo.expiration_date
        info["reserve_photo_url"] = ssoInfo.reserve_photo_url
        info["account_info_photo_positive_url"] = ssoInfo.account_info_photo_positive_url
        info["account_info_photo_back_url"] = ssoInfo.account_info_photo_back_url
        info["approval_status"] = ssoInfo.approval_status
        info["failed_reason"] = ssoInfo.failed_reason
        info["remarks"] = ssoInfo.remarks
        info["governor_address"] = ssoInfo.governor_address
        info["governor_name"] = governorInfo.name

        return True, info

    def GetUnapprovalTokenDetailInfo(self, address, id):
        s = self.session()

        try:
            ssoInfo = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == id).first()
            userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == ssoInfo.wallet_address).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if userInfo is None:
            return True, None

        if ssoInfo is None:
            return True, None

        info = {}
        info["id"] = ssoInfo.id
        info["wallet_address"] = userInfo.wallet_address
        info["public_key"] = userInfo.public_key
        info["name"] = userInfo.name
        info["country"] = userInfo.country
        info["id_number"] = userInfo.id_number
        info["phone_local_number"] = userInfo.phone_local_number
        info["phone_number"] = userInfo.phone_number
        info["email_address"] = userInfo.email_address
        info["token_type"] = ssoInfo.token_type
        info["token_id"] = ssoInfo.token_id
        info["amount"] = int(ssoInfo.amount)
        info["token_value"] = int(ssoInfo.token_value)
        info["token_name"] = ssoInfo.token_name
        info["application_date"] = ssoInfo.application_date
        info["validity_period"] = ssoInfo.validity_period
        info["expiration_date"] = ssoInfo.expiration_date
        info["reserve_photo_url"] = ssoInfo.reserve_photo_url
        info["account_info_photo_positive_url"] = ssoInfo.account_info_photo_positive_url
        info["account_info_photo_back_url"] = ssoInfo.account_info_photo_back_url
        info["approval_status"] = ssoInfo.approval_status
        info["failed_reason"] = ssoInfo.failed_reason
        info["remarks"] = ssoInfo.remarks

        return True, info

    def SetTokenPublished(self, address, id):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).filter(ViolasSSOInfo.id == id).filter(ViolasSSOInfo.approval_status == 3).first()

            if result is None:
                s.close()
                return True, False

            result.approval_status = 4
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetUnapprovalSSO(self, address, offset, limit):
        s = self.session()

        try:
            ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.governor_address == address).filter(ViolasSSOInfo.approval_status == 0).offset(offset).limit(limit).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in ssoInfos:
            try:
                userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == i.wallet_address).first()
            except OperationalError:
                logging.error(f"ERROR: Database operation failed!")
                s.close()
                return False, None

            info = {}
            info["wallet_address"] = userInfo.wallet_address
            info["name"] = userInfo.name
            info["country"] = userInfo.country
            info["id_number"] = userInfo.id_number
            info["phone_local_number"] = userInfo.phone_local_number
            info["phone_number"] = userInfo.phone_number
            info["email_address"] = userInfo.email_address
            info["id_photo_positive_url"] = userInfo.id_photo_positive_url
            info["id_photo_back_url"] = userInfo.id_photo_back_url
            info["token_type"] = i.token_type
            info["amount"] = int(i.amount)
            info["token_value"] = int(i.token_value)
            info["token_name"] = i.token_name
            info["application_date"] = i.application_date
            info["validity_period"] = i.validity_period
            info["expiration_date"] = i.expiration_date
            info["reserve_photo_url"] = i.reserve_photo_url
            info["account_info_photo_positive_url"] = i.account_info_photo_positive_url
            info["account_info_photo_back_url"] = i.account_info_photo_back_url
            info["approval_status"] = i.approval_status
            info["failed_reason"] = i.failed_reason
            info["remarks"] = i.remarks

            infos.append(info)

        s.close()
        return True, infos

    def SetApprovalStatus(self, id, status, reason = None, remarks = None):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == id).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        result.approval_status = status

        if reason is not None:
            result.failed_reason = reason
        if remarks is not None:
            result.remarks = remarks

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def SetTokenMinted(self, data):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == data["wallet_address"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        result.approval_status = 4

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def SetTokenMintedV2(self, data):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == data["id"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        result.approval_status = 4

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetGovernorInfoList(self, offset, limit):
        s = self.session()

        try:
            govInfos = s.query(ViolasGovernorInfo).order_by(ViolasGovernorInfo.id).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in govInfos:
            info = {}
            info["toxid"] = i.toxid
            info["name"] = i.name
            info["public_key"] = i.btc_public_key
            info["wallet_address"] = i.wallet_address
            info["vstake_address"] = i.vstake_address
            info["multisig_address"] = i.multisig_address
            info["is_chairman"] = i.is_chairman
            info["violas_public_key"] = i.wallet_public_key

            infos.append(info)

        return True, infos

    def GetGovernorInfoAboutAddress(self, address):
        s = self.session()

        try:
            govInfos = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == address).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if govInfos is None:
            return True, None

        info = {}
        info["toxid"] = govInfos.toxid
        info["name"] = govInfos.name
        info["btc_public_key"] = govInfos.btc_public_key
        info["wallet_address"] = govInfos.wallet_address
        info["vstake_address"] = govInfos.vstake_address
        info["multisig_address"] = govInfos.multisig_address
        info["is_chairman"] = govInfos.is_chairman
        info["status"] = govInfos.is_handle
        info["wallet_public_key"] = govInfos.wallet_public_key

        return True, info

    def AddGovernorInfo(self, data):
        s = self.session()

        if data["is_chairman"] == 0:
            isChairman = False
        else:
            isChairman = True

        try:
            if not s.query(exists().where(ViolasGovernorInfo.wallet_address == data["wallet_address"])).scalar():
                info = ViolasGovernorInfo(
                    wallet_address = data["wallet_address"],
                    toxid = data["toxid"],
                    name = data["name"],
                    btc_public_key = data["btc_public_key"],
                    vstake_address = data["vstake_address"],
                    multisig_address = data["multisig_address"],
                    is_chairman = isChairman,
                    is_handle = 0,
                    wallet_public_key = data["wallet_public_key"]
                )

                s.add(info)
                s.commit()
            else:
                s.close()
                return True, False
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def AddGovernorInfoForFrontEnd(self, data):
        s = self.session()

        try:
            if not s.query(exists().where(ViolasGovernorInfo.wallet_address == data["wallet_address"])).scalar():
                info = ViolasGovernorInfo(
                    wallet_address = data["wallet_address"],
                    name = data["name"],
                    btc_txid = data["txid"],
                    toxid = data.get("toxid"),
                    is_chairman = False,
                    is_handle = 0,
                    application_date = int(time()),
                    wallet_public_key = data["public_key"]
                )

                s.add(info)
                s.commit()
            else:
                s.close()
                return True, False
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def ModifyGovernorInfo(self, data):
        s = self.session()

        try:
            result = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == data["wallet_address"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        if "toxid" in data:
            result.toxid = data["toxid"]
        if "name" in data:
            result.name = data["name"]
        if "public_key" in data:
            result.btc_public_key = data["public_key"]
        if "vstake_address" in data:
            result.vstake_address = data["vstake_address"]
        if "multisig_address" in data:
            result.multisig_address = data["multisig_address"]
        if "btc_txid" in data:
            result.btc_txid = data["btc_txid"]
            result.application_date = int(time())
        if "is_handle" in data:
            result.is_handle = data["is_handle"]

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetInvestmentedGovernorInfo(self):
        s = self.session()

        try:
            result = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.btc_txid.isnot(None)).order_by(ViolasGovernorInfo.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in result:
            info = {}
            info["toxid"] = i.toxid
            info["name"] = i.name
            info["btc_public_key"] = i.btc_public_key
            info["wallet_public_key"] = i.wallet_public_key
            info["wallet_address"] = i.wallet_address
            info["vstake_address"] = i.vstake_address
            info["multisig_address"] = i.multisig_address
            info["btc_txid"] = i.btc_txid
            info["application_date"] = i.application_date
            info["is_handle"] = i.is_handle

            infos.append(info)

        return True, infos

    def GetCurrencies(self):
        s = self.session()

        try:
            ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.approval_status == 4).order_by(ViolasSSOInfo.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        currencies = []
        for i in ssoInfos:
            currency = {}
            currency["name"] = i.token_name + i.token_type
            currency["address"] = i.module_address
            currency["description"] = i.token_name

            currencies.append(currency)

        return True, currencies

    # explorer db handle function
    def GetRecentTransaction(self, limit, offset):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency

            infoList.append(info)

        return True, infoList

    def GetRecentTransactionAboutCurrency(self, limit, offset, currency):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.currency == currency).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency

            infoList.append(info)

        return True, infoList

    def GetAddressInfo(self, address):
        s = self.session()

        try:
            result = s.query(ViolasAddressInfo).filter(ViolasAddressInfo.address == address).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        if result is None:
            return True, None
        else:
            info = {}
            info["type"] = result.type
            info["first_seen"] = result.first_seen
            info["sent_amount"] = int(result.sent_amount)
            info["received_amount"] = int(result.received_amount)
            info["sent_tx_count"] = result.sent_tx_count
            info["received_tx_count"] = result.received_tx_count
            info["sent_minted_tx_count"] = result.sent_minted_tx_count
            info["received_minted_tx_count"] = result.received_minted_tx_count
            info["sent_failed_tx_count"] = result.sent_failed_tx_count
            info["received_failed_tx_count"] = result.received_failed_tx_count

            return True, info

    def GetTransactionsByAddress(self, address, limit, offset):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency
            info["confirmed_time"] = i.confirmed_time

            infoList.append(info)

        return True, infoList

    def GetTransactionsByAddressAboutCurrency(self, address, limit, offset, currency):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.currency == currency).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency
            info["confirmed_time"] = i.confirmed_time

            infoList.append(info)

        return True, infoList

    def GetTransactionByVersion(self, version):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.id == (version + 1)).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        info = {}
        info["version"] = result.id - 1
        info["type"] = result.transaction_type
        info["sequence_number"] = result.sequence_number
        info["sender"] = result.sender
        info["receiver"] = result.receiver
        info["currency"] = result.currency
        info["gas_currency"] = result.gas_currency
        info["amount"] = int(result.amount)
        info["gas"] = int(result.gas_used * i.gas_unit_price)
        info["gas_unit_price"] = int(result.gas_unit_price)
        info["max_gas_amount"] = int(result.max_gas_amount)
        info["expiration_time"] = result.expiration_time
        info["public_key"] = result.public_key
        info["signature"] = result.signature
        info["status"] = result.status
        info["data"] = result.data
        info["confirmed_time"] = result.confirmed_time

        return True, info

    def GetTransactionCount(self):
        s = self.session()

        try:
            result = s.query(ViolasTransaction.id).order_by(ViolasTransaction.id.desc()).limit(1).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        if result is None:
            result = 0
        else:
            result = result[0]

        return True, result

    def VerifyTransactionAboutVBtc(self, data):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.id == data["version"] + 1).first()
            s.close()
        except OperationalError:
            s.close()
            return False, False

        if result is None:
            return True, False

        if result.sender != data["sender_address"]:
            return True, False

        if result.sequence_number != data["sequence_number"]:
            return True, False

        if int(result.amount) != data["amount"]:
            return True, False

        try:
            res = result.data.rsplit(":", 1)
            if res[0] != "v2b:btc_address":
                return True, False

            if res[1] != data["btc_address"]:
                return True, False
        except:
            return True, False

        if result.module != data["module"]:
            return True, False

        if result.receiver != data["receiver"]:
            return True, False

        return True, True

    def GetTransactionsAboutVBtc(self, address, module, start_version):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.module == module).filter(ViolasTransaction.id >= (start_version + 1)).order_by(ViolasTransaction.id).limit(10).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["sender_address"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["amount"] = int(i.amount)
            info["version"] = i.id - 1

            if i.data is None:
                continue

            try:
                res = i.data.rsplit(":", 1)
                if res[0] != "v2b:btc_address":
                    continue

                info["btc_address"] = res[1]
            except:
                continue

            infoList.append(info)

        return True, infoList

    def GetTransactionsAboutGovernor(self, address, start_version, limit):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.id > (start_version + 1)).order_by(ViolasTransaction.id).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["max_gas_amount"] = int(i.max_gas_amount)
            info["gas_unit_price"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["transaction_type"] = i.transaction_type
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["module_address"] = i.module
            info["data"] = i.data
            info["public_key"] = i.public_key
            info["signature"] = i.signature
            info["transaction_hash"] = i.transaction_hash
            info["state_root_hash"] = i.state_root_hash
            info["event_root_hash"] = i.event_root_hash
            info["gas_used"] = int(i.gas_used)
            info["status"] = i.status

            infoList.append(info)

        return True, infoList

    def GetTransactionsForWallet(self, address, currency, flows, offset, limit):
        s = self.session()
        types = TransferType.keys()
        try:
            if currency is None:
                if flows is None:
                    result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 0:
                    result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 1:
                    result = s.query(ViolasTransaction).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
            else:
                if flows is None:
                    result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.currency == currency).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 0:
                    result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(ViolasTransaction.currency == currency).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 1:
                    result = s.query(ViolasTransaction).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.currency == currency).filter(ViolasTransaction.transaction_type.in_(types)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["type"] = TransferType.get(i.transaction_type)
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["currency"] = i.currency
            info["gas_currency"] = i.gas_currency
            info["status"] = i.status
            info["confirmed_time"] = i.confirmed_time

            infoList.append(info)

        s.close()
        return True, infoList

    def GetGovernorInfoForSSO(self):
        s = self.session()

        try:
            govInfos = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.is_handle == 4).order_by(ViolasGovernorInfo.id).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infos = []
        for i in govInfos:
            info = {}
            info["name"] = i.name
            info["wallet_address"] = i.wallet_address

            infos.append(info)

        return True, infos

    def GetExchangeTransactionCountFrom(self, address, exchangeAddress, exchangeModule):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(ViolasTransaction.receiver == exchangeAddress).filter(ViolasTransaction.token_id == exchangeModule).count()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        return True, result

    def GetExchangeTransactionCountTo(self, address, exchangeAddress, exchangeModule):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == exchangeAddress).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.token_id == exchangeModule).count()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        return True, result

    def GetMapTransactionInfo(self, sender, receiver, moduleMap, offset, limit):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == sender).filter(ViolasTransaction.receiver == receiver).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infos = []
        for i in result:
            info = {}
            info["date"] = i.expiration_time
            info["amount"] = int(i.amount)
            info["address"] = receiver
            info["coin"] = moduleMap.get(i.module)
            info["status"] = 0

            infos.append(info)

        return True, infos

    def GetVstakeModuleAddress(self):
        s = self.session()

        try:
            result = s.query(ViolasGovernorInfo.vstake_address).filter(ViolasGovernorInfo.is_chairman == True).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        if result == None:
            return True, None

        return True, result[0]

    def SetMintInfoV2(self, data):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == data["id"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            s.close()
            return True, False

        result.approval_status = data["approval_status"]
        result.module_address = data["module_address"]
        result.subaccount_number = data["subaccount_number"]

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetUnapprovalSSOList(self, address, limit, offset):
        s = self.session()

        try:
            ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in ssoInfos:
            try:
                userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == i.wallet_address).first()
            except OperationalError:
                logging.error(f"ERROR: Database operation failed!")
                s.close()
                return False, None

            info = {}
            info["id"] = i.id
            info["name"] = userInfo.name
            info["approval_status"] = i.approval_status
            info["application_date"] = i.application_date
            info["expiration_date"] = i.expiration_date

            infos.append(info)

        s.close()
        return True, infos

    def ChairmanBindGovernor(self, data):
        s = self.session()

        try:
            info = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == data["address"]).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        info.bind_governor = data["governor_address"]

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def CheckBind(self, address):
        s = self.session()

        try:
            info = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.is_chairman == True).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()

        if info.bind_governor == address:
            return True, True
        else:
            return True, False

    def GetUnapprovalSSOListForChairman(self, offset, limit):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.approval_status == 1).offset(offset).limit(limit).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in result:
            try:
                governorInfo = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == i.governor_address).first()
            except OperationalError:
                logging.error(f"ERROR: Database operation failed!")
                s.close()
                return False, None

            info = {}
            info["id"] = i.id
            info["name"] = governorInfo.name
            info["application_date"] = i.application_date
            info["approval_status"] = i.approval_status

            infos.append(info)

        s.close()
        return True, infos

    def GetTokenDetailInfoForChairman(self, address, id):
        s = self.session()

        try:
            ssoInfo = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == id).first()
            governorInfo = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == ssoInfo.governor_address).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        info = {}
        info["id"] = ssoInfo.id
        info["governor_name"] = governorInfo.name
        info["txid"] = governorInfo.btc_txid
        info["wallet_address"] = governorInfo.wallet_address
        info["public_key"] = governorInfo.wallet_public_key
        info["token_type"] = ssoInfo.token_type
        info["token_amount"] = int(ssoInfo.amount)
        info["token_value"] = int(ssoInfo.token_value)
        info["token_name"] = ssoInfo.token_name
        info["reserve_photo_url"] = ssoInfo.reserve_photo_url

        return True, info

    def SetTokenID(self, id, token_id):
        s = self.session()

        try:
            ssoInfo = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == id).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if ssoInfo is None:
            s.close()
            return True, False

        ssoInfo.token_id = token_id

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True
    def SetGovernorStatus(self, address, is_handle):
        s = self.session()

        try:
            governorInfo = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == address).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if governorInfo is None:
            s.close()
            return True, False

        governorInfo.is_handle = is_handle

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()

        return True, True

    def GetMarketExchangeTransaction(self, address, offset, limit):
        s = self.session()

        try:
            transactions = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(ViolasTransaction.transaction_type == "SWAP").order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        infos = []
        for i in transactions:
            info = {}
            event = {}
            info["version"] = i.id - 1
            info["date"] = i.expiration_time
            info["status"] = i.status
            info["confirmed_time"] = i.confirmed_time


            if i.event is not None:
                event = json.loads(i.event)
                info["input_name"] = event.get("input_name")
                info["output_name"] = event.get("output_name")
                info["input_amount"] = event.get("input_amount")
                info["output_amount"] = event.get("output_amount")
                info["input_show_name"] = get_show_name(info["input_name"])
                info["output_show_name"] = get_show_name(info["output_name"])

            else:
                txnInfo = s.query(ViolasSignedTransaction).filter(ViolasSignedTransaction.sender == address).filter(ViolasSignedTransaction.sequence_number == i.sequence_number).first()
                if txnInfo is not None:
                    sigTxn = json.loads(txnInfo.sigtxn)
                    info["input_name"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][0]["Struct"]["module"]
                    info["output_name"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][1]["Struct"]["module"]
                    info["input_amount"] = sigTxn["raw_txn"]["payload"]["Script"]["args"][1]["U64"]
                    info["output_amount"] = 0
                    info["input_show_name"] = get_show_name(info["input_name"])
                    info["output_show_name"] = get_show_name(info["output_name"])

            info["gas_used"] = int(i.gas_used * i.gas_unit_price)
            info["gas_currency"] = i.gas_currency

            infos.append(info)

        return True, infos

    def GetMarketPoolTransaction(self, address, offset, limit):
        s = self.session()
        try:
            transactions = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(or_(ViolasTransaction.transaction_type == "REMOVE_LIQUIDITY", ViolasTransaction.transaction_type == "ADD_LIQUIDITY")).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None
        infos = []
        for i in transactions:
            info = {}
            event = {}
            info["version"] = i.id - 1
            info["date"] = i.expiration_time
            info["status"] = i.status
            info["transaction_type"] = i.transaction_type
            info["confirmed_time"] = i.confirmed_time

            if i.event is not None:
                event = json.loads(i.event)
                if i.transaction_type == "REMOVE_LIQUIDITY":
                    info["coina"] = event.get("coina")
                    info["coinb"] = event.get("coinb")
                    info["amounta"] = event.get("withdraw_amounta")
                    info["amountb"] = event.get("withdraw_amountb")
                    info["token"] = event.get("burn_amount")
                    info["coina_show_name"] = get_show_name(info["coina"])
                    info["coinb_show_name"] = get_show_name(info["coinb"])
                else:
                    info["coina"] = event.get("coina")
                    info["coinb"] = event.get("coinb")
                    info["amounta"] = event.get("deposit_amounta")
                    info["amountb"] = event.get("deposit_amountb")
                    info["token"] = event.get("mint_amount")
                    info["coina_show_name"] = get_show_name(info["coina"])
                    info["coinb_show_name"] = get_show_name(info["coinb"])
            else:
                txnInfo = s.query(ViolasSignedTransaction).filter(ViolasSignedTransaction.sender == address).filter(ViolasSignedTransaction.sequence_number == i.sequence_number).first()
                if txnInfo is not None:
                    sigTxn = json.loads(txnInfo.sigtxn)
                    if i.transaction_type == "REMOVE_LIQUIDITY":
                        info["coina"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][0]["Struct"]["module"]
                        info["coinb"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][0]["Struct"]["module"]
                        info["amounta"] = 0
                        info["amountb"] = 0
                        info["token"] = sigTxn["raw_txn"]["payload"]["Script"]["args"][0]["U64"]
                        info["coina_show_name"] = get_show_name(info["coina"])
                        info["coinb_show_name"] = get_show_name(info["coinb"])
                    else:
                        info["coina"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][0]["Struct"]["module"]
                        info["coinb"] = sigTxn["raw_txn"]["payload"]["Script"]["ty_args"][1]["Struct"]["module"]
                        info["amounta"] = sigTxn["raw_txn"]["payload"]["Script"]["args"][0]["U64"]
                        info["amountb"] = sigTxn["raw_txn"]["payload"]["Script"]["args"][1]["U64"]
                        info["coina_show_name"] = get_show_name(info["coina"])
                        info["coinb_show_name"] = get_show_name(info["coinb"])
                        info["token"] = 0
            info["gas_used"] = int(i.gas_used * i.gas_unit_price)
            info["gas_currency"] = i.gas_currency


            infos.append(info)

        return True, infos

    def AddTransactionInfo(self, sender, seqNum, timestamp, sigtxn):
        s = self.session()

        try:
            info = ViolasSignedTransaction(
                sender = sender,
                sequence_number = seqNum,
                time = timestamp,
                sigtxn = sigtxn)

            s.add(info)
            s.commit()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False

        return True

    def GetYesterdayIncome(self, address):
        s = self.session()
        today = datetime.strptime(str(date.today()), '%Y-%m-%d')
        timestamp = datetime.timestamp(today)

        try:
            info = s.query(ViolasBankInterestInfo.interest, ViolasBankInterestInfo.total_interest).filter(ViolasBankInterestInfo.address == address).filter(ViolasBankInterestInfo.date > timestamp).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        return True, info

    def GetBorrowedToday(self, address):
        s = self.session()
        today = datetime.strptime(str(date.today()), '%Y-%m-%d')
        timestamp = datetime.timestamp(today)

        try:
            info = s.query(ViolasBankBorrowOrder.value).filter(ViolasBankBorrowOrder.address == address).filter(ViolasBankBorrowOrder.order_type == 0).filter(ViolasBankBorrowOrder.date >= timestamp).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        return True, info

    def GetDepositProductList(self):
        s = self.session()

        try:
            res = s.query(ViolasBankDepositProduct).order_by(ViolasBankDepositProduct.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        datas = []
        for i in res:
            item = {}
            item['id'] = i.product_id
            item['logo'] = i.logo
            item['name'] = i.product_name
            item['desc'] = i.description
            item['rate'] = float(i.rate)
            item['rate_desc'] = i.rate_desc
            item['token_module'] = i.currency

            datas.append(item)

        return True, datas

    def GetBorrowProductList(self):
        s = self.session()

        try:
            res = s.query(ViolasBankBorrowProduct).order_by(ViolasBankBorrowProduct.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        datas = []
        for i in res:
            item = {}
            item['id'] = i.product_id
            item['logo'] = i.logo
            item['name'] = i.product_name
            item['desc'] = i.description
            item['rate'] = float(i.rate)
            item['rate_desc'] = i.rate_desc
            item['token_module'] = i.currency

            datas.append(item)

        return True, datas

    def GetDepositProductDetail(self, productId):
        s = self.session()

        try:
            result = s.query(ViolasBankDepositProduct).filter(ViolasBankDepositProduct.product_id == productId).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            return True, None

        data = {}
        data['id'] = result.product_id
        data['name'] = result.product_name
        data['logo'] = result.logo
        data['minimum_amount'] = result.minimum_amount
        data['minimum_step'] = result.minimum_step
        data['quota_limit'] = result.max_limit
        data['rate'] = float(result.rate)
        data['rate_desc'] = result.rate_desc
        data['pledge_rate'] = float(result.pledge_rate)
        data['intor'] = json.loads(result.intor)
        data['question'] = json.loads(result.question)
        data['token_module'] = result.currency

        return True, data

    def GetDepositQuotaToday(self, address, productId):
        s = self.session()
        today = datetime.strptime(str(date.today()), '%Y-%m-%d')
        timestamp = datetime.timestamp(today)

        try:
            result = s.query(ViolasBankDepositOrder.value, ViolasBankDepositOrder.order_type).filter(ViolasBankDepositOrder.status == 0).filter(ViolasBankDepositOrder.address == address).filter(ViolasBankDepositOrder.product_id == productId).filter(ViolasBankDepositOrder.date >= timestamp).order_by(ViolasBankDepositOrder.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        quota = 0
        for idx, i in enumerate(result):
            if i[1] == 0:
                quota += i[0]
            elif i[1] == 1:
                if idx == 0 or quota == 0:
                    continue
                else:
                    quota -= i[0]
                    if quota < 0:
                        quota = 0


        return True, quota

    def GetOrderedProducts(self, address):
        s = self.session()

        try:
            result = s.query(ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).distinct().all()
            s.close();
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        products = []
        for i in result:
            products.append(i[0])

        return True, products

    def GetDepositOrderInfo(self, address, productId):
        s = self.session()

        try:
            order = s.query(ViolasBankDepositOrder).filter(ViolasBankDepositOrder.address == address).filter(ViolasBankDepositOrder.product_id == productId).order_by(ViolasBankDepositOrder.id.desc()).first()

            product = s.query(ViolasBankDepositProduct).filter(ViolasBankDepositProduct.product_id == productId).first()

            interest = s.query(ViolasBankInterestInfo).filter(ViolasBankInterestInfo.address == address).filter(ViolasBankInterestInfo.product_id == productId).order_by(ViolasBankInterestInfo.id.desc()).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if order is None:
            return True, None

        info = {}
        info['id'] = productId
        info['logo'] = product.logo
        info['currency'] = product.currency
        info['principal'] = order.total_value
        info['earnings'] = interest.total_interest if interest is not None else 0
        info['rate'] = float(product.rate)
        if order.total_value != 0:
            info['status'] = 0
        else:
            info['status'] = 1

        return True, info

    def GetAllDepositOfProduct(self, address, productId):
        s = self.session()

        try:
            order = s.query(ViolasBankDepositOrder).filter(ViolasBankDepositOrder.address == address).filter(ViolasBankDepositOrder.product_id == productId).order_by(ViolasBankDepositOrder.id.desc()).first()
            product = s.query(ViolasBankDepositProduct).filter(ViolasBankDepositProduct.product_id == productId).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None, None

        if order is None:
            return True, None, None

        return True, order.total_value, product.currency

    def GetDepositOrderList(self, address, offset, limit, currency = None, status = None, startTime = None, endTime = None):
        s = self.session()
        try:
            if currency is None and status is None:
                orders = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).all()
                count = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).count()
            elif status is None:
                orders = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositProduct.currency == currency).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).all()
                count =  s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositProduct.currency == currency).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).count()
            elif currency is None:
                orders = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositOrder.order_type == status).filter(ViolasBankDepositOrder.status == 0).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).all()
                count = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositOrder.order_type == status).filter(ViolasBankDepositOrder.status == 0).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).count()
            else:
                orders = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositProduct.currency == currency).filter(ViolasBankDepositOrder.order_type == status).filter(ViolasBankDepositOrder.status == 0).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).all()
                count = s.query(ViolasBankDepositOrder.order_id, ViolasBankDepositOrder.date, ViolasBankDepositOrder.order_type, ViolasBankDepositOrder.status, ViolasBankDepositProduct.logo, ViolasBankDepositProduct.currency, ViolasBankDepositOrder.value).filter(ViolasBankDepositProduct.currency == currency).filter(ViolasBankDepositOrder.order_type == status).filter(ViolasBankDepositOrder.status == 0).join(ViolasBankDepositProduct, ViolasBankDepositProduct.product_id == ViolasBankDepositOrder.product_id).filter(ViolasBankDepositOrder.address == address).order_by(ViolasBankDepositOrder.id.desc()).count()

            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None, None

        result = []
        for idx, order in enumerate(orders):
            if startTime is not None:
                if order[1] < startTime:
                    count -= 1
                    continue

            if endTime is not None:
                if order[1] > endTime:
                    count -= 1
                    continue

            if idx >= offset and idx < (offset + limit):
                item = {}
                item['id'] = order[0]
                item['date'] = order[1]
                if order[2] == 0 and order[3] == 0:
                    item['status'] = 0
                elif order[2] == 1 and order[3] == 0:
                    item['status'] = 1
                elif order[2] == 0 and order[3] == -1:
                    item['status'] = -1
                elif order[2] == 1 and order[3] == -1:
                    item['status'] = -2

                item['logo'] = order[4]
                item['currency'] = order[5]
                item['value'] = order[6]

                result.append(item)

        return True, result, count

    def GetBorrowProductDetail(self, productId):
        s = self.session()

        try:
            result = s.query(ViolasBankBorrowProduct).filter(ViolasBankBorrowProduct.product_id == productId).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is None:
            return True, None

        data = {}
        data['id'] = result.product_id
        data['name'] = result.product_name
        data['logo'] = result.logo
        data['minimum_amount'] = result.minimum_amount
        data['minimum_step'] = result.minimum_step
        data['quota_limit'] = result.max_limit
        data['rate'] = float(result.rate)
        data['pledge_rate'] = float(result.pledge_rate)
        data['intor'] = json.loads(result.intor)
        data['question'] = json.loads(result.question)
        data['token_module'] = result.currency

        return True, data

    def GetBorrowQuotaToday(self, address, productId):
        s = self.session()
        today = datetime.strptime(str(date.today()), '%Y-%m-%d')
        timestamp = datetime.timestamp(today)

        try:
            result = s.query(ViolasBankBorrowOrder.value, ViolasBankBorrowOrder.order_type).filter(ViolasBankBorrowOrder.status == 0).filter(ViolasBankBorrowOrder.address == address).filter(ViolasBankBorrowOrder.product_id == productId).filter(ViolasBankBorrowOrder.date >= timestamp).order_by(ViolasBankBorrowOrder.id).all()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        quota = 0
        for idx, i in enumerate(result):
            if i[0] == 0:
                quota += i[0]
            elif i[0] == 1:
                if idx == 0 or quota == 0:
                    continue
                else:
                    quota -= i[0]
                    if quota < 0:
                        quota = 0

        return True, quota

    def GetBorrowOrderedProducts(self, address):
        s = self.session()

        try:
            result = s.query(ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).distinct().all()
            s.close();
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        products = []
        for i in result:
            products.append(i[0])

        return True, products

    def GetBorrowOrderInfo(self, address, productId):
        s = self.session()

        try:
            order = s.query(ViolasBankBorrowOrder).filter(ViolasBankBorrowOrder.address == address).filter(ViolasBankBorrowOrder.product_id == productId).order_by(ViolasBankBorrowOrder.id.desc()).first()

            product = s.query(ViolasBankBorrowProduct).filter(ViolasBankBorrowProduct.product_id == productId).first()

            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None
        if order is None:
            return True, None

        info = {}
        info['id'] = productId
        info['logo'] = product.logo
        info['name'] = product.currency
        info['amount'] = order.total_value

        return True, info

    def GetBorrowOrderList(self, address, offset, limit, currency = None, status = None, startTime = None, endTime = None):
        s = self.session()
        try:
            if currency is None and status is None:
                orders = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).all()
                count = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).count()
            elif status is None:
                orders = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowProduct.currency == currency).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).all()
                count = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowProduct.currency == currency).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).count()
            elif currency is None:
                orders = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowOrder.order_type == status).filter(ViolasBankBorrowOrder.status == 0).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).all()
                count = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowOrder.order_type == status).filter(ViolasBankBorrowOrder.status == 0).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).count()
            else:
                orders = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowProduct.currency == currency).filter(ViolasBankBorrowOrder.order_type == status).filter(ViolasBankBorrowOrder.status == 0).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).all()
                count = s.query(ViolasBankBorrowOrder.order_id, ViolasBankBorrowOrder.date, ViolasBankBorrowOrder.order_type, ViolasBankBorrowOrder.status, ViolasBankBorrowProduct.logo, ViolasBankBorrowProduct.currency, ViolasBankBorrowOrder.value).filter(ViolasBankBorrowProduct.currency == currency).filter(ViolasBankBorrowOrder.order_type == status).filter(ViolasBankBorrowOrder.status == 0).join(ViolasBankBorrowProduct, ViolasBankBorrowProduct.product_id == ViolasBankBorrowOrder.product_id).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).count()

            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None, None

        result = []
        for idx, order in enumerate(orders):
            if startTime is not None:
                if order[1] < startTime:
                    count -= 1
                    continue

            if endTime is not None:
                if order[1] > endTime:
                    count -= 1
                    continue

            if idx >= offset and idx < (offset + limit):
                item = {}
                item['id'] = order[0]
                item['date'] = order[1]
                if order[2] == 0 and order[3] == 0:
                    item['status'] = 0
                elif order[2] == 1 and order[3] == 0:
                    item['status'] = 1
                elif order[2] == 2 and order[3] == 0:
                    item['status'] = 2
                elif order[2] == 0 and order[3] == -1:
                    item['status'] = -1
                elif order[2] == 1 and order[3] == -1:
                    item['status'] = -2

                item['logo'] = order[4]
                item['currency'] = order[5]
                item['value'] = order[6]

                result.append(item)

        return True, result, count

    def GetBorrowOrderDetail(self, address, productId):
        s = self.session()

        try:
            order = s.query(ViolasBankBorrowOrder).filter(ViolasBankBorrowOrder.address == address).filter(ViolasBankBorrowOrder.product_id == productId).order_by(ViolasBankBorrowOrder.id.desc()).first()
            product = s.query(ViolasBankBorrowProduct).filter(ViolasBankBorrowProduct.product_id == productId).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if order is None:
            return True, None

        data = {
            'id': order.order_id,
            'name': product.currency,
            'balance': order.total_value
        }

        return True, data

    def GetBorrowOrderDetailList(self, address, productId, q, offset, limit):
        s = self.session()

        try:
            orders = s.query(ViolasBankBorrowOrder).filter(ViolasBankBorrowOrder.address == address).filter(ViolasBankBorrowOrder.product_id == productId).filter(ViolasBankBorrowOrder.order_type == q).order_by(ViolasBankBorrowOrder.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        orderList = []
        if q == 2:
            for o in orders:
                item = {}
                item['date'] = o.date
                item['cleared'] = o.value
                item['deductioned'] = o.deductioned
                item['deductioned_currency'] = o.deductioned_currency
                item['status'] = 2

                orderList.append(item)
        else:
            for o in orders:
                item = {}
                item['date'] = o.date
                item['amount'] = o.value
                if o.order_type == 0 and o.status == 0:
                    item['status'] = 0
                elif o.order_type == 1 and o.status == 0:
                    item['status'] = 1
                elif o.order_type == 0 and o.status == -1:
                    item['status'] = -1
                elif o.order_type == 1 and o.status == -1:
                    item['status'] = -1

                orderList.append(item)

        return True, orderList

    def GetBorrowOrderRepayInfo(self, address, productId):
        s = self.session()

        try:
            order = s.query(ViolasBankBorrowOrder).filter(ViolasBankBorrowOrder.product_id == productId).filter(ViolasBankBorrowOrder.address == address).order_by(ViolasBankBorrowOrder.id.desc()).first()

            if order is None:
                s.close()
                return True, None

            product = s.query(ViolasBankBorrowProduct).filter(ViolasBankBorrowProduct.product_id == productId).first()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        data = {
            'balance': order.total_value,
            'rate': float(product.pledge_rate),
            'logo': product.logo,
            'token_module': product.currency
        }

        return True, data

    def AddDepositOrder(self, orderInfo):
        s = self.session()

        try:
            lastTotalValue = s.query(ViolasBankDepositOrder.total_value).filter(ViolasBankDepositOrder.address == orderInfo['address']).filter(ViolasBankDepositOrder.product_id == orderInfo["product_id"]).order_by(ViolasBankDepositOrder.id.desc()).first()

            if lastTotalValue is None:
                lastTotalValue = 0
            else:
                lastTotalValue = lastTotalValue[0]

            if orderInfo["status"] == 0:
                if orderInfo['order_type'] == 0:
                    newTotalValue = lastTotalValue + orderInfo["value"]
                elif orderInfo['order_type'] == 1:
                    newTotalValue = lastTotalValue + orderInfo["value"] * -1
            else:
                newTotalValue = lastTotalValue

            order = ViolasBankDepositOrder(
                order_id = orderInfo["order_id"],
                product_id = orderInfo["product_id"],
                address = orderInfo["address"],
                value = orderInfo["value"],
                total_value = newTotalValue,
                date = int(time()),
                order_type = orderInfo["order_type"],
                status = orderInfo["status"]
            )

            s.add(order)
            s.commit()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False

        return True

    def AddBorrowOrder(self, orderInfo):
        s = self.session()

        try:
            lastTotalValue = s.query(ViolasBankBorrowOrder.total_value).filter(ViolasBankBorrowOrder.address == orderInfo["address"]).filter(ViolasBankBorrowOrder.product_id == orderInfo["product_id"]).order_by(ViolasBankBorrowOrder.id.desc()).first()

            if lastTotalValue is None:
                lastTotalValue = 0
            else:
                lastTotalValue = lastTotalValue[0]

            if orderInfo["status"] == 0:
                if orderInfo["order_type"] == 0:
                    newTotalValue = lastTotalValue + orderInfo["value"]
                elif orderInfo["order_type"] == 1:
                    newTotalValue = lastTotalValue + orderInfo["value"] * -1
            else:
                newTotalValue = lastTotalValue

            order = ViolasBankBorrowOrder(
                order_id = orderInfo["order_id"],
                product_id = orderInfo["product_id"],
                address = orderInfo["address"],
                value = orderInfo["value"],
                total_value = newTotalValue,
                date = int(time()),
                order_type = orderInfo["order_type"],
                status = orderInfo["status"]
            )

            s.add(order)
            s.commit()
            s.close()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False

        return True

    def AddNewRegisteredRecord(self, orderInfo):
        s = self.session()

        try:
            incID = None
            if orderInfo.get("inviterAddress") is not None:
                result = s.query(ViolasIncentiveIssueRecord.id).filter(ViolasIncentiveIssueRecord.address == orderInfo.get("inviterAddress")).order_by(ViolasIncentiveIssueRecord.id.desc()).first()
                incID = result[0] if result is not None else None

            record = ViolasNewRegisteredRecord(
                wallet_address = orderInfo.get("walletAddress"),
                phone_number = orderInfo.get("phoneNumber"),
                inviter_address = orderInfo.get("inviterAddress"),
                date = int(time()),
                incentive_record_id = incID
            )

            s.add(record)
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False
        finally:
            s.close()

        return True

    def AddNewIncentiveRecord(self, address, amount, status, type):
        s = self.session()
        record = ViolasIncentiveIssueRecord(
            address = address,
            amount = amount,
            date = int(time()),
            status = status,
            type = type
        )

        try:
            s.add(record)
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False
        finally:
            s.close()

        return True

    def CheckRegistered(self, walletAddress):
        s = self.session()

        try:
            if s.query(exists().where(ViolasNewRegisteredRecord.wallet_address == walletAddress)).scalar():
                isNew = 1
            else:
                isNew = 0

        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        return True, isNew

    def GetInviteOrders(self, walletAddress, limit, offset):
        s = self.session()

        try:
            result = s.query(ViolasNewRegisteredRecord.wallet_address, ViolasNewRegisteredRecord.date, ViolasIncentiveIssueRecord.amount, ViolasIncentiveIssueRecord.status).join(ViolasIncentiveIssueRecord, ViolasNewRegisteredRecord.incentive_record_id == ViolasIncentiveIssueRecord.id).filter(ViolasNewRegisteredRecord.inviter_address == walletAddress).order_by(ViolasNewRegisteredRecord.id.desc()).offset(offset).limit(limit).all()
            count = s.query(ViolasNewRegisteredRecord.wallet_address, ViolasNewRegisteredRecord.date, ViolasIncentiveIssueRecord.amount, ViolasIncentiveIssueRecord.status).join(ViolasIncentiveIssueRecord, ViolasNewRegisteredRecord.incentive_record_id == ViolasIncentiveIssueRecord.id).filter(ViolasNewRegisteredRecord.inviter_address == walletAddress).count()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        orders = []
        for i in result:
            order = {
                "be_invited": i.wallet_address,
                "amount": int(i.amount),
                "date": i.date,
                "status": i.status,
                "total_count": count
            }

            orders.append(order)

        return True, orders

    def GetTop20Invite(self):
        s = self.session()

        try:
            result = s.query(ViolasIncentiveIssueRecord.address, func.count("*"), func.sum(ViolasIncentiveIssueRecord.amount)).filter(ViolasIncentiveIssueRecord.type == 1).group_by(ViolasIncentiveIssueRecord.address).order_by(func.count("*").desc()).limit(20).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        infos = []
        for idx, i in enumerate(result):
            info = {
                "rank": idx + 1,
                "address": i[0],
                "invite_count": i[1],
                "incentive": int(i[2])
            }

            infos.append(info)

        return True, infos

    def GetInviteCount(self, walletAddress):
        s = self.session()
        try:
            result = s.query(func.count("*")).filter(ViolasIncentiveIssueRecord.address == walletAddress).filter(ViolasIncentiveIssueRecord.type == 1).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        return True, result[0]

    def GetTotalIncentive(self, address):
        s = self.session()
        try:
            result = s.query(func.sum(ViolasIncentiveIssueRecord.amount)).filter(ViolasIncentiveIssueRecord.address == address).filter(ViolasIncentiveIssueRecord.status == 1).scalar()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        if result is None:
            result = 0
        return True, int(result)

    def GetIncentiveTop20(self):
        s = self.session()

        try:
            result = s.query(ViolasIncentiveIssueRecord.address, func.sum(ViolasIncentiveIssueRecord.amount)).group_by(ViolasIncentiveIssueRecord.address).order_by(func.count("*").desc()).limit(20).all()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        infos = []
        for idx, i in enumerate(result):
            info = {
                "rank": idx + 1,
                "address": i[0],
                "incentive": int(i[1])
            }

            infos.append(info)

        return True, infos

    def GetBankIncentiveOrders(self, address, offset, limit):
        s = self.session()

        try:
            result = s.query(ViolasIncentiveIssueRecord).filter(ViolasIncentiveIssueRecord.address == address).filter(or_(ViolasIncentiveIssueRecord.type == 3, ViolasIncentiveIssueRecord.type == 4, ViolasIncentiveIssueRecord.type == 5, ViolasIncentiveIssueRecord.type == 6, ViolasIncentiveIssueRecord.type == 7)).order_by(ViolasIncentiveIssueRecord.id.desc()).offset(offset).limit(limit).all()
            count = s.query(ViolasIncentiveIssueRecord).filter(ViolasIncentiveIssueRecord.address == address).filter(or_(ViolasIncentiveIssueRecord.type == 3, ViolasIncentiveIssueRecord.type == 4, ViolasIncentiveIssueRecord.type == 5, ViolasIncentiveIssueRecord.type == 6, ViolasIncentiveIssueRecord.type == 7)).count()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        orders = []
        for i in result:
            order = {
                "type": i.type,
                "amount": int(i.amount),
                "date": i.date,
                "status": i.status,
                "total_count": count
            }

            orders.append(order)

        return True, orders

    def GetPoolIncentiveOrders(self, address, offset, limit):
        s = self.session()

        try:
            result = s.query(ViolasIncentiveIssueRecord).filter(ViolasIncentiveIssueRecord.address == address).filter(ViolasIncentiveIssueRecord.type == 8).order_by(ViolasIncentiveIssueRecord.id.desc()).offset(offset).limit(limit).all()
            count = s.query(ViolasIncentiveIssueRecord).filter(ViolasIncentiveIssueRecord.address == address).filter(ViolasIncentiveIssueRecord.type == 8).count()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        orders = []
        for i in result:
            order = {
                "type": i.type,
                "amount": int(i.amount),
                "date": i.date,
                "status": i.status,
                "total_count": count
            }

            orders.append(order)

        return True, orders

    def GetBankTotalIncenntive(self, address):
        s = self.session()
        try:
            result = s.query(func.sum(ViolasIncentiveIssueRecord.amount)).filter(ViolasIncentiveIssueRecord.address == address).filter(or_(ViolasIncentiveIssueRecord.type == 3, ViolasIncentiveIssueRecord.type == 4, ViolasIncentiveIssueRecord.type == 5, ViolasIncentiveIssueRecord.type == 6, ViolasIncentiveIssueRecord.type == 7)).filter(ViolasIncentiveIssueRecord.status == 1).scalar()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        if result is None:
            result = 0
        return True, int(result)

    def GetPoolTotalIncenntive(self, address):
        s = self.session()
        try:
            result = s.query(func.sum(ViolasIncentiveIssueRecord.amount)).filter(ViolasIncentiveIssueRecord.address == address).filter(ViolasIncentiveIssueRecord.type == 8).filter(ViolasIncentiveIssueRecord.status == 1).scalar()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        if result is None:
            result = 0
        return True, int(result)

    def GetPhoneRegisterCount(self, mobileNumber):
        s = self.session()
        try:
            count = s.query(ViolasNewRegisteredRecord).filter(ViolasNewRegisteredRecord.phone_number == mobileNumber).count()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        return True, count
