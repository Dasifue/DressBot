from sqlalchemy import Engine, create_engine
from dotenv import load_dotenv
from os import getenv

load_dotenv()

url = "mysql+pymysql://{}:{}@{}/{}".format(
    getenv("DB_USER"),
    getenv("DB_PASSWORD"),
    getenv("DB_HOST"),
    getenv("DB_NAME")   
)

ENGINE: Engine = create_engine(url=url, echo=True)