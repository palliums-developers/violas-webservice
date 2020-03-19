from time import time, sleep
from ViolasModules import ViolasSSOInfo, ViolasSSOUserInfo, ViolasGovernorInfo, ViolasTransaction, ViolasAddressInfo
import logging

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy.sql.expression import false
from sqlalchemy.exc import OperationalError

from TransferType import TransferType

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
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.token_name == (data["token_name"] + data["token_type"])).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if result is not None:
            s.close()
            return True, False

        info = ViolasSSOInfo(
            wallet_address = data["wallet_address"],
            token_type = data["token_type"],
            amount = data["amount"],
            token_value = data["token_value"],
            token_name = data["token_name"] + data["token_type"],
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

        try:
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        s.close()
        return True, True

    def GetSSOApprovalStatus(self, address):
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
        info["amount"] = int(result.amount)
        info["token_name"] = result.token_name
        info["approval_status"] = result.approval_status
        info["module_address"] = result.module_address

        return True, info

    def SetTokenPublished(self, address):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).first()

            if result is None:
                s.close()
                return True, False

            result.approval_status = 3
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
            ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id).offset(offset).limit(limit).all()
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

            infos.append(info)

        s.close()
        return True, infos

    def SetMintInfo(self, data):
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

        result.approval_status = data["approval_status"]
        if "module_address" in data:
            logging.debug(f"module_address: {data['module_address']}")
            result.module_address = data["module_address"]

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

    def GetGovernorInfo(self, offset, limit):
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
            info["public_key"] = i.public_key
            info["wallet_address"] = i.wallet_address
            info["vstake_address"] = i.vstake_address
            info["multisig_address"] = i.multisig_address
            info["is_chairman"] = i.is_chairman
            info["subaccount_count"] = i.subaccount_count
            info["violas_public_key"] = i.violas_public_key

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
        info["public_key"] = govInfos.public_key
        info["wallet_address"] = govInfos.wallet_address
        info["vstake_address"] = govInfos.vstake_address
        info["multisig_address"] = govInfos.multisig_address
        info["is_chairman"] = govInfos.is_chairman
        info["subaccount_count"] = govInfos.subaccount_count
        info["status"] = govInfos.is_handle

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
                    public_key = data["public_key"],
                    vstake_address = data["vstake_address"],
                    multisig_address = data["multisig_address"],
                    is_chairman = isChairman,
                    is_handle = 0,
                    subaccount_count = data["subaccount_count"],
                    violas_public_key = data["violas_public_key"]
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
                    subaccount_count = 1,
                    application_date = int(time()),
                    violas_public_key = data["public_key"]
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
            result.public_key = data["public_key"]
        if "vstake_address" in data:
            result.vstake_address = data["vstake_address"]
        if "multisig_address" in data:
            result.multisig_address = data["multisig_address"]
        if "btc_txid" in data:
            result.btc_txid = data["btc_txid"]
            result.application_date = int(time())
        if "is_handle" in data:
            result.is_handle = data["is_handle"]
        if "subaccount_count" in data:
            result.subaccount_count = data["subaccount_count"]

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
            info["public_key"] = i.public_key
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
            currency["name"] = i.token_name
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
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["module_address"] = i.module

            infoList.append(info)

        return True, infoList

    def GetRecentTransactionAboutModule(self, limit, offset, module):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
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
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["module_address"] = i.module

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
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["module_address"] = i.module

            infoList.append(info)

        return True, infoList

    def GetTransactionsByAddressAboutModule(self, address, limit, offset, module):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
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
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["module_address"] = i.module

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
        info["module_address"] = result.module
        info["amount"] = int(result.amount)
        info["gas_unit_price"] = int(result.gas_unit_price)
        info["max_gas_amount"] = int(result.max_gas_amount)
        info["expiration_time"] = result.expiration_time
        info["public_key"] = result.public_key
        info["signature"] = result.signature
        info["status"] = result.status
        info["data"] = result.data

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

    def GetTransactionsForWallet(self, address, module, offset, limit, moduleMap):
        s = self.session()

        try:
            result = s.query(ViolasSSOInfo.module_address, ViolasSSOInfo.token_name).all()
        except OperationalError:
            s.close()
            return False, None

        for i in result:
            moduleMap[i.module_address] = i.token_name

        try:
            if module == "0000000000000000000000000000000000000000000000000000000000000000":
                result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
            else:
                result = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["type"] = TransferType[i.transaction_type]
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["sender_module"] = i.module
            info["receiver_module"] = i.module
            info["module_name"] = moduleMap.get(i.module)

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
            result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == address).filter(ViolasTransaction.receiver == exchangeAddress).filter(ViolasTransaction.module == exchangeModule).count()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        return True, result

    def GetExchangeTransactionCountTo(self, address, exchangeAddress, exchangeModule):
        s = self.session()

        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.sender == exchangeAddress).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.module == exchangeModule).count()
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
            ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id).offset(offset).limit(limit).all()
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
            info["application_date"] = i.application_date
            info["approval_status"] = i.approval_status
            info["expiration_date"] = i.expiration_date

            infos.append(info)

        s.close()
        return True, infos

    def GetUnapprovalSSOInfo(self, id):
        s = self.session()

        try:
            ssoInfo = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.id == id).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        if ssoInfo is None:
            return True, None

        try:
            userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == ssoInfo.wallet_address).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            s.close()
            return False, None

        info = {}
        info["id"] = ssoInfo.id
        info["wallet_address"] = userInfo.wallet_address
        info["name"] = userInfo.name
        info["country"] = userInfo.country
        info["id_number"] = userInfo.id_number
        info["phone_local_number"] = userInfo.phone_local_number
        info["phone_number"] = userInfo.phone_number
        info["email_address"] = userInfo.email_address
        # info["id_photo_positive_url"] = userInfo.id_photo_positive_url
        # info["id_photo_back_url"] = userInfo.id_photo_back_url
        info["token_type"] = ssoInfo.token_type
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
        info["subaccount_number"] = ssoInfo.subaccount_number
        info["module_address"] = ssoInfo.module_address

        s.close()
        return True, info

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
