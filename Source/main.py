# Import Library
import os
import sqlite3
from datetime import datetime

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

if __name__ == "__main__":
    Setup_Database(SQLITE_FILE = SQLITE_FILE)
