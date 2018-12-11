# encoding: UTF-8

'''
vnpy.api.binance的gateway接入
'''
from __future__ import print_function

import os
import json
from datetime import datetime, timedelta
from copy import copy

from vnpy.api.binance import BinanceApi
from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath, getTempPath


# DelegateStateTypeMapping
statusMapReverse = {}
statusMapReverse['NEW'] = STATUS_NOTTRADED
statusMapReverse['PARTIALLY_FILLED'] = STATUS_PARTTRADED
statusMapReverse['FILLED'] = STATUS_ALLTRADED
statusMapReverse['CANCELED'] = STATUS_CANCELLED
statusMapReverse['REJECTED'] = STATUS_REJECTED
statusMapReverse['EXPIRED'] = STATUS_CANCELLED

# DirectionMapping
directionMap = {}
directionMap[DIRECTION_LONG] = 'BUY'
directionMap[DIRECTION_SHORT] = 'SELL'
directionMapReverse = {v:k for k,v in directionMap.items()}

# PriceTypeMapping
priceTypeMap = {}
priceTypeMap[PRICETYPE_LIMITPRICE] = 'LIMIT'
priceTypeMap[PRICETYPE_MARKETPRICE] = 'MARKET'




#----------------------------------------------------------------------
def print_dict(d):
    """"""
    print('-' * 30)
    l = d.keys()
    l.sort()
    for k in l:
        print('%s:%s' %(k, d[k]))


