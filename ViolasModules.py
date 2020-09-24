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
    sigtxn = Column(Text, nullable = True)

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

class ViolasBankDepositProduct(Base):
    __tablename__ = "deposit_product"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    product_id = Column(String(32), primary_key = True, nullable = False)
    product_name = Column(String(32), nullable = False)
    logo = Column(String(32), nullable = False)
    minimum_amount = Column(Integer, nullable = False)
    minimum_step = Column(Integer, nullable = False)
    max_limit = Column(Integer, nullable = False)
    pledge_rate = Column(Numeric, nullable = False)
    description = Column(Text, nullable = False)
    intor = Column(Text, nullable = False)
    question = Column(Text, nullable = False)
    currency = Column(String(16), nullable = False)
    rate = Column(Numeric, nullable = True)
    rate_desc = Column(Text, nullable = True)

class ViolasBankDepositOrder(Base):
    __tablename__ = "deposit_order"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    order_id = Column(String(32), primary_key = True, nullable = False)
    product_id = Column(String(32), nullable = False)
    address = Column(String(64), nullable = False)
    value = Column(BigInteger, nullable = False)
    total_value = Column(BigInteger, nullable = False)
    date = Column(Integer, nullable = False)
    order_type  = Column(SmallInteger, nullable = False) # 0: deposit, 1: withdrawal
    status = Column(SmallInteger, nullable = False) # 0: succ, -1: failed

class ViolasBankInterestInfo(Base):
    __tablename__ = "interest_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = False)
    interest = Column(BigInteger, nullable = False)
    total_interest = Column(BigInteger, nullable = False)
    date = Column(Integer, nullable = False)
    product_id = Column(String(32), nullable = False)

class ViolasBankBorrowProduct(Base):
    __tablename__ = "borrow_product"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    product_id = Column(String(32), primary_key = True, nullable = False)
    product_name = Column(String(32), nullable = False)
    logo = Column(String(32), nullable = False)
    minimum_amount = Column(Integer, nullable = False)
    minimum_step = Column(Integer, nullable = False)
    max_limit = Column(Integer, nullable = False)
    pledge_rate = Column(Numeric, nullable = False)
    description = Column(Text, nullable = False)
    intor = Column(Text, nullable = False)
    question = Column(Text, nullable = False)
    currency = Column(String(16), nullable = False)
    rate = Column(Numeric, nullable = True)
    rate_desc = Column(Text, nullable = True)

class ViolasBankBorrowOrder(Base):
    __tablename__ = "borrow_order"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    order_id = Column(String(32), primary_key = True, nullable = False)
    product_id = Column(String(32), nullable = False)
    address = Column(String(64), nullable = False)
    value = Column(BigInteger, nullable = False)
    total_value = Column(BigInteger, nullable = False)
    date = Column(Integer, nullable = False)
    order_type  = Column(SmallInteger, nullable = False) # 0: borrwo, 1: repayment, 2: clear
    status = Column(SmallInteger, nullable = False) # 0: succ, -1: failed
    deductioned = Column(BigInteger, nullable = True)
    deductioned_currency = Column(String(16), nullable = True)

class ViolasBankLiabilityInfo(Base):
    __tablename__ = "liability_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = False)
    liability = Column(BigInteger, nullable = False)
    total_liability = Column(BigInteger, nullable = False)
    date = Column(Integer, nullable = False)
    product_id = Column(String(32), nullable = False)
