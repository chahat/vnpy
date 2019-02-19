# encoding: UTF-8

"""
Thanks to darwin quant for his strategic thinking.
Know the original column: https://zhuanlan.zhihu.com/p/24448511

Strategy logic:
1. Bollinger channel (signal)
2. cci indicator (filtered)
3. atr indicator (stop loss)

Suitable variety: rebar
Suitable period: 15 minutes

The strategy here is that the author implements vn.py according to the original text, and made some modifications to the strategy implementation, for reference only.

"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class BollChannelStrategy(CtaTemplate):
    """基于布林通道的交易策略"""
    className = 'BollChannelStrategy'
    author = u'用Python的交易员'

    # 策略参数
    bollWindow = 18                     # Boolean channel window number
    bollDev = 3.4                       # Deviation of the Bollinger channel
    cciWindow = 10                      # CCI窗口数
    atrWindow = 30                      # ATR窗口数
    slMultiplier = 5.2                  # Calculate the multiplier of the stop loss distance
    initDays = 10                       # 初始化数据所用的天数
    fixedSize = 1                       # 每次交易的数量

    # 策略变量
    bollUp = 0                          # 布林通道上轨
    bollDown = 0                        # 布林通道下轨
    cciValue = 0                        # CCI指标数值
    atrValue = 0                        # ATR指标数值
    
    intraTradeHigh = 0                  # 持仓期内的最高点
    intraTradeLow = 0                   # 持仓期内的最低点
    longStop = 0                        # 多头止损
    shortStop = 0                       # 空头止损

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'bollWindow',
                 'bollDev',
                 'cciWindow',
                 'atrWindow',
                 'slMultiplier',
                 'initDays',
                 'fixedSize']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'bollUp',
               'bollDown',
               'cciValue',
               'atrValue',
               'intraTradeHigh',
               'intraTradeLow',
               'longStop',
               'shortStop']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(BollChannelStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 15, self.onXminBar)        # 创建K线合成器对象
        self.am = ArrayManager()
            
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s policy initialization' %self.name)
        
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s policy started' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s policy stopped' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）""" 
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def onXminBar(self, bar):
        """ReceivedXMinutesKLine"""
        # CommissionIssuedBeforeFullWithdrawal
        self.cancelAll()
    
        # SaveKLineData
        am = self.am
        
        am.updateBar(bar)
        
        if not am.inited:
            return
        
        # CalculateTheIndicatorValue
        self.bollUp, self.bollDown = am.boll(self.bollWindow, self.bollDev)
        self.cciValue = am.cci(self.cciWindow)
        self.atrValue = am.atr(self.atrWindow)
        
        # DetermineIfYouWantToTrade
    
        # Currently no position, send open position commission
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            
            
            if self.cciValue > 0:
                self.buy(self.bollUp, self.fixedSize, True)
                
            elif self.cciValue < 0:
                self.short(self.bollDown, self.fixedSize, True)
    
        # 持有多头仓位
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            self.longStop = self.intraTradeHigh - self.atrValue * self.slMultiplier
            
            self.sell(self.longStop, abs(self.pos), True)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            self.shortStop = self.intraTradeLow + self.atrValue * self.slMultiplier
            
            self.cover(self.shortStop, abs(self.pos), True)
            
        # 同步数据到数据库
        self.saveSyncData()        
    
        # 发出状态更新事件
        self.putEvent()        

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """成交推送"""
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
    
