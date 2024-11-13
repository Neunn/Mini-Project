# Import Library
import sqlite3
import pandas as pd
import configparser
import time
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
from settrade_v2 import Investor
from settrade_v2.errors import SettradeError

# จำนวนครั้งในการเรียก API ไม่เกิน 5 ครั้งต่อวินาที สำหรับกลุ่ม API ในการดึงข้อมูล


# อ่านไฟล์ Config เพื่อไปใช้ใน settrade
configParser = configparser.RawConfigParser()
configFilePath = "./Source/user-info.properties"
configParser.read(configFilePath)
app_id = configParser.get("STT-OPENAPI-AUTH", "app-id")
app_secret = configParser.get("STT-OPENAPI-AUTH", "app-secret")
app_code = configParser.get("STT-OPENAPI-AUTH", "app-code")
broker_id = configParser.get("STT-OPENAPI-AUTH", "broker-id")
line_token = configParser.get("LINE-API", "token")

investor = Investor(
    app_id=app_id,
    app_secret=app_secret,
    broker_id=broker_id,
    app_code=app_code,
    is_auto_queue=False,
)

sqlite_file = "./Database/database.db"
stock_frame = pd.read_csv("./Source/stock.csv", index_col=0)


def Connect_Database(_sqlite_file):
    """
    Function สำหรับสร้าง Connection Database
    """
    try:
        CONN_ = sqlite3.connect(database=_sqlite_file)
    except sqlite3.Error as e:
        CONN_ = None
        print(e)

    return CONN_


def Past_Data_Pull(_stock_frame, _hist_day):
    """
    Function สำหรับดึงข้อมูลย้อนหลัง 3 เดือนแล้วนำไปเก็บไว้ใน DataBase
    """
    CONN_ = Connect_Database(_sqlite_file=sqlite_file)
    CURSOR_ = CONN_.cursor()
    MARKET_ = investor.MarketData()
    try:
        for INDEX_, DATA_STOCK_ in enumerate(_stock_frame.values):
            print(f"INDEX_ = {INDEX_}")
            print(f"DATA_STOCK_ {DATA_STOCK_}")
            if DATA_STOCK_[1] == 0:
                RAW_DATA_ = MARKET_.get_candlestick(
                    symbol=DATA_STOCK_[0],
                    interval="1m",
                    start=(datetime.now() - timedelta(days=_hist_day)).strftime(
                        "%Y-%m-%dT00:00:00"
                    ),
                    end=datetime.now().strftime("%Y-%m-%dT00:00:00"),
                    normalized=False,
                )
                DATA_HIST_ = pd.DataFrame(RAW_DATA_).iloc[:, 1:]
                # DATA_HIST_["time"] = pd.to_datetime(DATA_HIST_["time"], unit="s")
                INSERT_LIST = []
                print(f"len(DATA_HIST_) = {len(DATA_HIST_)}")
                for i in range(len(DATA_HIST_)):
                    INSERT_LIST.append(DATA_HIST_.iloc[i, :].tolist())
                print(INSERT_LIST)
                CURSOR_.executemany(
                    f"""INSERT INTO {DATA_STOCK_[0]}(date, open_price, high_price, low_price, close_price, volume, value)
                    VALUES(?, ?, ?, ?, ?, ?, ?);""",
                    INSERT_LIST,
                )
                CONN_.commit()
                _stock_frame.iloc[INDEX_, 1] = 1
            else:
                pass
        print()
        print()
        print(_stock_frame)
        print()
        _stock_frame.to_csv("./Source/stock.csv")
        CONN_.close()

    except SettradeError as e:
        print("---- error message  ----")
        print(e)
        print("---- error code ----")
        print(e.code)
        print("---- status code ----")
        print(e.status_code)


