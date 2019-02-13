from __future__ import absolute_import
import pandas as pd
from matplotlib import pyplot as plt
from mpl_finance import candlestick_ohlc

import json
from pymongo import MongoClient, ASCENDING
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
import matplotlib.dates as mdates

import plotly
plotly.tools.set_credentials_file(username='chahat', api_key='yPXDlrhq3tQaEyeEPDC1')

import plotly.plotly as py
import plotly.graph_objs as go
from plotly.tools import FigureFactory as FF

import re
config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SYMBOLS = 'BINANCE_SPOT_ETH_USDT'

mc = MongoClient(MONGO_HOST, MONGO_PORT)
db = mc[MINUTE_DB_NAME]


def plotCandlestick(af):
    df = af.iloc[:1000]
    df["datetime"] = df["datetime"].apply(mdates.date2num)
    df["close"] = pd.to_numeric(df["close"])
    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    ohlc = df[['datetime', 'open', 'high', 'low', 'close']]
    f1, ax = plt.subplots(figsize=(10, 5))

    # plot the candlesticks
    candlestick_ohlc(ax, ohlc.values, colorup='green', colordown='red')
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    # Saving image
    # plt.savefig('OHLC HDFC.png')

    # In case you dont want to save image but just displya it
    plt.show()

def plotNormal(df, name):
    # df = df.iloc[:10000]
    plt.plot(df['datetime'], df[name])
    plt.xlabel('Date')
    plt.ylabel(name)
    plt.title('Simple time series plot for '+name)
    plt.show()

if __name__ == '__main__':
    cl = db[SYMBOLS]
    regx = re.compile("^2017")
    cursor = cl.find(projection={'datetime': True, 'open': True, 'high': True, 'close': True, 'low': True}, filter={'date': regx}) #
    clist = list(cursor)
    print(len(clist))
    df = pd.DataFrame(clist)

    df["close"] = pd.to_numeric(df["close"])
    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])

    fig = FF.create_ohlc(df['open'], df['high'], df['low'], df['close'], dates=df['datetime'])

    py.iplot(fig, filename='eth-usdt-binance-ohlc-2017')

    # data = [go.Scatter(x=df['datetime'], y=df['open'])]
    # py.iplot(data, filename='open')

    # plt.plot(df['datetime'], df['open'])
    # plt.xlabel('Date')
    # plt.ylabel('open')
    # plt.title('Simple time series plot for ')
    # plt.show()
    # plotNormal(df, 'open')










