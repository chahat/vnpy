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

from lxml.html import fromstring
import requests
from itertools import cycle
import traceback

from http import cookiejar  # Python 2: import cookielib as cookiejar
class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            if check_proxy(proxy):
                proxies.add(proxy)
    return proxies

def check_proxy(proxy):
    try:
        response = requests.get('https://httpbin.org/ip',proxies={"http": proxy, "https": proxy})
        print(" proxy %s %s" % (response.status_code, response.json()))
        return True
    except:
        return False

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
                apikey = m.group()
                return apikey
            else:
                raise Exception(u'The regex failed to extract the key from mail body %s' % coinapi_email.excerpt)

def getHeaders():
    # APIKEY = generateNewApiKey()
    # print(APIKEY)
    headers = {'X-CoinAPI-Key': APIKEY}
    return headers


def registerForFreeAPIKey(email):

    url = 'https://rest.coinapi.io/www/freeplan'
    params = {
        'email': email,
        'name': email.split('@')[0],
        'title': email.split('@')[0],
        'company': "1-10"
    }
    #proxy = next(proxy_pool)
    resp = requests.post(url, json=params) #, proxies={"http": proxy, "https": proxy}

    if resp.status_code != 200:
        raise Exception(u'%s Email registration for free api failed' % email)


#----------------------------------------------------------------------
def generateVtBar(symbol, d):
    """GenerateKLine"""
    l = symbol.split('_')
    bar = VtBarData()
    bar.gatewayName = l[0]
    bar.rawData = d
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

    cl = db[symbol]                                                 
    cl.ensure_index([('datetime', ASCENDING)], unique=True)         
    
    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')
    url = 'https://rest.coinapi.io/v1/ohlcv/%s/history' % symbol

    while(startDt < endDt):
        startTime = time.time()
        params = {
            'period_id': period,
            'time_start': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
            #'time_end': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
            'limit': 1000
        }
        #proxy = next(proxy_pool)
        s = requests.Session()
        s.cookies.set_policy(BlockAll())
        resp = s.get(url, headers=getHeaders(), params=params) #, proxies={"http": proxy, "https": proxy}

        #APIKEY_O.update(resp.headers['X-RateLimit-Remaining'], resp.headers['X-RateLimit-Reset'])

        if resp.status_code != 200:
            print(u'%s Data download failed. resp code %s' % (symbol, resp.status_code))
            return

        l = resp.json()
        bar = None
        for d in l:
            bar = generateVtBar(symbol, d)
            d = bar.__dict__
            flt = {'datetime': bar.datetime}
            cl.replace_one(flt, d, True)

        if bar:
            startDt = bar.datetime
        else:
            print('lastClose did not change.')
            exit()

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
        downMinuteBarBySymbol(symbol, '1MIN', start, end)
        time.sleep(1)

    print('-' * 50)
    print(u'Contract minute line data download completed')
    print('-' * 50)

proxy_pool = None
if __name__ == '__main__':
    # proxies = get_proxies()
    # proxy_pool = cycle(proxies)
    downloadAllMinuteBar('20180913', '20181130')
    