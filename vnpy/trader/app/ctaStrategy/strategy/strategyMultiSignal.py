# encoding: UTF-8

"""
一个多信号组合策略，基于的信号包括：
RSI（1分钟）：大于70为多头、低于30为空头
CCI（1分钟）：大于10为多头、低于-10为空头
MA（5分钟）：快速大于慢速为多头、低于慢速为空头
"""

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (TargetPosTemplate, 
                                                     CtaSignal,
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class RsiSignal(CtaSignal):
    """RSI信号"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(RsiSignal, self).__init__()
        
        self.rsiWindow = 14
        self.rsiLevel = 20
        self.rsiLong = 50 + self.rsiLevel
        self.rsiShort = 50 - self.rsiLevel
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""
        self.am.updateBar(bar)
        
        if not self.am.inited:
            self.setSignalPos(0)
            
        rsiValue = self.am.rsi(self.rsiWindow)
        
        if rsiValue >= self.rsiLong:
            self.setSignalPos(1)
        elif rsiValue <= self.rsiShort:
            self.setSignalPos(-1)
        else:
            self.setSignalPos(0)


########################################################################
class CciSignal(CtaSignal):
    """CCI信号"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(CciSignal, self).__init__()
        
        self.cciWindow = 30
        self.cciLevel = 10
        self.cciLong = self.cciLevel
        self.cciShort = -self.cciLevel
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()        
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""
        self.am.updateBar(bar)
        
        if not self.am.inited:
            self.setSignalPos(0)
            
        cciValue = self.am.cci(self.cciWindow)
        
        if cciValue >= self.cciLong:
            self.setSignalPos(1)
        elif cciValue<= self.cciShort:
            self.setSignalPos(-1)    
        else:
            self.setSignalPos(0)
    

########################################################################
class MaSignal(CtaSignal):
    """双均线信号"""
    
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(MaSignal, self).__init__()
        
        self.fastWindow = 5
        self.slowWindow = 20
        
        self.bg = BarGenerator(self.onBar, 5, self.onFiveBar)
        self.am = ArrayManager()        
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """K线更新"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def onFiveBar(self, bar):
        """5分钟K线更新"""
        self.am.updateBar(bar)
        
        if not self.am.inited:
            self.setSignalPos(0)
            
        fastMa = self.am.sma(self.fastWindow)
        slowMa = self.am.sma(self.slowWindow)
        
        if fastMa > slowMa:
            self.setSignalPos(1)
        elif fastMa < slowMa:
            self.setSignalPos(-1)
        else:
            self.setSignalPos(0)
    

########################################################################
class MultiSignalStrategy(TargetPosTemplate):
    """CrossTimeTradingStrategy"""
    className = 'MultiSignalStrategy'
    author = u'TraderWithPython'

    # PolicyParameter
    initDays = 10           # TheNumberOfDaysToInitializeTheData
    fixedSize = 1           # NumberOfTransactionsPerTransaction

    # StrategyVariable
    signalPos = {}          # SignalPosition
    
    # ListOfParametersSaveTheNameOfTheParameter
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']    

    # List of variables, the name of the variable is saved
    varList = ['inited',
               'trading',
               'pos',
               'signalPos',
               'targetPos']

    # Synchronize the list and save the name of the variable that needs to be saved to the database
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(MultiSignalStrategy, self).__init__(ctaEngine, setting)

        self.rsiSignal = RsiSignal()
        self.cciSignal = CciSignal()
        self.maSignal = MaSignal()
        
        self.signalPos = {
            "rsi": 0,
            "cci": 0,
            "ma": 0
        }
        
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
        super(MultiSignalStrategy, self).onTick(tick)
        
        self.rsiSignal.onTick(tick)
        self.cciSignal.onTick(tick)
        self.maSignal.onTick(tick)
        
        self.calculateTargetPos()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """Received a Bar push (must be implemented by the user)"""
        super(MultiSignalStrategy, self).onBar(bar)
        
        self.rsiSignal.onBar(bar)
        self.cciSignal.onBar(bar)
        self.maSignal.onBar(bar)
        
        self.calculateTargetPos()
        
    #----------------------------------------------------------------------
    def calculateTargetPos(self):
        """CalculateTheTargetPosition"""
        self.signalPos['rsi'] = self.rsiSignal.getSignalPos()
        self.signalPos['cci'] = self.cciSignal.getSignalPos()
        self.signalPos['ma'] = self.maSignal.getSignalPos()
        
        targetPos = 0
        for v in self.signalPos.values():
            targetPos += v
            
        self.setTargetPos(targetPos)
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """Received a delegate change push (must be implemented by the user)"""
        super(MultiSignalStrategy, self).onOrder(order)

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # IssueAStatusUpdateEvent
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """StopSinglePush"""
        pass