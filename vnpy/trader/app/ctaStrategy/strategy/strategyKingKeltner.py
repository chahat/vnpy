# encoding: UTF-8

"""
Trading strategy based on King Keltner channel, suitable for use on stock indexes,
Demonstrates the OCO delegation and the 5-minute K-line aggregation method.

Note: The author does not guarantee any profit on the transaction, the strategy code is for reference only.
"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class KkStrategy(CtaTemplate):
    """TradingStrategyBasedOnKingKeltnerChannel"""
    className = 'KkStrategy'
    author = u'Use Python Trader'

    # PolicyParameter
    kkLength = 11           # CalculateTheNumberOfWindowsInTheChannel
    kkDev = 1.6             # CalculateTheDeviationOfTheChannelWidth
    trailingPrcnt = 0.8     # TrailingStop
    initDays = 10           # TheNumberOfDaysToInitializeTheData
    fixedSize = 1           # NumberOfTransactionsPerTransaction

    # StrategyVariable
    kkUp = 0                            # KKChannelUpperRail
    kkDown = 0                          # KKChannelLowerRail
    intraTradeHigh = 0                  # TheHighestPointInTheHoldingPeriod
    intraTradeLow = 0                   # TheLowestPointInTheHoldingPeriod

    buyOrderIDList = []                 # OCO commissioned to buy the opening number of the warehouse
    shortOrderIDList = []               # OCO commissioned to sell the order number of the open position
    orderList = []                      # SaveTheListOfDelegateCodes

    # ListOfParametersSaveTheNameOfTheParameter
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'kkLength',
                 'kkDev']    

    # List of variables, the name of the variable is saved
    varList = ['inited',
               'trading',
               'pos',
               'kkUp',
               'kkDown']
    
    # Synchronize the list and save the name of the variable that needs to be saved to the database
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(KkStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 5, self.onFiveBar)     # CreateAKLineSynthesizerObject
        self.am = ArrayManager()
        
        self.buyOrderIDList = []
        self.shortOrderIDList = []
        self.orderList = []
        
    #----------------------------------------------------------------------
    def onInit(self):
        """Initialization strategy (must be implemented by user inheritance)"""
        self.writeCtaLog(u'%s PolicyInitialization' %self.name)
        
        # Load historical data and initialize strategy values ​​using playback calculations
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """Startup policy (must be implemented by user inheritance)"""
        self.writeCtaLog(u'%s PolicyStartup' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """Stop policy (must be implemented by user inheritance)"""
        self.writeCtaLog(u'%s StrategyStop' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Received market TICK push (must be implemented by user inheritance)"""
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """Received a Bar push (must be implemented by the user)"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def onFiveBar(self, bar):
        """ received 5 minutes K line """
        # Cancel the previously unsigned orders (including limit orders and stop orders)
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []
    
        # SaveKLineData
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return
        
        # CalculateTheIndicatorValue
        self.kkUp, self.kkDown = am.keltner(self.kkLength, self.kkDev)
        
        # DetermineIfYouWantToTrade
    
        # Currently no position, send OCO open position commission
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            
            self.sendOcoOrder(self.kkUp, self.kkDown, self.fixedSize)
    
        # HoldALongPosition
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            
            l = self.sell(self.intraTradeHigh*(1-self.trailingPrcnt/100), 
                          abs(self.pos), True)
            self.orderList.extend(l)
    
        # HoldingAShortPosition
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            
            l = self.cover(self.intraTradeLow*(1+self.trailingPrcnt/100), 
                           abs(self.pos), True)
            self.orderList.extend(l)
    
        # SynchronizeDataToTheDatabase
        self.saveSyncData()    
    
        # IssueAStatusUpdateEvent
        self.putEvent()        

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        if self.pos != 0:
            # After the long position is closed, the short commission is cancelled.
            if self.pos > 0:
                for shortOrderID in self.shortOrderIDList:
                    self.cancelOrder(shortOrderID)
            # The Opposite
            elif self.pos < 0:
                for buyOrderID in self.buyOrderIDList:
                    self.cancelOrder(buyOrderID)
            
            # RemoveTheCommissionNumber
            for orderID in (self.buyOrderIDList + self.shortOrderIDList):
                if orderID in self.orderList:
                    self.orderList.remove(orderID)
                
        # IssueAStatusUpdateEvent
        self.putEvent()
        
    #----------------------------------------------------------------------
    def sendOcoOrder(self, buyPrice, shortPrice, volume):
        """
        SendOCOCommission
        
        OCO (One Cancel Other) commissioned:
        1. Mainly used to achieve interval breakthrough admission
        2. Contains two stop orders in opposite directions
        3. The stop order in one direction will immediately cancel the other direction.
        """
        # Send a bilateral stop order delegate and record the commission number
        self.buyOrderIDList = self.buy(buyPrice, volume, True)
        self.shortOrderIDList = self.short(shortPrice, volume, True)
        
        # Record the delegate number in the list
        self.orderList.extend(self.buyOrderIDList)
        self.orderList.extend(self.shortOrderIDList)

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """StopSinglePush"""
        pass