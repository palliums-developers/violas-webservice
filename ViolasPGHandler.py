from time import time
from ViolasModules import ViolasSSOInfo, ViolasSSOUserInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class ViolasPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def AddSSOUserInfo(self, data):
        s = self.session()

        info = ViolasSSOUserInfo(
            wallet_address = data["wallet_address"],
            name = data["name"],
            country = data["country"],
            id_number = data["id_number"],
            phone_number = data["phone_number"],
            email_address = data["email_address"],
            id_photo_positive_url = data["id_photo_positive_url"],
            id_photo_back_url = data["id_photo_back_url"]
        )

        s.add(info)
        s.commit()
        s.close()

        return

    def AddSSOInfo(self, data):
        s = self.session()
        timestamp = int(time())

        info = ViolasSSOInfo(
            wallet_address = data["wallet_address"],
            token_type = data["token_type"],
            amount = data["amount"],
            token_value = data["token_value"],
            token_name = data["token_name"],
            application_date = timestamp,
            validity_period = 5,
            expiration_date = timestamp + 60 * 60 * 24 * 5,
            reserive_photo_url = data["reserive_photo_url"],
            account_info_photo_positive_url = data["account_info_photo_positive_url"],
            account_info_photo_back_url = data["account_info_photo_back_url"],
            approval_status = 0,
            publish_status = 0
        )

        s.add(info)
        s.commit()
        s.close()

        return

    def GetSSOApprovalStatus(self, address):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).first()

        info = {}
        info["amount"] = result.amount
        info["token_name"] = result.token_name
        info["approval_status"] = result.approval_status

        s.close()

        return info

    def ModifySSOApprovalStatus(self, address, status):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).first()

        result.approval_status = status
        s.commit()
        s.close()

        return

    def ModifySSOPublishStatus(self, address, status):
        s = self.session()
        result = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.wallet_address == address).first()

        result.publish_status = 1
        s.commit()
        s.close()

        return

    def GetPublishedSSO(self):
        s = self.session()
        ssoInfos = s.query(ViolasSSOInfo).filter(ViolasSSOInfo.publish_status == 1).all()

        infos = []
        for i in result:
            info = {}
            info["wallet_address"] = i.wallet_address
            info["amount"] = i.amount

            infos.append(info)

        s.close()
        return infos
