from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, String, Numeric, BigInteger, Boolean

Base = declarative_base()

class ViolasSSOUserInfo(Base):
    __tablename__ = "sso_user_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    name = Column(String(32), nullable = True)
    country = Column(String(32), nullable = True)
    id_number = Column(String(32), nullable = True)
    phone_local_number = Column(String(8), nullable = True)
    phone_number = Column(String(32), nullable = True)
    email_address = Column(String(64), nullable = True)
    id_photo_positive_url = Column(String(64), nullable = True)
    id_photo_back_url = Column(String(64), nullable = True)

class ViolasSSOInfo(Base):
    __tablename__ = "sso_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    token_type = Column(String(16), nullable = False)
    amount = Column(Numeric, nullable = False)
    token_value = Column(Numeric, nullable = False)
    token_name = Column(String(32), nullable = False)
    application_date = Column(Integer, nullable = False)
    validity_period = Column(SmallInteger, nullable = False)
    expiration_date = Column(Integer, nullable = False)
    reserve_photo_url = Column(String(64), nullable = False)
    account_info_photo_positive_url = Column(String(64), nullable = False)
    account_info_photo_back_url = Column(String(64), nullable = False)
    module_address = Column(String(64), nullable = True)
    approval_status = Column(SmallInteger, nullable = False) # 0: not approved; 1: pass; 2: not pass; 3: published; 4: minted

class ViolasGovernorInfo(Base):
    __tablename__ = "governor_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    toxid = Column(String(76), nullable = False)
    name = Column(String(32), nullable = False)
    public_key = Column(String(64), nullable = False)
    vstake_address = Column(String(64), nullable = False)
    multisig_address = Column(String(35), nullable = False)
    is_chairman = Column(Boolean, nullable = False)
    btc_txid = Column(String(64), nullable = True)
    is_handle = Column(Boolean, nullable = False)
