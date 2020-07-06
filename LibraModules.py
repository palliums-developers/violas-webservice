from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, String, Numeric, Text

Base = declarative_base()

class LibraTransaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    sequence_number = Column(Integer, nullable = False)
    sender = Column(String(64), nullable = False)
    receiver = Column(String(64), nullable = True)
    currency = Column(String(16), nullable = True)
    gas_currency = Column(String(16), nullable = True)
    amount = Column(Numeric, nullable = False)
    gas_used = Column(Numeric, nullable = False)
    gas_unit_price = Column(Numeric, nullable = False)
    max_gas_amount = Column(Numeric, nullable = False)
    expiration_time = Column(Integer, nullable = False)
    transaction_type = Column(String(64), nullable = False)
    data = Column(Text(), nullable = True)
    public_key = Column(Text(), nullable = True)
    script_hash = Column(String(64), nullable = True)
    signature = Column(Text(), nullable = True)
    signature_scheme = Column(String(32), nullable = True)
    status = Column(SmallInteger, nullable = False)

class LibraAddressInfo(Base):
    __tablename__ = "address_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = False)
    type = Column(SmallInteger, nullable = False) # 0: Minter, 1: metadata 2: Normal
    first_seen = Column(BigInteger, nullable = False)
    received_amount = Column(Numeric, nullable = False)
    sent_amount = Column(Numeric, nullable = False)
    sent_tx_count = Column(BigInteger, nullable = False)
    received_tx_count = Column(BigInteger, nullable = False)
    sent_minted_tx_count = Column(BigInteger, nullable = False)
    received_minted_tx_count = Column(BigInteger, nullable = False)
    sent_failed_tx_count = Column(BigInteger, nullable = False)
    received_failed_tx_count = Column(BigInteger, nullable = False)
