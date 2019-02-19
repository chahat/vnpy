# encoding: UTF-8

"""
The Demo here is one of the simplest two-average strategy implementations.
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)


########################################################################
class DoubleMaStrategy(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'DoubleMaStrategy'
    author = u'用Python的交易员'
    
    # 策略参数
    fastWindow = 10     # 快速均线参数
    slowWindow = 60     # 慢速均线参数
    initDays = 10       # 初始化数据所用的天数
    
    # 策略变量
    fastMa0 = EMPTY_FLOAT   # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT   # 上一根的快速EMA
    
    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastWindow',
                 'slowWindow']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'fastMa0',
               'fastMa1',
               'slowMa0',
               'slowMa1']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DoubleMaStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()
        
        # Note that the variable object properties (usually list and dict, etc.) in the policy class need to be recreated when the policy is initialized.
        # Otherwise, data sharing between multiple policy instances may occur, which may lead to potential policy logic error risks.
        # The variable object properties in the policy class can be selected and not written, all placed under __init__, mainly for reading
        #Strategy is convenient (more is a choice of programming habits)
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Dual EMA presentation strategy initialization')
        
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
        
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Dual EMA demo strategy launch')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Double EMA demonstration strategy stopped')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return
        
        # 计算快慢均线
        fastMa = am.sma(self.fastWindow, array=True)
        self.fastMa0 = fastMa[-1]
        self.fastMa1 = fastMa[-2]
        
        slowMa = am.sma(self.slowWindow, array=True)
        self.slowMa0 = slowMa[-1]
        self.slowMa1 = slowMa[-2]

        # 判断买卖
        crossOver = self.fastMa0>self.slowMa0 and self.fastMa1<self.slowMa1     # Wear on a gold fork
        crossBelow = self.fastMa0<self.slowMa0 and self.fastMa1>self.slowMa1    # Under the cross
        
        #金叉和死叉's condition is mutually exclusive
        # All commissions are entrusted with the K-line closing price (there is a risk that the real-time can not be traded, consider adding support for the analog market order type)
        if crossOver:
            # If there is no position at hand when the gold fork is in hand, do more directly.
            if self.pos == 0:
                self.buy(bar.close, 1)
            # If there is a short position, first empty, then do more
            elif self.pos < 0:
                self.cover(bar.close, 1)
                self.buy(bar.close, 1)
        # The dead fork and the golden fork are the opposite
        elif crossBelow:
            if self.pos == 0:
                self.short(bar.close, 1)
            elif self.pos > 0:
                self.sell(bar.close, 1)
                self.short(bar.close, 1)
                
        # 发出状态更新事件
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """ received a delegate change push (must be implemented by user inheritance) """
        # For on strategies that do not require fine-grained delegation control, you can ignore onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """ received a transaction push (must be implemented by the user) """
        # For on strategies that do not require fine-grained delegation control, you can ignore onOrder
        pass
    
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
