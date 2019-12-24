from time import time
from ViolasModules import ViolasSSOInfo, ViolasSSOUserInfo, ViolasGovernorInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy.sql.expression import false

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

        return

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
        ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.approval_status == 0).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id).offset(offset).limit(limit).all()

        infos = []
        for i in result:
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
            info["amount"] = i.amount
            info["token_value"] = i.token_value
            info["token_name"] = i.token_name
            info["application_date"] = i.application_date
            info["validity_period"] = i.validity_period
            info["expiration_date"] = i.expiration_date
            info["reserve_photo_url"] = i.reserve_photo_url
            info["account_info_photo_positive_url"] = i.account_info_photo_positive_url
            info["account_info_photo_back_url"] = i.account_info_photo_back_url

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
            result.moudle.address = data["module_address"]

        s.commit()
        s.close()

        return True

    def GetPublishedSSOInfo(self, address, offset, limit):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.approval_status == 3).filter(ViolasSSOInfo.governor_address == address).order_by(ViolasSSOInfo.id).offset(offset).limit(limit).all()

        infos = []
        for i in result:
            info = {}
            info["wallet_address"] = i.wallet_address
            info["module_address"] = i.module_address
            info["amount"] = i.amount

            infos.append(info)

        s.close()
        return infos

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

            infos.append(info)

        s.close()
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
                is_handle = False
            )

            s.add(info)
            s.commit()

        s.close()

        return

    def ModifyGovernorInfo(self, data):
        s = self.session()

        result =  s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.toxid == data["toxid"]).first()
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
        if "is_handle" in data:
            if data["is_handle"] == 0:
                result.is_handle = False
            else:
                result.is_handle = True

        s.commit()
        s.close()
        return True

    def GetInvestmentedGovernorInfo(self, offset, limit):
        s = self.session()
        result = s.query(ViolasGovernorInfo).filter(ViolasGovernorInfo.is_handle == False).filter(ViolasGovernorInfo.btc_txid.isnot(None)).order_by(ViolasGovernorInfo.id).offset(offset).limit(limit).all()

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
