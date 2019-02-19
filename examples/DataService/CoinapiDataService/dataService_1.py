# encoding: UTF-8

from __future__ import print_function

import json
import time
from time import sleep
import datetime
import re

import requests
import logging
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

from pymongo import MongoClient, ASCENDING

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
from collections import deque
from vnpy.trader.vtConstant import (EMPTY_INT, EMPTY_STRING)
from guerrillamail import GuerrillaMailSession


# LoadConfiguration
config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
APIKEY = setting['APIKEY']
SYMBOLS = setting['SYMBOLS']

mc = MongoClient(MONGO_HOST, MONGO_PORT)                        # MongoLink
db = mc[MINUTE_DB_NAME]                                         # Database

CoinAPI_DB_NAME = 'CoinAPIKey'
dbCoin = mc[CoinAPI_DB_NAME]
clCoin = dbCoin[CoinAPI_DB_NAME]
#cl.ensure_index([('datetime', ASCENDING)], unique=True)

#APIKEY_Q = deque()

class APIKeyObject(object):

    def __init__(self):
        #self.limit = EMPTY_INT
        self.remaining = EMPTY_INT
        self.reset = EMPTY_STRING
        self.key = EMPTY_STRING

    @staticmethod
    def createFromData(key, remaining = 100, reset = EMPTY_STRING):
        d = APIKeyObject()
        d.key = key
        d.remaining = remaining
        d.reset = reset

    def update(self, remaining, reset):
        self.remaining = remaining
        self.reset = reset

APIKEY_O = APIKeyObject()

def generateNewApiKey():
    session = GuerrillaMailSession()
    email_add = session.get_session_state()['email_address']
    registerForFreeAPIKey(email_add)
    while True:
        coinapi_email = next((email for email in session.get_email_list() if email.sender == 'no-reply@coinapi.io'), None)
        if coinapi_email is None:
            sleep(2)
        else:
            m = re.search(r'[A-Z0-9-]{36}', coinapi_email.excerpt)
            if m:
                apikey = APIKeyObject.createFromData(m.group())
                clCoin.insert_one(apikey.__dict__)
                return apikey
            else:
                raise Exception(u'The regex failed to extract the key from mail body %s' % coinapi_email.excerpt)

def getHeaders():
    global APIKEY_O
    if APIKEY_O.remaining is EMPTY_INT:
        existingKey = clCoin.find_one({'remaining': {'$gt': 0}})
        if existingKey is None:
            APIKEY_O = generateNewApiKey()
        else:
            APIKEY_O.__dict__ = existingKey  # _one('remaining:{$gt:0}')

    elif APIKEY_O.remaining == 0:
        clCoin.update(APIKEY_O.__dict__)
        #{$or: [{high:{$gt:8400}}, {low:{$lt:8300}}]}

    headers = {'X-CoinAPI-Key': APIKEY_O.key}
    return headers


def registerForFreeAPIKey(email):

    url = 'https://rest.coinapi.io/www/freeplan'
    params = {
        'email': email,
        'name': email.split('@')[0],
        'title': email.split('@')[0],
        'company': "1-10"
    }
    resp = requests.post(url, json=params)

    if resp.status_code != 200:
        raise Exception(u'%s Email registration for free api failed' % email)


#----------------------------------------------------------------------
def generateVtBar(symbol, d):
    """GenerateKLine"""
    l = symbol.split('_')
    bar = VtBarData()
    bar.symbol = l[-2] + l[-1]
    bar.exchange = l[0]
    bar.vtSymbol = '/'.join([bar.symbol, bar.exchange])
    bar.datetime = datetime.datetime.strptime(d['time_open'], '%Y-%m-%dT%H:%M:%S.%f0Z')
    bar.date = bar.datetime.strftime('%Y%m%d')
    bar.time = bar.datetime.strftime('%H:%M:%S')
    bar.open = d['price_open']
    bar.high = d['price_high']
    bar.low = d['price_low']
    bar.close = d['price_close']
    bar.volume = d['volume_traded']
    
    return bar

#----------------------------------------------------------------------
def downMinuteBarBySymbol(symbol, period, start, end):
    """Download minute line data for a contract"""
    startTime = time.time()
    
    cl = db[symbol]                                                 
    cl.ensure_index([('datetime', ASCENDING)], unique=True)         
    
    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')
    
    url = 'https://rest.coinapi.io/v1/ohlcv/%s/history' %symbol
    params = {
        'period_id': period,
        'time_start': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'time_end': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'limit': 10000
    }
    resp = requests.get(url, headers=getHeaders(), params=params)

    #APIKEY_O.update(resp.headers['X-RateLimit-Remaining'], resp.headers['X-RateLimit-Reset'])

    if resp.status_code != 200:
        print(u'%s Data download failed. resp code %' % (symbol, resp.status_code))
        return

    for d in l:
        bar = generateVtBar(symbol, d)
        d = bar.__dict__
        flt = {'datetime': bar.datetime}
        cl.replace_one(flt, d, True)
        
    endTime = time.time()
    cost = (endTime - startTime) * 1000

    print(u'Contract %s data download completed %s - %s, time %s milliseconds' %(symbol, l[0]['time_period_start'],
                                                  l[-1]['time_period_end'], cost))

#----------------------------------------------------------------------
def downloadAllMinuteBar(start, end):
    """Download minute line data for contracts in all configurations"""
    print('-' * 50)
    print(u'Start downloading contract minute line data')
    print('-' * 50)
    
    for symbol in SYMBOLS:
        downMinuteBarBySymbol(symbol['SYMBOL'], '1MIN', start, end)
        time.sleep(1)

    print('-' * 50)
    print(u'Contract minute line data download completed')
    print('-' * 50)


    