from time import time
from ViolasModules import ViolasSSOInfo, ViolasSSOUserInfo, ViolasGovernorInfo, ViolasTransaction, ViolasAddressInfo
import logging

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy.sql.expression import false

from TransferType import TransferType

class ViolasPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def AddSSOUser(self, address):
        s = self.session()

        if not s.query(exists().where(ViolasSSOUserInfo.wallet_address == address)).scalar():
            info = ViolasSSOUserInfo(
                wallet_address = address
            )

            s.add(info)
            s.commit()

        s.close()

        return

    def UpdateSSOUserInfo(self, data):
        s = self.session()

        result = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == data["wallet_address"]).first()

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

        s.commit()
        s.close()

        return

    def GetSSOUserInfo(self, address):
        s = self.session()
        result = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == address).first()
        if result is None:
            return None

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

        return info

    def AddSSOInfo(self, data):
        s = self.session()
        timestamp = int(time())

        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.token_name == (data["token_name"] + data["token_type"])).first()
        if result is not None:
            return False

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
        s.commit()
        s.close()

        return True

    def GetSSOApprovalStatus(self, address):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).order_by(ViolasSSOInfo.id.desc()).first()

        if result is None:
            return None

        info = {}
        info["amount"] = int(result.amount)
        info["token_name"] = result.token_name
        info["approval_status"] = result.approval_status
        info["module_address"] = result.module_address

        s.close()

        return info

    def SetTokenPublished(self, address):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).first()

        result.approval_status = 3
        s.commit()
        s.close()

        return

    def GetUnapprovalSSO(self, address, offset, limit):
        s = self.session()
        ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id).offset(offset).limit(limit).all()

        infos = []
        for i in ssoInfos:
            userInfo = s.query(ViolasSSOUserInfo).filter(ViolasSSOUserInfo.wallet_address == i.wallet_address).first()

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
        return infos

    def SetMintInfo(self, data):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == data["wallet_address"]).first()
        if result is None:
            return False

        result.approval_status = data["approval_status"]
        if "module_address" in data:
            logging.debug(f"module_address: {data['module_address']}")
            result.module_address = data["module_address"]

        s.commit()
        s.close()

        return True

    def SetTokenMinted(self, data):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == data["wallet_address"]).first()
        if result is None:
            return False

        result.approval_status = 4

        s.commit()
        s.close()

        return True

    def GetGovernorInfo(self, offset, limit):
        s = self.session()
        govInfos = s.query(ViolasGovernorInfo).order_by(ViolasGovernorInfo.id).offset(offset).limit(limit).all()

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

            infos.append(info)

        s.close()
        return infos

    def GetGovernorInfoAboutAddress(self, address):
        s = self.session()
        govInfos = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == address).first()

        info = {}
        info["toxid"] = i.toxid
        info["name"] = i.name
        info["public_key"] = i.public_key
        info["wallet_address"] = i.wallet_address
        info["vstake_address"] = i.vstake_address
        info["multisig_address"] = i.multisig_address
        info["is_chairman"] = i.is_chairman
        info["subaccount_count"] = i.subaccount_count

        return infos

    def AddGovernorInfo(self, data):
        s = self.session()

        if data["is_chairman"] == 0:
            isChairman = False
        else:
            isChairman = True

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
                subaccount_count = data["subaccount_count"]
            )

            s.add(info)
            s.commit()

        s.close()

        return

    def ModifyGovernorInfo(self, data):
        s = self.session()

        result =  s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.wallet_address == data["wallet_address"]).first()
        if result is None:
            return False

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
        if "is_chairman" in data:
            if data["is_chairman"] == 0:
                result.is_chairman = False
            else:
                result.is_chairman = True
        if "btc_txid" in data:
            result.btc_txid = data["btc_txid"]
            result.application_date = int(time())
        if "is_handle" in data:
            result.is_handle = data["is_handle"]
        if "subaccount_count" in data:
            result.subaccount_count = data["subaccount_count"]

        s.commit()
        s.close()
        return True

    def GetInvestmentedGovernorInfo(self):
        s = self.session()
        result = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.btc_txid.isnot(None)).order_by(ViolasGovernorInfo.id).all()

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

        s.close()
        return infos

    def GetCurrencies(self):
        s = self.session()
        ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.approval_status == 4).order_by(ViolasSSOInfo.id).all()

        currencies = []
        for i in ssoInfos:
            currency = {}
            currency["name"] = i.token_name
            currency["address"] = i.module_address
            currency["description"] = i.token_name

            currencies.append(currency)

        s.close()
        return currencies

    # explorer db handle function
    def GetRecentTransaction(self, limit, offset):
        s = self.session()
        query = s.query(ViolasTransaction).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

        infoList = []
        for i in query:
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

        s.close()
        return infoList

    def GetRecentTransactionAboutModule(self, limit, offset, module):
        s = self.session()
        result = s.query(ViolasTransaction).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

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

        s.close()
        return infoList

    def GetAddressInfo(self, address):
        s = self.session()
        result = s.query(ViolasAddressInfo).filter(ViolasAddressInfo.address == address).first()
        if result is None:
            return None

        info = {}
        if result is not None:
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

        s.close()
        return info

    def GetTransactionsByAddress(self, address, limit, offset):
        s = self.session()
        query = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

        infoList = []
        for i in query:
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

        s.close()
        return infoList

    def GetTransactionsByAddressAboutModule(self, address, limit, offset, module):
        s = self.session()
        query = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

        infoList = []
        for i in query:
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

        s.close()
        return infoList

    def GetTransactionByVersion(self, version):
        s = self.session()
        result = s.query(ViolasTransaction).filter(ViolasTransaction.id == (version + 1)).first()

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

        s.close()
        return info

    def GetTransactionCount(self):
        s = self.session()
        result = s.query(ViolasTransaction).count()
        s.close()

        return result

    def VerifyTransactionAboutVBtc(self, data):
        s = self.session()
        result = s.query(ViolasTransaction).filter(ViolasTransaction.id == data["version"] + 1).first()
        s.close()

        if result is None:
            return False

        if result.sender != data["sender_address"]:
            return False

        if result.sequence_number != data["sequence_number"]:
            return False

        if int(result.amount) != data["amount"]:
            return False

        try:
            res = result.data.rsplit(":", 1)
            if res[0] != "v2b:btc_address":
                return False

            if res[1] != data["btc_address"]:
                return False

        except:
            return False

        if result.module != data["module"]:
            return False

        if result.receiver != data["receiver"]:
            return False

        return True

    def GetTransactionsAboutVBtc(self, address, module, start_version):
        s = self.session()
        result = s.query(ViolasTransaction).filter(ViolasTransaction.receiver == address).filter(ViolasTransaction.module == module).filter(ViolasTransaction.id >= (start_version + 1)).order_by(ViolasTransaction.id).limit(10).all()

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

        s.close()
        return infoList

    def GetTransactionsAboutGovernor(self, address, start_version, limit):
        s = self.session()
        query = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.id > (start_version + 1)).order_by(ViolasTransaction.id).limit(limit).all()

        infoList = []
        for i in query:
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

        s.close()
        return infoList

    def GetTransactionsForWallet(self, address, module, offset, limit):
        s = self.session()
        infoList = []

        result = s.query(ViolasSSOInfo.module_address, ViolasSSOInfo.token_name).all()
        moduleMap = {}
        moduleMap["0000000000000000000000000000000000000000000000000000000000000000"] = "vtoken"

        for i in result:
            moduleMap[i.module_address] = i.token_name

        if module == "0000000000000000000000000000000000000000000000000000000000000000":
            query = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()
        else:
            query = s.query(ViolasTransaction).filter(or_(ViolasTransaction.sender == address, ViolasTransaction.receiver == address)).filter(ViolasTransaction.module == module).order_by(ViolasTransaction.id.desc()).offset(offset).limit(limit).all()

        for i in query:
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
            info["module_name"] = moduleMap[i.module]

            infoList.append(info)

        s.close()
        return infoList

    def GetGovernorInfoForSSO(self):
        s = self.session()
        govInfos = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.is_handle == 4).order_by(ViolasGovernorInfo.id).all()

        infos = []
        for i in govInfos:
            info = {}
            info["name"] = i.name
            info["wallet_address"] = i.wallet_address

            infos.append(info)

        s.close()
        return infos
