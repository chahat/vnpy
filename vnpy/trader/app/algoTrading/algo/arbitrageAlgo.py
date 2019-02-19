# encoding: UTF-8

from __future__ import division
from collections import OrderedDict

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    STATUS_ALLTRADED, STATUS_CANCELLED,
                                    STATUS_REJECTED)

from vnpy.trader.uiQt import QtGui

from vnpy.trader.app.algoTrading.algoTemplate import AlgoTemplate
from vnpy.trader.app.algoTrading.uiAlgoWidget import AlgoWidget, QtWidgets


STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])


########################################################################
class ArbitrageAlgo(AlgoTemplate):
    """Arbitrage algorithm for arbitrage"""
    
    templateName = 'Arbitrage'

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(ArbitrageAlgo, self).__init__(engine, setting, algoName)
        
        # 配置参数
        self.activeVtSymbol = str(setting['activeVtSymbol'])    # 主动腿
        self.passiveVtSymbol = str(setting['passiveVtSymbol'])  # 被动腿
        
        self.spread = float(setting['spread'])    # 价差
        self.volume = float(setting['volume'])    # 数量
        self.interval = int(setting['interval'])  # 间隔
        
        self.activeOrderID = ''            # 主动委托号
        self.passiveOrderID = ''           # 被动委托号
        
        self.netPos = 0                    # 净持仓
        self.count = 0                     # 运行计数

        # 初始化
        self.subscribe(self.activeVtSymbol)
        self.subscribe(self.passiveVtSymbol)
        
        self.paramEvent()
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        # 更新净持仓数量
        if trade.direction == DIRECTION_LONG:
            self.netPos += trade.volume
        else:
            self.netPos -= trade.volume
            
        # 如果是主动腿成交则需要执行对冲
        if trade.vtSymbol == self.activeVtSymbol:
            self.hedge()

        self.varEvent()
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""
        if order.vtSymbol == self.activeVtSymbol:
            if order.status in STATUS_FINISHED:
                self.activeOrderID = ''
        elif order.vtSymbol == self.passiveVtSymbol:
            if order.status in STATUS_FINISHED:
                self.passiveOrderID = ''
        
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTimer(self):
        """"""
        self.count += 1
        if self.count < self.interval:
            return
        
        self.count = 0
        
        # 撤单
        if self.activeOrderID or self.passiveOrderID:
            self.cancelAll()
            return
        
        # 如果有净仓位则执行对冲
        if self.netPos:
            self.hedge()
            return
        
        # 计算价差的bid/ask
        activeTick = self.getTick(self.activeVtSymbol)
        passiveTick = self.getTick(self.passiveVtSymbol)
        
        spreadBidPrice = activeTick.bidPrice1 - passiveTick.askPrice1
        spreadAskPrice = activeTick.askPrice1 - passiveTick.bidPrice1
        
        spreadBidVolume = min(activeTick.bidVolume1, passiveTick.askVolume1)
        spreadAskVolume = min(activeTick.askVolume1, passiveTick.bidVolume1)
        
        if spreadBidPrice > self.spread:
            self.activeOrderID = self.sell(self.activeVtSymbol, activeTick.bidPrice1, spreadBidVolume)
        elif spreadAskPrice < - self.spread:
            self.activeOrderID = self.buy(self.activeVtSymbol, activeTick.askPrice1, spreadAskVolume)
        
        # 更新界面
        self.varEvent()
        
    #----------------------------------------------------------------------
    def onStop(self):
        """"""
        self.writeLog(u'Algorithm stop')
        
        self.varEvent()
        
    #----------------------------------------------------------------------
    def varEvent(self):
        """更新变量"""
        d = OrderedDict()
        d['active'] = self.active
        d['count'] = self.count
        d['netPos'] = self.netPos
        d['activeOrderId'] = self.activeOrderID
        d['passiveOrderId'] = self.passiveOrderID
        self.putVarEvent(d)
    
    #----------------------------------------------------------------------
    def paramEvent(self):
        """更新参数"""
        d = OrderedDict()
        d['activeVtSymbol'] = self.activeVtSymbol
        d['passiveVtSymbol'] = self.passiveVtSymbol
        d['spread'] = self.spread
        d['volume'] = self.volume
        d['interval'] = self.interval
        self.putParamEvent(d)

    #----------------------------------------------------------------------
    def hedge(self):
        """"""
        tick = self.getTick(self.passiveVtSymbol)
        volume = abs(self.netPos)
        
        if self.netPos > 0:
            self.passiveOrderID = self.sell(self.passiveVtSymbol,
                                            tick.bidPrice5,
                                            volume)
        elif self.netPos < 0:
            self.passiveOrderID = self.buy(self.passiveVtSymbol,
                                           tick.askPrice5,
                                           volume)



########################################################################
class ArbitrageWidget(AlgoWidget):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(ArbitrageWidget, self).__init__(algoEngine, parent)
        
        self.templateName = ArbitrageAlgo.templateName
        
    #----------------------------------------------------------------------
    def initAlgoLayout(self):
        """"""
        self.lineActiveVtSymbol = QtWidgets.QLineEdit()
        self.linePassiveVtSymbol = QtWidgets.QLineEdit()
        
        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)
        
        self.lineSpread = QtWidgets.QLineEdit()
        self.lineSpread.setValidator(validator)
        
        self.lineVolume = QtWidgets.QLineEdit()
        self.lineVolume.setValidator(validator)
        
        intValidator = QtGui.QIntValidator()
        intValidator.setBottom(10)
        self.lineInterval = QtWidgets.QLineEdit()
        self.lineInterval.setValidator(intValidator)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label('activeVtSymbol'), 0, 0)
        grid.addWidget(self.lineActiveVtSymbol, 0, 1)
        grid.addWidget(Label('passiveVtSymbol'), 1, 0)
        grid.addWidget(self.linePassiveVtSymbol, 1, 1)
        grid.addWidget(Label('spread'), 2, 0)
        grid.addWidget(self.lineSpread, 2, 1)
        grid.addWidget(Label('volume'), 3, 0)
        grid.addWidget(self.lineVolume, 3, 1)
        grid.addWidget(Label('interval'), 4, 0)
        grid.addWidget(self.lineInterval, 4, 1)
        
        return grid
    
    #----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = self.templateName
        setting['activeVtSymbol'] = str(self.lineActiveVtSymbol.text())
        setting['passiveVtSymbol'] = str(self.linePassiveVtSymbol.text())
        setting['spread'] = float(self.lineSpread.text())
        setting['volume'] = float(self.lineVolume.text())
        setting['interval'] = int(self.lineInterval.text())
        
        return setting
    
