from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, String, Numeric, Text, Index

Base = declarative_base()

class LibraTransaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    sequence_number = Column(Integer, nullable = True)
    sender = Column(String(64), nullable = True)
    receiver = Column(String(64), nullable = True)
    currency = Column(String(16), nullable = True)
    gas_currency = Column(String(16), nullable = True)
    amount = Column(Numeric, nullable = True)
    gas_used = Column(Numeric, nullable = True)
    gas_unit_price = Column(Numeric, nullable = True)
    max_gas_amount = Column(Numeric, nullable = True)
    expiration_time = Column(Integer, nullable = True)
    transaction_type = Column(String(64), nullable = True)
    data = Column(Text(), nullable = True)
    public_key = Column(Text(), nullable = True)
    script_hash = Column(String(64), nullable = True)
    signature = Column(Text(), nullable = True)
    signature_scheme = Column(String(32), nullable = True)
    status = Column(String(32), nullable = True)
    confirmed_time = Column(BigInteger, nullable = True)

Index("address_index", LibraTransaction.sender, LibraTransaction.receiver)
Index("sender_index", LibraTransaction.sender)
Index("receiver_index", LibraTransaction.receiver)
Index("currency_index", LibraTransaction.currency)

class LibraAddressInfo(Base):
    __tablename__ = "address_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = True)
    type = Column(SmallInteger, nullable = True) # 0: Minter, 1: metadata 2: Normal
    first_seen = Column(BigInteger, nullable = True)
    received_amount = Column(Numeric, nullable = True)
    sent_amount = Column(Numeric, nullable = True)
    sent_tx_count = Column(BigInteger, nullable = True)
    received_tx_count = Column(BigInteger, nullable = True)
    sent_minted_tx_count = Column(BigInteger, nullable = True)
    received_minted_tx_count = Column(BigInteger, nullable = True)
    sent_failed_tx_count = Column(BigInteger, nullable = True)
    received_failed_tx_count = Column(BigInteger, nullable = True)

Index("address_info_index", LibraAddressInfo.address)
