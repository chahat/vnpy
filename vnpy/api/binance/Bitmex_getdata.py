from __future__ import absolute_import
from time import sleep
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

# You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

from six.moves import input

from vnpy.api.binance.vnbinance import BinanceApi
from datetime import timedelta

import json
import datetime
from pymongo import MongoClient, ASCENDING
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME

config = open('config_bitmex.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SYMBOLS = setting['SYMBOLS']
DATE = setting['DATE']

mc = MongoClient(MONGO_HOST, MONGO_PORT)
db = mc[MINUTE_DB_NAME]


def queryKlines(symbol, granularity, start):
    """"""
    path = 'https://www.bitmex.com/api/v1/trade/bucketed'
    params = {
        'binSize': granularity,
        'symbol': symbol,
        'startTime' : start
    }

    try:
        resp = requests.get(path, params = params)
        print('query start %s', start)
        if resp.status_code == 200:
            return True, resp.json()
        else:
            error = {
                'params': params,
                'code': resp.status_code,
                'msg': resp.json()
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

    l = SYMBOLS.split('_')
    cl = db[l[2]+l[-1]+'.'+l[0]]

    cl.ensure_index([('datetime', ASCENDING)], unique=True)

    startDt = datetime.datetime.strptime(DATE, '%Y%m%d')
    endDt = datetime.datetime(2019, 02, 13)



    while(startDt < endDt):
        success, val = queryKlines(l[2]+l[-1], '5m', startDt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        if success:
            lastClose = None
            for d in val:
                bar = VtBarData()
                bar.gatewayName = l[0]
                bar.rawData = d
                bar.symbol = d['symbol']
                bar.exchange = l[0]
                bar.vtSymbol = '.'.join([bar.symbol, bar.exchange])
                bar.datetime = datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z')
                bar.date = bar.datetime.strftime('%Y%m%d')
                bar.time = bar.datetime.strftime('%H:%M:%S')
                bar.open = d['open']
                bar.high = d['high']
                bar.low = d['low']
                bar.close = d['close']
                bar.volume = d['volume']
                lastClose = bar.datetime
                d = bar.__dict__
                flt = {'datetime': bar.datetime}
                cl.replace_one(flt, d, True)
            if lastClose:
                startDt = lastClose
            else:
                print('lastClose did not change.')
                exit()
        else:
            if val['code'] is 429:
                print('code %s msg %s'% (val['code'], val['msg']))
                sleep(1)
            if val['code'] is 418:
                print('code %s msg %s' % (val['code'], val['msg']))
                exit()





