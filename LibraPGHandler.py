from time import time, sleep
from datetime import date, datetime
import logging
import json


from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from LibraModules import *
import TransferType

class LibraPGHandler():
    def __init__(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

        return

    def GetRecentTransaction(self, limit, offset):
        s = self.session()

        try:
            result = s.query(LibraTransaction).order_by(LibraTransaction.version.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            return False, None
        finally:
            s.close()

        infoList = []
        for i in result:
            info = {
                "version": i.version
            }

            infoList.append(info)

        return True, infoList

    def GetRecentTransactionAboutCurrency(self, limit, offset, currency):
        s = self.session()

        try:
            result = s.query(LibraTransaction).filter(LibraTransaction.currency == currency).order_by(LibraTransaction.version.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            return False, None
        finally:
            s.close()

        infoList = []
        for i in result:
            info = {
                "version": i.version
            }

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

    def GetTransactionsByAddress(self, address, currency, limit, offset):
        s = self.session()

        try:
            result  = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address))
            if currency:
                result = result.filter(LibraTransaction.currency == currency)

            result = result.order_by(LibraTransaction.version.desc()).offset(offset).limit(limit).all()
        except OperationalError:
            return False, None
        finally:
            s.close()

        infoList = []
        for i in result:
            info = {}
            info["version"] = i.version
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number

            infoList.append(info)

        return True, infoList

    def GetTransactionsForWallet(self, address, currency, flows, offset, limit):
        s = self.session()

        try:
            if flows is not None:
                if flows == 0:
                    s.query(LibraTransaction).filter(LibraTransaction.sender == address)
                elif flows == 1:
                    s.query(LibraTransaction).filter(LibraTransaction.receiver == address)
            else:
                result = s.query(LibraTransaction).filter(or_(LibraTransaction.sender == address, LibraTransaction.receiver == address))

            if currency:
                result = result.filter(LibraTransaction.currency == currency)

            result = result.filter(LibraTransaction.transaction_type.in_(TransferType.Common.keys()))

            result = result.order_by(LibraTransaction.version.desc()).offset(offset).all()

        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        infoList = []
        for idx, i in enumerate(result):
            if idx == limit:
                break

            info = {}
            info["version"] = i.version
            info["sender"] = i.sender
            info["sequence_number"] = i.sequence_number

            infoList.append(info)

        return True, infoList

    def GetTransactionTime(self, sender, sequence_number):
        s = self.session()
        try:
            result = s.query(LibraSignedTransaction).filter(LibraSignedTransaction.sender == sender).filter(LibraSignedTransaction.sequence_number == sequence_number).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return None
        finally:
            s.close()

        return result.date if result else None

    def AddTransactionInfo(self, sender, seqNum, timestamp, sigtxn):
        s = self.session()

        try:
            info = LibraSignedTransaction(
                sender = sender,
                sequence_number = seqNum,
                time = timestamp,
                sigtxn = sigtxn
            )

            s.add(info)
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False
        finally:
            s.close()

        return True
