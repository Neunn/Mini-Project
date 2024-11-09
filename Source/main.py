# Import Library
import sqlite3
import pandas as pd
import configparser
from datetime import datetime
from settrade_v2 import Investor


# จำนวนครั้งในการเรียก API ไม่เกิน 5 ครั้งต่อวินาที สำหรับกลุ่ม API ในการดึงข้อมูล


# อ่านไฟล์ Config เพื่อไปใช้ใน settrade
configParser = configparser.RawConfigParser()
configFilePath = "Source/user-info.properties"
configParser.read(configFilePath)
app_id = configParser.get("STT-OPENAPI-AUTH", "app-id")
app_secret = configParser.get("STT-OPENAPI-AUTH", "app-secret")
app_code = configParser.get("STT-OPENAPI-AUTH", "app-code")
broker_id = configParser.get("STT-OPENAPI-AUTH", "broker-id")


investor = Investor(
    app_id=app_id,
    app_secret=app_secret,
    broker_id=broker_id,
    app_code=app_code,
    is_auto_queue=False,
)

SQLITE_FILE = "./Database/database.db"


def Setup_Database(SQLITE_FILE):
    """
    Function สำหรับสร้าง Connection Database
    """

    try:
        CONN = sqlite3.connect(database=SQLITE_FILE)
    except sqlite3.Error as e:
        CONN = None
        print(e)

    return CONN


def Create_Table():
    """
    Function สำหรับการสร้าง Table
    """
    try:
        CONN = Setup_Database(SQLITE_FILE=SQLITE_FILE)
        CURSOR = CONN.cursor()
        CURSOR.execute(
            """
            CREATE TABLE IF NOT EXITS Stock_Data 
            (id INTEGER PRIMARY KEY,
            stock_name TEXT NOT NULL,
            time int,
            quantity int,
            price float)
            """
        )

    except sqlite3.Error as e:
        print(e)


if __name__ == "__main__":
    Setup_Database(SQLITE_FILE=SQLITE_FILE)