########################################################################
class BinanceGateway(VtGateway):
    """CurrencyInterface"""

    #----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName=''):
        """Constructor"""
        super(BinanceGateway, self).__init__(eventEngine, gatewayName)

        self.api = GatewayApi(self)

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
            symbols = setting['symbols']
        except KeyError:
            log = VtLogData()
            log.gatewayName = self.gatewayName
            log.logContent = u'Connection configuration missing field, please check'
            self.onLog(log)
            return

        # CreateQuotesAndTradingInterfaceObjects
        self.api.connect(apiKey, secretKey, symbols)

        # InitializeAndStartTheQuery
        #self.initQuery()

    #----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """SubscribeToTheMarket"""
        pass

    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """Billing"""
        return self.api.sendOrder(orderReq)

    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """Withdrawal"""
        self.api.cancel(cancelOrderReq)

    #----------------------------------------------------------------------
    def close(self):
        """close"""
        self.api.close()
    
    #----------------------------------------------------------------------
    def queryAccount(self):
        """"""
        self.api.queryAccount()

    #----------------------------------------------------------------------
    def initQuery(self):
        """InitializeContinuousQuery"""
        if self.qryEnabled:
            # List of query functions that need to be looped
            self.qryFunctionList = [self.queryAccount]

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
class GatewayApi(BinanceApi):
    """API实现"""

    #----------------------------------------------------------------------
    def __init__(self, gateway):
        """Constructor"""
        super(GatewayApi, self).__init__()

        self.gateway = gateway                  # gatewayObject
        self.gatewayName = gateway.gatewayName  # gatewayObjectName
        
        self.date = datetime.now().strftime('%y%m%d%H%M%S')
        self.orderId = 0

        self.tickDict = {}

    #----------------------------------------------------------------------
    def connect(self, apiKey, secretKey, symbols):
        """ConnectToTheServer"""
        self.init(apiKey, secretKey)
        self.start()
        self.writeLog(u'TradingAPIStartedSuccessfully')
        
        l = []
        for symbol in symbols:
            symbol = symbol.lower()
            l.append(symbol+'@ticker')
            l.append(symbol+'@depth5')
        self.initDataStream(l)
        self.writeLog(u'QuotePushSubscriptionSuccess')
        
        self.startStream()
        
        # InitializeTheQuery
        self.queryExchangeInfo()
        self.queryAccount()
        
        for symbol in symbols:
            self.queryOpenOrders(symbol.upper())

    #----------------------------------------------------------------------
    def writeLog(self, content):
        """IssueLog"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.gateway.onLog(log)

    #----------------------------------------------------------------------
    def onError(self, data, reqid):
        """"""
        err = VtErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = data['code']
        err.errorMsg = data['msg']
        self.gateway.onError(err)
        
    #----------------------------------------------------------------------
    def onQueryExchangeInfo(self, data, reqid):
        """"""
        for d in data['symbols']:
            contract = VtContractData()
            contract.gatewayName = self.gatewayName
            
            contract.symbol = d['symbol']
            contract.exchange = EXCHANGE_BINANCE
            contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
            contract.name = contract.vtSymbol
            contract.productClass = PRODUCT_SPOT
            contract.size = 1
            
            for f in d['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    contract.priceTick = float(f['tickSize'])
            
            self.gateway.onContract(contract)
            
    #----------------------------------------------------------------------
    def onNewOrder(self, data, reqid):
        """"""
        pass              

    #----------------------------------------------------------------------
    def onCancelOrder(self, data, reqid):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onQueryOpenOrders(self, data, reqid):
        """"""
        for d in data:
            order = VtOrderData()
            order.gatewayName = self.gatewayName
            
            order.symbol = d['symbol']
            order.exchange = EXCHANGE_BINANCE
            order.vtSymbol = '.'.join([order.symbol, order.exchange])
            
            order.orderID = d['clientOrderId']
            order.vtOrderID = '.'.join([order.gatewayName, order.orderID])
            
            order.direction = directionMapReverse[d['side']]
            order.price = float(d['price'])
            order.totalVolume = float(d['origQty'])
            order.tradedVolume = float(d['executedQty'])
            date, order.orderTime = self.generateDateTime(d['time'])
            order.status = statusMapReverse[d['status']]
            
            self.gateway.onOrder(order)
        
    #----------------------------------------------------------------------
    def onQueryAllOrders(self, data, reqid):
        """"""
        pass         
        
    #----------------------------------------------------------------------
    def onQueryAccount(self, data, reqid):
        """"""
        for d in data['balances']:
            free = float(d['free'])
            locked = float(d['locked'])
            
            account = VtAccountData()
            account.gatewayName = self.gatewayName
            
            account.accountID = d['asset']
            account.vtAccountID = '.'.join([account.gatewayName, account.accountID])
            account.balance = free + locked
            account.available = free
            
            self.gateway.onAccount(account)
        
    #----------------------------------------------------------------------
    def onQueryMyTrades(self, data, reqid):
        """"""
        pass         
        
    #----------------------------------------------------------------------
    def onStartStream(self, data, reqid):
        """"""
        key = data['listenKey']
        self.initUserStream(key)
        self.writeLog(u'TransactionPushSubscriptionSuccess')
    
    #----------------------------------------------------------------------
    def onKeepaliveStream(self, data, reqid):
        """"""
        self.writeLog(u'TransactionPushRefreshedSuccessfully')
    
    #----------------------------------------------------------------------
    def onCloseStream(self, data, reqid):
        """"""
        self.writeLog(u'TransactionPushClose')

    #----------------------------------------------------------------------
    def onUserData(self, data):
        """"""
        if data['e'] == 'outboundAccountInfo':
            self.onPushAccount(data)
        elif data['e'] == 'executionReport':
            self.onPushOrder(data)
    
    #----------------------------------------------------------------------
    def onPushAccount(self, data):
        """"""
        for d in data['B']:
            free = float(d['f'])
            locked = float(d['l'])
            
            account = VtAccountData()
            account.gatewayName = self.gatewayName
            
            account.accountID = d['a']
            account.vtAccountID = '.'.join([account.gatewayName, account.accountID])
            account.balance = free + locked
            account.available = free
            
            self.gateway.onAccount(account)

    #----------------------------------------------------------------------
    def onPushOrder(self, d):
        """"""
        # CommissionUpdate
        order = VtOrderData()
        order.gatewayName = self.gatewayName
        
        order.symbol = d['s']
        order.exchange = EXCHANGE_BINANCE
        order.vtSymbol = '.'.join([order.symbol, order.exchange])
        
        if d['C'] != 'null':
            order.orderID = d['C']  # WithdrawalOriginalOrderNumber
        else:
            order.orderID = d['c']
        order.vtOrderID = '.'.join([order.gatewayName, order.orderID])
        
        order.direction = directionMapReverse[d['S']]
        order.price = float(d['p'])
        order.totalVolume = float(d['q'])
        order.tradedVolume = float(d['z'])
        date, order.orderTime = self.generateDateTime(d['T'])
        order.status = statusMapReverse[d['X']]      
        
        self.gateway.onOrder(order)
        
        # TransactionUpdate
        if float(d['l']):
            trade = VtTradeData()
            trade.gatewayName = self.gatewayName
            
            trade.symbol = order.symbol
            trade.exchange = order.exchange
            trade.vtSymbol = order.vtSymbol
            trade.orderID = order.orderID
            trade.vtOrderID = order.vtOrderID
            trade.tradeID = str(d['t'])
            trade.vtTradeID = '.'.join([trade.gatewayName, trade.tradeID])
            trade.direction = order.direction
            trade.price = float(d['L'])
            trade.volume = float(d['l'])
            date, trade.tradeTime = self.generateDateTime(d['E'])
            
            self.gateway.onTrade(trade)
    
    #----------------------------------------------------------------------
    def onMarketData(self, data):
        """"""
        name = data['stream']
        symbol, channel = name.split('@')
        symbol = symbol.upper()
        
        if symbol in self.tickDict:
            tick = self.tickDict[symbol]
        else:
            tick = VtTickData()
            tick.gatewayName = self.gatewayName
            tick.symbol = symbol
            tick.exchange = EXCHANGE_BINANCE
            tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            
            self.tickDict[symbol] = tick
        
        data = data['data']
        if channel == 'ticker':
            tick.volume = float(data['v'])            
            tick.openPrice = float(data['o'])
            tick.highPrice = float(data['h'])
            tick.lowPrice = float(data['l'])
            tick.lastPrice = float(data['c'])
            tick.date, tick.time = self.generateDateTime(data['E'])
        else:
            tick.askPrice1, tick.askVolume1, buf = data['asks'][0]
            tick.askPrice2, tick.askVolume2, buf = data['asks'][1]
            tick.askPrice3, tick.askVolume3, buf = data['asks'][2]
            tick.askPrice4, tick.askVolume4, buf = data['asks'][3]
            tick.askPrice5, tick.askVolume5, buf = data['asks'][4]
            
            tick.bidPrice1, tick.bidVolume1, buf = data['bids'][0]
            tick.bidPrice2, tick.bidVolume2, buf = data['bids'][1]
            tick.bidPrice3, tick.bidVolume3, buf = data['bids'][2]
            tick.bidPrice4, tick.bidVolume4, buf = data['bids'][3]
            tick.bidPrice5, tick.bidVolume5, buf = data['bids'][4]    
            
            tick.askPrice1 = float(tick.askPrice1)
            tick.askPrice2 = float(tick.askPrice2)
            tick.askPrice3 = float(tick.askPrice3)
            tick.askPrice4 = float(tick.askPrice4)
            tick.askPrice5 = float(tick.askPrice5)
            
            tick.bidPrice1 = float(tick.bidPrice1)
            tick.bidPrice2 = float(tick.bidPrice2)
            tick.bidPrice3 = float(tick.bidPrice3)
            tick.bidPrice4 = float(tick.bidPrice4)
            tick.bidPrice5 = float(tick.bidPrice5)          
            
            tick.askVolume1 = float(tick.askVolume1)
            tick.askVolume2 = float(tick.askVolume2)
            tick.askVolume3 = float(tick.askVolume3)
            tick.askVolume4 = float(tick.askVolume4)
            tick.askVolume5 = float(tick.askVolume5)
            
            tick.bidVolume1 = float(tick.bidVolume1)
            tick.bidVolume2 = float(tick.bidVolume2)
            tick.bidVolume3 = float(tick.bidVolume3)
            tick.bidVolume4 = float(tick.bidVolume4)
            tick.bidVolume5 = float(tick.bidVolume5) 
        
        self.gateway.onTick(copy(tick))
    
    #----------------------------------------------------------------------
    def onDataStreamError(self, msg):
        """"""
        self.writeLog(msg)
    
    #----------------------------------------------------------------------
    def onUserStreamError(self, msg):
        """"""
        self.writeLog(msg)
        
    #----------------------------------------------------------------------
    def generateDateTime(self, s):
        """GenerationTime"""
        dt = datetime.fromtimestamp(float(s)/1e3)
        time = dt.strftime("%H:%M:%S.%f")
        date = dt.strftime("%Y%m%d")
        return date, time    
    
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """"""
        self.orderId += 1
        orderId = self.date + str(self.orderId).rjust(6, '0')
        vtOrderID = '.'.join([self.gatewayName, orderId])
        side = directionMap.get(orderReq.direction, '')
        type_ = priceTypeMap.get(orderReq.priceType, PRICETYPE_LIMITPRICE)
        
        self.newOrder(orderReq.symbol, side, type_, orderReq.price, 
                      orderReq.volume, 'GTC', newClientOrderId=orderId)
        
        return vtOrderID
    
    #----------------------------------------------------------------------
    def cancel(self, cancelOrderReq):
        """"""
        self.cancelOrder(cancelOrderReq.symbol, origClientOrderId=cancelOrderReq.orderID)
