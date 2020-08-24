from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, String, Numeric, Boolean, Text, Index

Base = declarative_base()

class ViolasTransaction(Base):
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
    status = Column(SmallInteger, nullable = True)
    event = Column(Text(), nullable = True)
    confirmed_time = Column(Integer, nullable = True)


class ViolasAddressInfo(Base):
    __tablename__ = "address_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = True)
    type = Column(SmallInteger, nullable = True) # 0: Minter, 1: Faucet, 2: Normal
    first_seen = Column(BigInteger, nullable = True)
    sent_amount = Column(Numeric, nullable = True)
    received_amount = Column(Numeric, nullable = True)
    sent_tx_count = Column(BigInteger, nullable = True)
    received_tx_count = Column(BigInteger, nullable = True)
    sent_minted_tx_count = Column(BigInteger, nullable = True)
    received_minted_tx_count = Column(BigInteger, nullable = True)
    sent_failed_tx_count = Column(BigInteger, nullable = True)
    received_failed_tx_count = Column(BigInteger, nullable = True)

class ViolasSignedTransaction(Base):
    __tablename__ = "signed_transactions"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    sender = Column(String(64), nullable = False)
    sequence_number = Column(Integer, nullable = False)
    time = Column(Integer, nullable = False)
    sigtxn = Column(Text(), nullable = True)

Index("sender_seqnum_index", ViolasSignedTransaction.sender, ViolasSignedTransaction.sequence_number)

class ViolasSSOUserInfo(Base):
    __tablename__ = "sso_user_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    public_key = Column(String(64), nullable = True)
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
    token_id = Column(Integer, nullable = True)
    application_date = Column(Integer, nullable = False)
    validity_period = Column(SmallInteger, nullable = False)
    expiration_date = Column(Integer, nullable = False)
    reserve_photo_url = Column(String(64), nullable = False)
    account_info_photo_positive_url = Column(String(64), nullable = False)
    account_info_photo_back_url = Column(String(64), nullable = False)
    governor_address = Column(String(64), nullable = False)
    approval_status = Column(SmallInteger, nullable = True) # -3: chairman failed; -2: governor failed; -1: timeout; 0: in review; 1: governor pass; 2: chairman pass; 3: Transferred 4: published; 5: minted; 
    failed_reason = Column(SmallInteger, nullable = True)
    remarks = Column(String(128), nullable = True)

class ViolasGovernorInfo(Base):
    __tablename__ = "governor_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    wallet_address = Column(String(64), nullable = False)
    wallet_public_key = Column(String(64), nullable = False)
    toxid = Column(String(76), nullable = True)
    name = Column(String(32), nullable = False)
    btc_public_key = Column(String(128), nullable = True)
    vstake_address = Column(String(64), nullable = True)
    multisig_address = Column(String(35), nullable = True)
    is_chairman = Column(Boolean, nullable = False)
    btc_txid = Column(String(64), nullable = True)
    is_handle = Column(SmallInteger, nullable = False) # 0: in review; 1: pass; 2: failed; 3: published; 4: minted
    application_date = Column(Integer, nullable = True)
    bind_governor = Column(String(64), nullable = True)
