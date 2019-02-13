from __future__ import absolute_import
import time
from urllib import urlencode
import requests
import traceback
from vnpy.trader.vtObject import VtBarData

import logging
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1
#
# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

from six.moves import input

from vnpy.api.binance.vnbinance import BinanceApi

import json
import datetime
from pymongo import MongoClient, ASCENDING
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME

config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SYMBOLS = setting['SYMBOLS']
SYM = setting['SYM']
DATE = setting['DATE']
EXCHANGE = setting['EXCHANGE']

mc = MongoClient(MONGO_HOST, MONGO_PORT)
db = mc[MINUTE_DB_NAME]


def queryKlines(symbol, interval, limit=0, startTime=0, endTime=0):
    """"""
    path = 'https://api.binance.com/api/v1/klines'

    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
        'startTime' : startTime,
        'endTime' : endTime
    }

    try:
        resp = requests.get(path, params=params)
        print('query start %s, end %s', datetime.datetime.utcfromtimestamp(startDtMs/1000.0), datetime.datetime.utcfromtimestamp(endDtMs/1000.0))
        if resp.status_code == 200:
            return True, resp.json()
        else:
            error = {
                'params': params,
                'code': resp.status_code,
                'msg': resp.json()['msg']
            }
            return False, error
    except Exception as e:
        error = {
            'params': params,
            'code': e,
            'msg': traceback.format_exc()
        }
        return False, error

if __name__ == '__main__':

    cl = db[SYMBOLS]
    cl.ensure_index([('datetime', ASCENDING)], unique=True)

    startDt = datetime.datetime.strptime(DATE, '%Y%m%d')
    endDt = datetime.datetime(2019, 02, 13)

    epoch = datetime.datetime.utcfromtimestamp(0)

    startDtMs = long((startDt - epoch).total_seconds() * 1000) #time.gmtime(startDt.timetuple())*1000
    endDtMs = long((endDt - epoch).total_seconds() * 1000) #time.gmtime(endDt.timetuple())*1000

    print(startDtMs)
    print(endDtMs)
    while(startDtMs < endDtMs):
        success, val = queryKlines(SYM, '5m', 1000, startDtMs, endDtMs)
        if success:
            lastClose = None
            for d in val:
                bar = VtBarData()
                bar.gatewayName = EXCHANGE
                bar.rawData = d
                bar.symbol = SYMBOLS
                bar.exchange = EXCHANGE
                bar.vtSymbol = '/'.join([bar.symbol, bar.exchange])
                bar.datetime = datetime.datetime.utcfromtimestamp(d[0]/1000.0)
                bar.date = bar.datetime.strftime('%Y%m%d')
                bar.time = bar.datetime.strftime('%H:%M:%S')
                bar.open = d[1]
                bar.high = d[2]
                bar.low = d[3]
                bar.close = d[4]
                bar.volume = d[5]
                lastClose = d[6]
                d = bar.__dict__
                flt = {'datetime': bar.datetime}
                cl.replace_one(flt, d, True)
            if lastClose:
                startDtMs = lastClose
            else:
                print('lastClose did not change.')
                exit()
        else:
            if val['code'] is 429 or 418:
                print('code %s', val['code'])
                exit()





