from time import sleep
from LibraModules import LibraAddressInfo, LibraTransaction

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from TransferType import TransferType

class LibraPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def GetRecentTransaction(self, limit, offset):
        s = self.session()

        try:
            result = s.query(LibraTransaction).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["currency"] = i.currency
            info["status"] = i.status


            infoList.append(info)

        return True, infoList

    def GetRecentTransactionAboutCurrency(self, limit, offset, currency):
        s = self.session()

        try:
            result = s.query(LibraTransaction).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency

            infoList.append(info)

        return True, infoList

    def GetAddressInfo(self, address):
        s = self.session()

        try:
            result = s.query(LibraAddressInfo).filter(LibraAddressInfo.address == address).first()
            s.close()
        except OperationalError:
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

        try:
            result  = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["currency"] = i.currency
            info["status"] = i.status

            infoList.append(info)

        return True, infoList

    def GetTransactionsByAddressAboutCurrency(self, address, limit, offset, currency):
        s = self.session()

        try:
            result = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.id - 1
            info["type"] = i.transaction_type
            info["sender"] = i.sender
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["status"] = i.status
            info["currency"] = i.currency

            infoList.append(info)

        return True, infoList

    def GetTransactionByVersion(self, version):
        s = self.session()

        try:
            result = s.query(LibraTransaction).filter(LibraTransaction.id == (version + 1)).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        info = {}
        info["version"] = result.id - 1
        info["type"] = result.transaction_type
        info["sequence_number"] = result.sequence_number
        info["sender"] = result.sender
        info["receiver"] = result.receiver
        info["currency"] = result.currency
        info["gas_currency"] = result.gas_currency
        info["amount"] = int(result.amount)
        info["gas"] = int(result.gas_used * i.gas_unit_price)
        info["gas_unit_price"] = int(result.gas_unit_price)
        info["max_gas_amount"] = int(result.max_gas_amount)
        info["expiration_time"] = result.expiration_time
        info["public_key"] = result.public_key
        info["signature"] = result.signature
        info["status"] = result.status
        info["data"] = result.data

        return True, info

    def GetTransactionCount(self):
        s = self.session()

        try:
            result = s.query(LibraTransaction.id).order_by(LibraTransaction.id.desc()).limit(1).first()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        if result is None:
            result = 0
        else:
            result = result[0]

        return True, result

    def GetTransactionsForWallet(self, address, currency, flows, offset, limit):
        s = self.session()

        try:
            if currency is None:
                if flows is None:
                    result = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 0:
                    result = s.query(LibraTransaction).filter(LibraTransaction.sender == address).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 1:
                    result = s.query(LibraTransaction).filter(LibraTransaction.receiver == address).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            else:
                if flows is None:
                    result = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address)).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 0:
                    result = s.query(LibraTransaction).filter(LibraTransaction.sender == address).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
                elif flows == 1:
                    result = s.query(LibraTransaction).filter(LibraTransaction.receiver == address).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()

            s.close()
        except OperationalError:
            s.close()
            return False, None

        infoList = []
        for i in result:
            info = {}
            info["type"] = TransferType.get(i.transaction_type)
            info["version"] = i.id - 1
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number
            info["gas"] = int(i.gas_used * i.gas_unit_price)
            info["expiration_time"] = i.expiration_time
            info["receiver"] = i.receiver
            info["amount"] = int(i.amount)
            info["currency"] = i.currency
            info["gas_currency"] = i.gas_currency
            info["status"] = i.status

            infoList.append(info)

        return True, infoList

    def GetMapTransactionInfo(self, sender, receiver, offset, limit):
        s = self.session()

        try:
            result = s.query(LibraTransaction).filter(LibraTransaction.sender == sender).filter(LibraTransaction.receiver == receiver).order_by(LibraTransaction.id.desc()).offset(offset).limit(limit).all()
            s.close()
        except OperationalError:
            s.close()
            return False, None

        infos = []
        for i in result:
            info = {}
            info["date"] = i.expiration_time
            info["amount"] = int(i.amount)
            info["address"] = receiver
            info["coin"] = "vlibra"
            info["status"] = 0

            infos.append(info)

        return True, infos
