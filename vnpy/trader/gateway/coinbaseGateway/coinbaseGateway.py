# encoding: UTF-8

'''
vnpy.api.bitmexGatewayAccess
'''
from __future__ import print_function

import os
import json
import hashlib
import hmac
import time
import traceback
import base64
import uuid
from datetime import datetime, timedelta
from copy import copy

from vnpy.api.coinbase import CoinbaseRestApi, CoinbaseWebsocketApi
from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath, getTempPath

# DirectionMapping
directionMap = {}
directionMap[DIRECTION_LONG] = 'buy'
directionMap[DIRECTION_SHORT] = 'sell'
directionMapReverse = {v:k for k,v in directionMap.items()}

# PriceTypeMapping
priceTypeMap = {}
priceTypeMap[PRICETYPE_LIMITPRICE] = 'limit'
priceTypeMap[PRICETYPE_MARKETPRICE] = 'market'

# DataCacheDictionary
cancelDict = {}     # orderID:req
orderDict = {}      # sysID:order
orderSysDict = {}   # orderID:sysID


########################################################################
class CoinbaseGateway(VtGateway):
    """BitfinexInterface"""

    #----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName=''):
        """Constructor"""
        super(CoinbaseGateway, self).__init__(eventEngine, gatewayName)

        self.restApi = RestApi(self)
        self.wsApi = WebsocketApi(self)

        self.qryEnabled = False         # Do you want to start a loop query?

        self.fileName = self.gatewayName + '_connect.json'
        self.filePath = getJsonPath(self.fileName, __file__)
        
    #----------------------------------------------------------------------
    def connect(self):
        """Connection"""
        try:
            f = open(self.filePath)
        except IOError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'Error reading connection configuration, please check'
            self.onLog(log)
            return

        # ParsingJsonFiles
        setting = json.load(f)
        f.close()
        try:
            apiKey = str(setting['apiKey'])
            secretKey = str(setting['secretKey'])
            passphrase = str(setting['passphrase'])
            sessionCount = int(setting['sessionCount'])
            symbols = setting['symbols']
        except KeyError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'Connection configuration missing field, please check'
            self.onLog(log)
            return

        # CreateQuotesAndTradingInterfaceObjects
        self.restApi.connect(apiKey, secretKey, passphrase, sessionCount)
        self.wsApi.connect(apiKey, secretKey, passphrase, symbols)

        # InitializeAndStartTheQuery
        self.initQuery()

    #----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """SubscribeToTheMarket"""
        pass

    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """Billing"""
        return self.restApi.sendOrder(orderReq)

    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """Withdrawal"""
        self.restApi.cancelOrder(cancelOrderReq)

    #----------------------------------------------------------------------
    def close(self):
        """close"""
        self.restApi.close()
        self.wsApi.close()
    
    #----------------------------------------------------------------------
    def initQuery(self):
        """InitializeContinuousQuery"""
        if self.qryEnabled:
            # ListOfQueryFunctionsThatNeedToBeLooped
            self.qryFunctionList = [self.restApi.qryAccount]

            self.qryCount = 0           # QueryTriggerCountdown
            self.qryTrigger = 1         # QueryTriggerPoint
            self.qryNextFunction = 0    # LastRunQueryFunctionIndex

            self.startQuery()

    #----------------------------------------------------------------------
    def query(self, event):
        """Register to the query function on the event processing engine"""
        self.qryCount += 1

        if self.qryCount > self.qryTrigger:
            # EmptyCountdown
            self.qryCount = 0

            # ExecuteTheQueryFunction
            function = self.qryFunctionList[self.qryNextFunction]
            function()

            # Calculate the index of the next query function, if it exceeds the length of the list, reset it to 0
            self.qryNextFunction += 1
            if self.qryNextFunction == len(self.qryFunctionList):
                self.qryNextFunction = 0

    #----------------------------------------------------------------------
    def startQuery(self):
        """StartContinuousQuery"""
        self.eventEngine.register(EVENT_TIMER, self.query)

    #----------------------------------------------------------------------
    def setQryEnabled(self, qryEnabled):
        """SetWhetherYouWantToStartACircularQuery"""
        self.qryEnabled = qryEnabled