def Create_Table(_stock_frame, _sqlite_file=sqlite_file):
    """
    Function สำหรับการสร้าง Table แม้มีการสร้าง
    """
    try:
        CONN_ = Connect_Database(_sqlite_file=_sqlite_file)
        CURSOR_ = CONN_.cursor()
        for i in _stock_frame.values:
            CURSOR_.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {i[0]} 
                (id INTEGER PRIMARY KEY,
                date INTEGER,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                value REAL);
                """
            )
            CONN_.commit()
        CONN_.close()
        Past_Data_Pull(_stock_frame=_stock_frame, _hist_day=30)

    except sqlite3.Error as e:
        print(e)


def Send_Line_Notification(_last_df, _result):
    """
    Function สำหรับการส่ง Line notification การแจ้งเตือนของหุ้นโดยที่
    0 = ไม่ทำอะไร
    1 = ซื้อ
    -1 = ขาย
    """
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_token}"}
    if _last_df == 0:
        pass
    elif _last_df == 1:
        MESSAGE_ = f"signal = 1, หุ้น {_result['data']['symbol']} 'ควร ซื้อ น้าาาาา'"
    elif _last_df == -1:
        MESSAGE_ = f"signal = -1, หุ้น {_result['data']['symbol']} 'ควร ขาย น้าาาาา'"
    data = {"message": MESSAGE_}
    print(MESSAGE_)

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Notification sent successfully!")
    else:
        print(f"Failed to send notification: {response.status_code}")


def Moving_Average_Forecast(_sqlite_file, _table, _result):
    """
    Function สำหรับคำนวณ Moving Average Filter
    """
    CONN_ = Connect_Database(_sqlite_file=_sqlite_file)
    print()
    DF_ = pd.read_sql_query(f"SELECT * FROM {_table}", CONN_)
    # print(DF_.info())
    print()

    DF_["Signal"] = 0  # Default no signal
    DF_["SMA_3"] = DF_["close_price"].rolling(window=3).mean()
    DF_["SMA_10"] = DF_["close_price"].rolling(window=10).mean()
    DF_.loc[DF_["SMA_3"] > DF_["SMA_10"], "Signal"] = 1  # 1 = ซื้อ
    DF_.loc[DF_["SMA_3"] < DF_["SMA_10"], "Signal"] = -1  # -1 = ขาย
    print(DF_)
    print()
    Send_Line_Notification(_last_df=DF_.iloc[-1]["Signal"], _result=_result)


def Sub_Message_Update(_result, _sqlite_file, _table):
    """
    Function สำหรับ Update เพิ่มใน Database
    """
    # print(f" Update {_result} in {_table}")
    print(f"")
    print(
        f"""
            _table = {_result["data"]["symbol"]},
            time.time() = {time.time()},
            _result["data"]["projected_open_price"] = {_result["data"]["projected_open_price"]},
            _result["data"]["high"] = {_result["data"]["high"]},
            _result["data"]["low"] = {_result["data"]["low"]},
            _result["data"]["last"] = {_result["data"]["last"]},
            _result["data"]["total_volume"] = {_result["data"]["total_volume"]},
            _result["data"]["total_value"] = {_result["data"]["total_value"]}"""
    )
    print(f"")
    LIST_INSERT_ = [
        (time.time()),
        (_result["data"]["projected_open_price"]),
        (_result["data"]["high"]),
        (_result["data"]["low"]),
        (_result["data"]["last"]),
        (_result["data"]["total_volume"]),
        (_result["data"]["total_value"]),
    ]

    CONN_ = Connect_Database(_sqlite_file)
    CURSOR_ = CONN_.cursor()
    CURSOR_.execute(
        f"""
        INSERT INTO {_result["data"]["symbol"]} (date, open_price, high_price, low_price, close_price, volume, value)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [
            time.time(),
            _result["data"]["projected_open_price"],
            _result["data"]["high"],
            _result["data"]["low"],
            _result["data"]["last"],
            _result["data"]["total_volume"],
            _result["data"]["total_value"],
        ],
    )
    CONN_.commit()
    CONN_.close()
    Moving_Average_Forecast(_sqlite_file=_sqlite_file, _table=_table, _result=_result)


def Stock_Sub(_sqlite_file=sqlite_file):
    """
    Function สำหรับการสร้าง Stock Sub
    """
    REALTIME_ = investor.RealtimeDataConnection()
    STOCK_NAME_ = stock_frame.iloc[:, 0].values.tolist()
    STOCK_LIST_ = []
    for i in STOCK_NAME_:
        a = REALTIME_.subscribe_price_info(
            symbol=i,
            on_message=Sub_Message_Update,
            kwargs={"_sqlite_file": _sqlite_file, "_table": i},
        )
        a.start()
        STOCK_LIST_.append(a)
    print(f"STOCK_LIST_ = {STOCK_LIST_}")
    return STOCK_LIST_


if __name__ == "__main__":
    Create_Table(_stock_frame=stock_frame, _sqlite_file=sqlite_file)
    stock_list = Stock_Sub(_sqlite_file=sqlite_file)
    while True:
        time.sleep(1)
