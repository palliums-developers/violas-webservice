from LibraModules import LibraAddressInfo, LibraTransaction

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

class LibraPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def GetRecentTransaction(self, limit, offset):
        s = self.session()
        query = s.query(LibraTransaction).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

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

        s.close()
        return infoList

    def GetAddressInfo(self, address):
        s = self.session()
        result = s.query(LibraAddressInfo).filter(LibraAddressInfo.address == address).first()

        info = {}
        if result is not None:
            info["type"] = result.type
            info["first_seen"] = result.first_seen
            info["sent_amount"] = result.sent_amount
            info["received_amount"] = result.received_amount
            info["sent_tx_count"] = result.sent_tx_count
            info["received_tx_count"] = result.received_tx_count
            info["sent_minted_tx_count"] = result.sent_minted_tx_count
            info["received_minted_tx_count"] = result.received_minted_tx_count
            info["sent_failed_tx_count"] = result.sent_failed_tx_count
            info["received_failed_tx_count"] = result.received_failed_tx_count

        s.close()
        return info

    def GetTransactionsByAddress(self, address, limit, offset):
        s = self.session()
        query = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

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

        s.close()
        return infoList

    def GetTransactionByVersion(self, version):
        s = self.session()
        result = s.query(LibraTransaction).filter(LibraTransaction.id == (version + 1)).first()

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

        s.close()
        return info

    def GetTransactionCount(self):
        s = self.session()
        result = s.query(LibraTransaction).count()
        s.close()

        return result

    def GetTransactionsForWallet(self, address, offset, limit):
        s = self.session()
        query = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

        infoList = []
        for i in query:
            info = {}
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["gas"] = int(i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)

            infoList.append(info)

        s.close()
        return infoList
