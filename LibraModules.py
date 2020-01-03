from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, String, Numeric

Base = declarative_base()

class LibraTransaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    sender = Column(String(64), nullable = False)
    sequence_number = Column(Integer, nullable = True)
    max_gas_amount = Column(Numeric, nullable = False)
    gas_unit_price = Column(Numeric, nullable = False)
    expiration_time = Column(Integer, nullable = False)
    transaction_type = Column(String(64), nullable = False)
    receiver = Column(String(64), nullable = True)
    amount = Column(Numeric, nullable = False)
    public_key = Column(String(64), nullable = True)
    signature = Column(String(128), nullable = True)
    transaction_hash = Column(String(64), nullable = False)
    state_root_hash = Column(String(64), nullable = False)
    event_root_hash = Column(String(64), nullable = False)
    gas_used = Column(Numeric, nullable = False)
    status = Column(SmallInteger, nullable = False)

class LibraAddressInfo(Base):
    __tablename__ = "address_info"

    id = Column(Integer, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = False)
    address_type = Column(SmallInteger, nullable = False) # 0: Minter, 1: Normal
    balance = Column(Numeric, nullable = False)
    sequence_number = Column(Integer, nullable = False)