########################################################################
class RestApi(CoinbaseRestApi):
    """REST APIImplementation"""

    #----------------------------------------------------------------------
    def __init__(self, gateway):
        """Constructor"""
        super(RestApi, self).__init__()

        self.gateway = gateway                  # GatewayObject
        self.gatewayName = gateway.gatewayName  # GatewayObjectName
        
        self.orderSysDict = {}
        self.sysOrderDict = {}
        self.cancelDict = {}
        
    #----------------------------------------------------------------------
    def connect(self, apiKey, secretKey, passphrase, sessionCount):
        """ConnectToTheServer"""
        self.init(apiKey, secretKey, passphrase)
        self.start(sessionCount)
        
        self.writeLog(u'REST API Successful startup')
        
        self.qryContract()
        self.qryOrder()
    
    #----------------------------------------------------------------------
    def writeLog(self, content):
        """issueLog"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)
    
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """"""
        orderId = uuid.uuid1()
        vtOrderID = '.'.join([self.gatewayName, str(orderId)])
        
        req = {
            'product_id': orderReq.symbol,
            'side': directionMap[orderReq.direction],
            'price': str(orderReq.price),
            'size': str(orderReq.volume),
            'client_oid': str(orderId),
            'type': priceTypeMap[orderReq.priceType]
        }
        self.addReq('POST', '/orders', self.onSendOrder, postdict=req)
        
        return vtOrderID
    
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """"""
        orderID = cancelOrderReq.orderID
        if orderID not in orderSysDict:
            cancelDict[orderID] = cancelOrderReq
            return
        
        sysID = orderSysDict[orderID]
        path = '/orders/%s' %sysID
        self.addReq('DELETE', path, self.onCancelOrder)

    #----------------------------------------------------------------------
    def qryContract(self):
        """"""
        self.addReq('GET', '/products', self.onQryContract)

    #----------------------------------------------------------------------
    def qryAccount(self):
        """"""
        self.addReq('GET', '/accounts', self.onQryAccount)
        
    #----------------------------------------------------------------------
    def qryOrder(self):
        """"""
        req = {'status': 'all'}
        self.addReq('GET', '/orders', self.onQryOrder, params=req)

    #----------------------------------------------------------------------
    def onSendOrder(self, data, reqid):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onCancelOrder(self, data, reqid):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onError(self, code, error):
        """"""
        e = VtErrorData()
        e.gatewayName = self.gatewayName
        e.errorID = code
        e.errorMsg = error
        self.gateway.onError(e)
    
    #----------------------------------------------------------------------
    def onQryContract(self, data, reqid):
        """"""
        for d in data:
            contract = VtContractData()
            contract.gatewayName = self.gatewayName
    
            contract.symbol = d['id']
            contract.exchange = EXCHANGE_COINBASE
            contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
            contract.name = contract.vtSymbol
            
            contract.size = 1
            contract.priceTick = float(d['quote_increment'])
            contract.productClass = PRODUCT_SPOT
            
            self.gateway.onContract(contract)
        
        self.writeLog(u'合约信息查询成功')
    
    #----------------------------------------------------------------------
    def onQryAccount(self, data, reqid):
        """"""    
        for d in data:
            account = VtAccountData()
            account.gatewayName = self.gatewayName
            
            account.accountID = d['currency']
            account.vtAccountID = '.'.join([self.gatewayName, account.accountID])
            
            account.balance = float(d['balance'])
            account.available = float(d['available'])
            
            self.gateway.onAccount(account)
    
    #----------------------------------------------------------------------
    def onQryOrder(self, data, reqid):
        """"""    
        for d in data:
            order = VtOrderData()
            order.gatewayName = self.gatewayName
            
            order.orderID = d['id']
            order.vtOrderID = '.'.join([self.gatewayName, order.orderID])
            
            order.symbol = d['product_id']
            order.exchange = EXCHANGE_COINBASE
            order.vtSymbol = '.'.join([order.symbol, order.exchange])
            
            order.direction = directionMapReverse[d['side']]
            if 'price' in d:
                order.price = float(d['price'])
            order.totalVolume = float(d['size'])
            order.tradedVolume = float(d['filled_size'])
            
            date, time = d['created_at'].split('T')
            time = time.replace('Z', '')            
            order.orderTime = time
            
            if d['status'] == 'open':
                if not order.tradedVolume:
                    order.status = STATUS_NOTTRADED
                else:
                    order.status = STATUS_PARTTRADED
            else:
                if order.tradedVolume == order.totalVolume:
                    order.status = STATUS_ALLTRADED
                else:
                    order.status = STATUS_CANCELLED
            
            self.gateway.onOrder(order)
            
            orderDict[order.orderID] = order
            orderSysDict[order.orderID] = order.orderID
        
        self.writeLog(u'Entrusted information query succeeded')


########################################################################
class WebsocketApi(CoinbaseWebsocketApi):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, gateway):
        """Constructor"""
        super(WebsocketApi, self).__init__()
        
        self.gateway = gateway
        self.gatewayName = gateway.gatewayName
        
        self.apiKey = ''
        self.secretKey = ''
        self.passphrase = ''
        
        self.callbackDict = {
            'ticker': self.onTicker,
            'snapshot': self.onSnapshot,
            'l2update': self.onL2update,
            'received': self.onOrderReceived,
            'open': self.onOrderOpen,
            'done': self.onOrderDone,
            'match': self.onMatch
        }
        
        self.tickDict = {}
        self.orderDict = {}
        self.tradeSet = set()
        
        self.bidDict = {}
        self.askDict = {}
        
    #----------------------------------------------------------------------
    def connect(self, apiKey, secretKey, passphrase, symbols):
        """"""
        self.apiKey = apiKey
        self.secretKey = secretKey
        self.passphrase = passphrase
        self.symbols = symbols
        
        for symbol in symbols:
            tick = VtTickData()
            tick.gatewayName = self.gatewayName
            tick.symbol = symbol
            tick.exchange = EXCHANGE_COINBASE
            tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            self.tickDict[symbol] = tick
            
        self.start()
    
    #----------------------------------------------------------------------
    def onConnect(self):
        """ConnectionCallback"""
        self.writeLog(u'Websocket API Connection Succeeded')
        
        self.subscribe()
    
    #----------------------------------------------------------------------
    def onData(self, data):
        """DataCallback"""
        if 'type' in data:
            cb = self.callbackDict.get(data['type'], None)
            if cb:
                cb(data)
        else:
            self.writeLog(str(data))
    
    #----------------------------------------------------------------------
    def onError(self, msg):
        """ErrorCallback"""
        self.writeLog(msg)
    
    #----------------------------------------------------------------------
    def writeLog(self, content):
        """IssueLog"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)    

    #----------------------------------------------------------------------
    def authenticate(self):
        """"""
        timestamp = str(time.time())
        method = 'GET'
        path = '/users/self/verify'
        msg = timestamp + method + path
        msg = msg.encode('ascii')
        hmacKey = base64.b64decode(self.secretKey)
        signature = hmac.new(hmacKey, msg, hashlib.sha256)
        signature64 = base64.b64encode(signature.digest()).decode('utf-8').rstrip('\n')
        
        d = {
            'key': self.apiKey,
            'passphrase': self.passphrase,
            'timestamp': timestamp,
            'signature': signature64
        }
        return d

    #----------------------------------------------------------------------
    def subscribe(self):
        """"""
        req = {
            'type': 'subscribe',
            'product_ids': self.symbols,
            'channels': ['ticker', 'level2', 'user']
        }
        
        d = self.authenticate()
        req.update(d)
        self.sendReq(req)
    
    #----------------------------------------------------------------------
    def onTicker(self, d):
        """"""
        symbol = d['product_id']

        tick = self.tickDict.get(symbol, None)
        if not tick:
            return
        
        tick.openPrice = float(d['open_24h'])
        tick.highPrice = float(d['high_24h'])
        tick.lowPrice = float(d['low_24h'])
        tick.lastPrice = float(d['price'])
        tick.volume = float(d['volume_24h'])
        
        tick.datetime = datetime.now()
        tick.date = tick.datetime.strftime('%Y%m%d')
        tick.time = tick.datetime.strftime('%H:%M:%S')
        
        self.gateway.onTick(copy(tick))

    #----------------------------------------------------------------------
    def onSnapshot(self, d):
        """"""
        symbol = d['product_id']
        tick = self.tickDict.get(symbol, None)
        if not tick:
            return
        
        bid = self.bidDict.setdefault(symbol, {})
        ask = self.askDict.setdefault(symbol, {})
        
        for price, amount in d['bids']:
            bid[float(price)] = float(amount)
        
        for price, amount in d['asks']:
            ask[float(price)] = float(amount)
        
        self.generateTick(symbol)
    
    #----------------------------------------------------------------------
    def generateTick(self, symbol):
        """"""
        tick = self.tickDict[symbol]
        bid = self.bidDict[symbol]
        ask = self.askDict[symbol]
        
        
        bidPriceList = bid.keys()
        tick.bidPrice1 = bidPriceList[0]
        tick.bidPrice2 = bidPriceList[1]
        tick.bidPrice3 = bidPriceList[2]
        tick.bidPrice4 = bidPriceList[3]
        tick.bidPrice5 = bidPriceList[4]
        
        tick.bidVolume1 = bid[tick.bidPrice1]
        tick.bidVolume2 = bid[tick.bidPrice2]
        tick.bidVolume3 = bid[tick.bidPrice3]
        tick.bidVolume4 = bid[tick.bidPrice4]
        tick.bidVolume5 = bid[tick.bidPrice5]        
        
        askPriceList = ask.keys()
        askPriceList.sort()
        
        tick.askPrice1 = askPriceList[0]
        tick.askPrice2 = askPriceList[1]
        tick.askPrice3 = askPriceList[2]
        tick.askPrice4 = askPriceList[3]
        tick.askPrice5 = askPriceList[4]
        
        tick.askVolume1 = ask[tick.askPrice1]
        tick.askVolume2 = ask[tick.askPrice2]
        tick.askVolume3 = ask[tick.askPrice3]
        tick.askVolume4 = ask[tick.askPrice4]
        tick.askVolume5 = ask[tick.askPrice5]       
        
        tick.datetime = datetime.now()
        tick.date = tick.datetime.strftime('%Y%m%d')
        tick.time = tick.datetime.strftime('%H:%M:%S')
        
        self.gateway.onTick(copy(tick))
    
    #----------------------------------------------------------------------
    def onL2update(self, d):
        """"""
        symbol = d['product_id']
        tick = self.tickDict.get(symbol, None)
        if not tick:
            return
        
        bid = self.bidDict.setdefault(symbol, {})
        ask = self.askDict.setdefault(symbol, {})
        
        for direction, price, amount in d['changes']:
            price = float(price)
            amount = float(amount)
            
            if direction == 'buy':    
                if amount:
                    bid[price] = amount
                elif price in bid:
                    del bid[price]
            else:
                if amount:
                    ask[price] = amount
                elif price in ask:
                    del ask[price]
        
        self.generateTick(symbol)
    
    #----------------------------------------------------------------------
    def onMatch(self, d):
        """"""
        trade = VtTradeData()
        trade.gatewayName = self.gatewayName
        
        trade.symbol = d['product_id']
        trade.exchange = EXCHANGE_COINBASE
        trade.vtSymbol = '.'.join([trade.symbol, trade.exchange])
        
        if d['maker_order_id'] in orderDict:
            order = orderDict[d['maker_order_id']]
        else:
            order = orderDict[d['taker_order_id']]
        
        trade.orderID = order.orderID
        trade.vtOrderID = order.vtOrderID
        
        trade.tradeID = str(d['trade_id'])
        trade.vtTradeID = '.'.join([trade.gatewayName, trade.tradeID])
        
        trade.direction = order.direction
        trade.price = float(d['price'])
        trade.volume = float(d['size'])
        
        date, time = d['time'].split('T')
        time = time.replace('Z', '')            
        trade.tradeTime = time
        
        self.gateway.onTrade(trade)
    
    #----------------------------------------------------------------------
    def onOrderReceived(self, d):
        """"""
        sysID = d['order_id']
        orderID = d['client_oid']
        
        order = VtOrderData()
        order.gatewayName = self.gatewayName
        
        order.orderID = orderID
        order.vtOrderID = '.'.join([self.gatewayName, order.orderID])
        
        order.symbol = d['product_id']
        order.exchange = EXCHANGE_COINBASE
        order.vtSymbol = '.'.join([order.symbol, order.exchange])
        
        order.direction = directionMapReverse[d['side']]
        if 'price' in d:
            order.price = float(d['price'])
        order.totalVolume = float(d['size'])
        
        date, time = d['time'].split('T')
        time = time.replace('Z', '')            
        order.orderTime = time
        
        order.status = STATUS_NOTTRADED
        
        self.gateway.onOrder(order)        
        
        # CacheDelegate
        orderDict[sysID] = order
        orderSysDict[orderID] = sysID
        
        # ExecutionPendingOrder
        if orderID in cancelDict:
            req = cancelDict.pop(orderID)
            self.gateway.cancelOrder(req)
    
    #----------------------------------------------------------------------
    def onOrderOpen(self, d):
        """"""
        order = orderDict.get(d['order_id'], None)
        if not order:
            return
        
        order.tradedVolume = order.totalVolume - float(d['remaining_size'])
        if order.tradedVolume:
            order.status = STATUS_PARTTRADED
        self.gateway.onOrder(order)
    
    #----------------------------------------------------------------------
    def onOrderDone(self, d):
        """"""
        #print('done')
        #print(d)
        order = orderDict.get(d['order_id'], None)
        if not order:
            return
        
        order.tradedVolume = order.totalVolume - float(d['remaining_size'])
        
        if order.tradedVolume == order.totalVolume:
            order.status = STATUS_ALLTRADED
        else:
            order.status = STATUS_CANCELLED
        
        self.gateway.onOrder(order)        
    

#----------------------------------------------------------------------
def printDict(d):
    """"""
    print('-' * 30)
    l = d.keys()
    l.sort()
    for k in l:
        print(k, d[k])
    
