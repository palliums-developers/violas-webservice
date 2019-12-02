from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, String, Numeric, BigInteger

Base = declarative_base()

class ViolasSSOUserInfo(Base):
    __tablename__ = "sso_user_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    name = Column(String(32), nullable = True)
    country = Column(String(32), nullable = True)
    id_number = Column(String(32), nullable = True)
    phone_number = Column(String(32), nullable = True)
    email_address = Column(String(64), nullable = True)
    id_photo_positive_url = Column(String(64), nullable = True)
    id_photo_back_url = Column(String(64), nullable = True)

class ViolasSSOInfo(Base):
    __tablename__ = "sso_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    token_type = Column(SmallInteger, nullable = False)
    amount = Column(Numeric, nullable = False)
    token_value = Column(Numeric, nullable = False)
    token_name = Column(String(32), nullable = False)
    application_date = Column(Integer, nullable = False)
    validity_period = Column(SmallInteger, nullable = False)
    expiration_date = Column(Integer, nullable = False)
    reserve_photo_url = Column(String(64), nullable = False)
    account_info_photo_positive_url = Column(String(64), nullable = False)
    account_info_photo_back_url = Column(String(64), nullable = False)
    approval_status = Column(SmallInteger, nullable = False) # 0: not approved; 1: pass; 2: not pass
    publish_status = Column(SmallInteger, nullable = False)  # 0: not publish; 1: published; 2: minted
