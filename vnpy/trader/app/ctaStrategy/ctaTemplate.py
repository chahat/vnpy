# encoding: UTF-8

'''
This file contains the template for policy development in the CTA engine. You need to inherit the CtaTemplate class when developing the strategy.
'''

from vnpy.trader.vtConstant import *
from vnpy.trader.vtUtility import BarGenerator, ArrayManager

from .ctaBase import *


########################################################################
class CtaTemplate(object):
    """CTAPolicyTemplate"""
    
    # TheNameAndAuthorOfTheStrategyClass
    className = 'CtaTemplate'
    author = EMPTY_UNICODE
    
    # MongoDB The name of the database, the K-line database defaults to 1 minute.
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME
    
    # basicParametersOfTheStrategy
    name = EMPTY_UNICODE           # PolicyInstanceName
    vtSymbol = EMPTY_STRING        # ContractVtSystemCodeForTrading
    productClass = EMPTY_STRING    # ProductTypeOnlyRequiredForIBInterface
    currency = EMPTY_STRING        # CurrencyOnlyRequiredForIBInterface
    
    # The basic variables of the strategy, managed by the engine
    inited = False                 # WhetherItWasInitialized
    trading = False                # Whether to initiate a transaction, managed by the engine
    pos = 0                        # Position
    
    # ListOfParametersSaveTheNameOfTheParameter
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']
    
    # List of variables, the name of the variable is saved
    varList = ['inited',
               'trading',
               'pos']
    
    # Synchronize the list and save the name of the variable that needs to be saved to the database
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine

        # SetTheParametersOfThePolicy
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
    
    #----------------------------------------------------------------------
    def onInit(self):
        """Initialization strategy (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStart(self):
        """Startup policy (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStop(self):
        """Stop policy (must be implemented by user inheritance)"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Received market TICK push (must be implemented by user inheritance)"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """Received a delegate change push (must be implemented by the user)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """Received a transaction push (must be implemented by the user)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """Received a Bar push (must be implemented by the user)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """Received a stop push (must be inherited by the user)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def buy(self, price, volume, stop=False):
        """BuyOpen"""
        return self.sendOrder(CTAORDER_BUY, price, volume, stop)
    
    #----------------------------------------------------------------------
    def sell(self, price, volume, stop=False):
        """Sell​​Flat"""
        return self.sendOrder(CTAORDER_SELL, price, volume, stop)       

    #----------------------------------------------------------------------
    def short(self, price, volume, stop=False):
        """Sell​​Open"""
        return self.sendOrder(CTAORDER_SHORT, price, volume, stop)          
 
    #----------------------------------------------------------------------
    def cover(self, price, volume, stop=False):
        """BuyFlat"""
        return self.sendOrder(CTAORDER_COVER, price, volume, stop)
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, stop=False):
        """SendCommission"""
        if self.trading:
            # If stop is True, it means sending a local stop order.
            if stop:
                vtOrderIDList = self.ctaEngine.sendStopOrder(self.vtSymbol, orderType, price, volume, self)
            else:
                vtOrderIDList = self.ctaEngine.sendOrder(self.vtSymbol, orderType, price, volume, self) 
            return vtOrderIDList
        else:
            # Billing returns an empty string when the transaction stops
            return []
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """Withdrawal"""
        # If the billing number is an empty string, no further operations are performed.
        if not vtOrderID:
            return
        
        if STOPORDERPREFIX in vtOrderID:
            self.ctaEngine.cancelStopOrder(vtOrderID)
        else:
            self.ctaEngine.cancelOrder(vtOrderID)
            
    #----------------------------------------------------------------------
    def cancelAll(self):
        """AllWithdrawals"""
        self.ctaEngine.cancelAll(self.name)
    
    #----------------------------------------------------------------------
    def insertTick(self, tick):
        """InsertTickDataIntoTheDatabase"""
        self.ctaEngine.insertData(self.tickDbName, self.vtSymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, bar):
        """InsertBarDataIntoTheDatabase"""
        self.ctaEngine.insertData(self.barDbName, self.vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """ReadTickData"""
        return self.ctaEngine.loadTick(self.tickDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days):
        """ReadBarData"""
        return self.ctaEngine.loadBar(self.barDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """RecordCTALogs"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """IssueAPolicyStateChangeEvent"""
        self.ctaEngine.putStrategyEvent(self.name)
        
    #----------------------------------------------------------------------
    def getEngineType(self):
        """QueryTheCurrentlyRunningEnvironment"""
        return self.ctaEngine.engineType
    
    #----------------------------------------------------------------------
    def saveSyncData(self):
        """SaveSynchronizedDataToTheDatabase"""
        if self.trading:
            self.ctaEngine.saveSyncData(self)
    
    #----------------------------------------------------------------------
    def getPriceTick(self):
        """QueryMinimumPriceChanges"""
        return self.ctaEngine.getPriceTick(self)
        

########################################################################
class TargetPosTemplate(CtaTemplate):
    """
    A policy template that allows transactions to be implemented directly by modifying the target position

    When developing a strategy, there is no need to call the specific delegate commands such as buy/sell/cover/short.
    Just call setTargetPos to set the target position after the strategy logic runs, the underlying algorithm
    Will automatically complete the relevant transactions, suitable for users who are not good at managing the details of the transaction withdrawal order.

    When developing a strategy using this template, first call the parent class's methods in the following callback methods:
    onTick
    onBar
    onOrder
    
    Assuming the policy is called TestStrategy, add the onTick callback:
    Super(TestStrategy, self).onTick(tick)

    Other methods are similar.
    """
    
    className = 'TargetPosTemplate'
    author = u'QuantitativeInvestment'
    
    # BasicVariablesOfTheTargetPositionTemplate
    tickAdd = 1             # Overpriced relative to the benchmark price at the time of entrustment
    lastTick = None         # LatestTickData
    lastBar = None          # LatestBarData
    targetPos = EMPTY_INT   # TargetPosition
    orderList = []          # ListOfCommissionNumbers

    # List of variables, the name of the variable is saved
    varList = ['inited',
               'trading',
               'pos',
               'targetPos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(TargetPosTemplate, self).__init__(ctaEngine, setting)
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """ReceivedMarketPush"""
        self.lastTick = tick
        
        # In the real mode, after starting the transaction, you need to perform the automatic opening and closing operation according to the real-time push of the tick.
        if self.trading:
            self.trade()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """ReceivedKLinePush"""
        self.lastBar = bar
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """ReceivedACommissionPush"""
        if order.status == STATUS_ALLTRADED or order.status == STATUS_CANCELLED:
            if order.vtOrderID in self.orderList:
                self.orderList.remove(order.vtOrderID)
    
    #----------------------------------------------------------------------
    def setTargetPos(self, targetPos):
        """SetTargetPosition"""
        self.targetPos = targetPos
        
        self.trade()
        
    #----------------------------------------------------------------------
    def trade(self):
        """ExecuteTransaction"""
        # FirstCancelThePreviousDelegate
        self.cancelAll()
        
        # If the target position is the same as the actual position, no action is taken
        posChange = self.targetPos - self.pos
        if not posChange:
            return
        
        # Determine the base price of the commission, use it when there is tick data, otherwise use bar
        longPrice = 0
        shortPrice = 0
        
        if self.lastTick:
            if posChange > 0:
                longPrice = self.lastTick.askPrice1 + self.tickAdd
                if self.lastTick.upperLimit:
                    longPrice = min(longPrice, self.lastTick.upperLimit)         # UpLimitPriceCheck
            else:
                shortPrice = self.lastTick.bidPrice1 - self.tickAdd
                if self.lastTick.lowerLimit:
                    shortPrice = max(shortPrice, self.lastTick.lowerLimit)       # StopPriceCheck
        else:
            if posChange > 0:
                longPrice = self.lastBar.close + self.tickAdd
            else:
                shortPrice = self.lastBar.close - self.tickAdd
        
        # In the backtest mode, the method of merged and reversed open positions is adopted.
        if self.getEngineType() == ENGINETYPE_BACKTESTING:
            if posChange > 0:
                l = self.buy(longPrice, abs(posChange))
            else:
                l = self.short(shortPrice, abs(posChange))
            self.orderList.extend(l)
        
        # In the real mode, first make sure that the previous delegates have ended (full, undo)
        # Then first issue the closing order, wait for the transaction, and then send a new opening order
        else:
            # theCommissionHasBeenCompletedBeforeTheCheck
            if self.orderList:
                return
            
            # Buy
            if posChange > 0:
                # IfThereIsCurrentlyAShortPosition
                if self.pos < 0:
                    # If the purchase volume is less than the short position, the direct purchase amount is
                    if posChange < abs(self.pos):
                        l = self.cover(longPrice, posChange)
                    # Otherwise, all the short positions will be flattened first.
                    else:
                        l = self.cover(longPrice, abs(self.pos))
                # If there is no short position, perform the opening operation
                else:
                    l = self.buy(longPrice, abs(posChange))
            # SellingTheOpposite
            else:
                if self.pos > 0:
                    if abs(posChange) < self.pos:
                        l = self.sell(shortPrice, abs(posChange))
                    else:
                        l = self.sell(shortPrice, abs(self.pos))
                else:
                    l = self.short(shortPrice, abs(posChange))
            self.orderList.extend(l)
    

########################################################################
class CtaSignal(object):
    """
    CTA Strategy signal, responsible for pure signal generation (target position), not involved in specific transaction management
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.signalPos = 0      # SignalPosition
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """KLinePush"""
        pass
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick Push"""
        pass
        
    #----------------------------------------------------------------------
    def setSignalPos(self, pos):
        """SetSignalPosition"""
        self.signalPos = pos
        
    #----------------------------------------------------------------------
    def getSignalPos(self):
        """GetSignalPosition"""
        return self.signalPos
