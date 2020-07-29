import configparser
from sqlalchemy import create_engine

from ViolasModules import Base

config = configparser.ConfigParser()
config.read("./config.ini")

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"

engine = create_engine(violasDBUrl)

Base.metadata.tables["signed_transactions"].drop(engine)
Base.metadata.tables["sso_user_info"].drop(engine)
Base.metadata.tables["sso_info"].drop(engine)
Base.metadata.tables["governor_info"].drop(engine)

Base.metadata.tables["signed_transactions"].create(engine)
Base.metadata.tables["sso_user_info"].create(engine)
Base.metadata.tables["sso_info"].create(engine)
Base.metadata.tables["governor_info"].create(engine)
