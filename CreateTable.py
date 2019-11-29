import configparser
from sqlalchemy import create_engine

from ViolasModules import Base

config = configparser.ConfigParser()
config.read("./config.ini")

violasDBInfo = config["VIOLAS DB INFO"]
violasDBUrl = f"{violasDBInfo['DBTYPE']}+{violasDBInfo['DRIVER']}://{violasDBInfo['USERNAME']}:{violasDBInfo['PASSWORD']}@{violasDBInfo['HOSTNAME']}:{violasDBInfo['PORT']}/{violasDBInfo['DATABASE']}"

engine = create_engine(violasDBUrl)

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
