from time import sleep
from LibraModules import LibraAddressInfo, LibraTransaction

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

class LibraPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def Commit(self, session):
        for i in range(5):
            try:
                session.commit()
                session.close()
                return True
            except OperationalError:
                session.close()
                logging.debug(f"ERROR: Database commit failed! Retry after {i} second.")
                sleep(i)
                session = self.session()
                continue

        session.close()
        return False

    def Query(self, session, table):
        for i in range(5):
            try:
                return session, session.query(table)
            except OperationalError:
                session.close()
                logging.debug(f"ERROR: Database query failed! Retry after {i} second.")
                sleep(i)
                session = self.session()
                continue

        return session, False

    def GetRecentTransaction(self, limit, offset):
        s = self.session()

        s, query = self.Query(s, LibraTransaction)
        if query:
            result = query.order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        else:
            s.close()
            return False, None

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

            infoList.append(info)

        return True, infoList

    def GetAddressInfo(self, address):
        s = self.session()

        s, query = self.Query(s, LibraAddressInfo)
        if query:
            result = query.filter(LibraAddressInfo.address == address).first()
            s.close()
        else:
            s.close()
            return False, None

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

        return True, info

    def GetTransactionsByAddress(self, address, limit, offset):
        s = self.session()

        s, query = self.Query(s, LibraTransaction)
        if query:
            result  = query.filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        else:
            s.close()
            return False, None

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

            infoList.append(info)

        return True, infoList

    def GetTransactionByVersion(self, version):
        s = self.session()

        s, query = self.Query(s, LibraTransaction)
        if query:
            result = query.filter(LibraTransaction.id == (version + 1)).first()
            s.close()
        else:
            s.close()
            return False, None

        info = {}
        info["version"] = result.id - 1
        info["type"] = result.transaction_type
        info["sequence_number"] = result.sequence_number
        info["sender"] = result.sender
        info["receiver"] = result.receiver
        info["amount"] = int(result.amount)
        info["gas_unit_price"] = int(result.gas_unit_price)
        info["max_gas_amount"] = int(result.max_gas_amount)
        info["expiration_time"] = result.expiration_time
        info["public_key"] = result.public_key
        info["signature"] = result.signature
        info["status"] = result.status

        return True, info

    def GetTransactionCount(self):
        s = self.session()

        s, query = self.Query(s, LibraTransaction)
        if query:
            result = query.count()
            s.close()
        else:
            s.close()
            return False, None

        return True, result

    def GetTransactionsForWallet(self, address, offset, limit):
        s = self.session()

        s, query = self.Query(s, LibraTransaction)
        if query:
            result = query.filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        else:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)

            infoList.append(info)

        return True, infoList
