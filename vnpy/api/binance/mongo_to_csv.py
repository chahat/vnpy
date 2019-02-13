import pandas as pd
from pymongo import MongoClient
import json
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME


config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SYMBOLS = 'BTCUSD.COINBASE'

mc = MongoClient(MONGO_HOST, MONGO_PORT)
db = mc[MINUTE_DB_NAME]


if __name__ == '__main__':
    cl = db[SYMBOLS]
    cursor = cl.find(projection={'datetime': True, 'open': True, 'high': True, 'low': True, 'close': True, 'volume': True})
    df = pd.DataFrame(list(cursor))

    # Delete the _id
    df.to_csv(SYMBOLS+'.csv', index=False)