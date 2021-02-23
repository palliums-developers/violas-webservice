import configparser
from sqlalchemy import create_engine

from ViolasModules import Base as ViolasBase
from LibraModules import Base as LibraBase

config = configparser.ConfigParser()
config.read("./config.ini")

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"

ViolasEngine = create_engine(violasDBUrl)

ViolasBase.metadata.tables["transactions"].drop(ViolasEngine)
ViolasBase.metadata.tables["address_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["signed_transactions"].drop(ViolasEngine)
ViolasBase.metadata.tables["sso_user_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["sso_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["governor_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["deposit_product"].drop(ViolasEngine)
ViolasBase.metadata.tables["deposit_order"].drop(ViolasEngine)
ViolasBase.metadata.tables["interest_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["borrow_product"].drop(ViolasEngine)
ViolasBase.metadata.tables["borrow_order"].drop(ViolasEngine)
ViolasBase.metadata.tables["liability_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["new_registered_record"].drop(ViolasEngine)
ViolasBase.metadata.tables["incentive_issue_record"].drop(ViolasEngine)
ViolasBase.metadata.tables["device_info"].drop(ViolasEngine)
ViolasBase.metadata.tables["message_record"].drop(ViolasEngine)
ViolasBase.metadata.tables["notice_record"].drop(ViolasEngine)
ViolasBase.metadata.tables["notice_read_record"].drop(ViolasEngine)

ViolasBase.metadata.tables["transactions"].create(ViolasEngine)
ViolasBase.metadata.tables["address_info"].create(ViolasEngine)
ViolasBase.metadata.tables["signed_transactions"].create(ViolasEngine)
ViolasBase.metadata.tables["sso_user_info"].create(ViolasEngine)
ViolasBase.metadata.tables["sso_info"].create(ViolasEngine)
ViolasBase.metadata.tables["governor_info"].create(ViolasEngine)
ViolasBase.metadata.tables["deposit_product"].create(ViolasEngine)
ViolasBase.metadata.tables["deposit_order"].create(ViolasEngine)
ViolasBase.metadata.tables["interest_info"].create(ViolasEngine)
ViolasBase.metadata.tables["borrow_product"].create(ViolasEngine)
ViolasBase.metadata.tables["borrow_order"].create(ViolasEngine)
ViolasBase.metadata.tables["liability_info"].create(ViolasEngine)
ViolasBase.metadata.tables["new_registered_record"].create(ViolasEngine)
ViolasBase.metadata.tables["incentive_issue_record"].create(ViolasEngine)
ViolasBase.metadata.tables["device_info"].create(ViolasEngine)
ViolasBase.metadata.tables["message_record"].create(ViolasEngine)
ViolasBase.metadata.tables["notice_record"].create(ViolasEngine)
ViolasBase.metadata.tables["notice_read_record"].create(ViolasEngine)

libraDBInfo = config["LIBRA DB INFO"]
libraDBUrl = f"{libraDBInfo['DBTYPE']}+{libraDBInfo['DRIVER']}://{libraDBInfo['USERNAME']}:{libraDBInfo['PASSWORD']}@{libraDBInfo['HOSTNAME']}:{libraDBInfo['PORT']}/{libraDBInfo['DATABASE']}"

LibraEngine = create_engine(libraDBUrl)

LibraBase.metadata.drop_all(LibraEngine)
LibraBase.metadata.create_all(LibraEngine)
