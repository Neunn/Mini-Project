import time
import pandas as pd
import configparser
from datetime import datetime, timedelta
from settrade_v2 import Investor, MarketRep


configParser = configparser.RawConfigParser()
configFilePath = "Source/user-info.properties"
configParser.read(configFilePath)

investor = Investor(
    app_id=configParser.get("STT-OPENAPI-AUTH", "app-id"),  # Your app ID
    app_secret=configParser.get("STT-OPENAPI-AUTH", "app-secret"),  # Your app Secret
    broker_id="SANDBOX",
    app_code="SANDBOX",
    is_auto_queue=False,
)


# deri = investor.Derivatives(account_no="Finnize-D")  # Your account number
# equity = investor.Equity(account_no="Finnize-E")
market = investor.MarketData()

realtime = investor.RealtimeDataConnection()


# Callback function for subscribing AOT's bid offer
def on_message(message):
    print(message)


# This is subscriber object
subscriber = realtime.subscribe_price_info(symbol="CCET", on_message=on_message)
subscriber.start()  # <- This start subscription of AOT's bid offer

# run main thread forever
while True:
    time.sleep(1)
