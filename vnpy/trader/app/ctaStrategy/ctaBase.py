# encoding: UTF-8

'''
This file contains some basic settings, classes, and constants used in the CTA module.
'''

# CTA Data class definitions involved in the engine
from vnpy.trader.vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT

# ConstantDefinition
# CTAType of transaction direction involved in the engine
CTAORDER_BUY = u'buy_open'
CTAORDER_SELL = u'sell_​​flat'
CTAORDER_SHORT = u'sell_​​open'
CTAORDER_COVER = u'buy_flat'

# LocalStopSingleState
STOPORDER_WAITING = u'Waiting'
STOPORDER_CANCELLED = u'CANCELLED'
STOPORDER_TRIGGERED = u'TRIGGERED'

# Local stop single prefix
STOPORDERPREFIX = 'CtaStopOrder.'

# NameDatabase
SETTING_DB_NAME = 'VnTrader_Setting_Db'
POSITION_DB_NAME = 'VnTrader_Position_Db'

TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'

# Engine type, used to distinguish the running environment of the current policy
ENGINETYPE_BACKTESTING = 'backtesting'  # BackTest
ENGINETYPE_TRADING = 'trading'          # SolidDisk

# CTAModuleEvent
EVENT_CTA_LOG = 'eCtaLog'               # CTA RelatedLogEvents
EVENT_CTA_STRATEGY = 'eCtaStrategy.'    # CTA PolicyStateChangeEvent


########################################################################
class StopOrder(object):
    """LocalStopOrder"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING
        self.orderType = EMPTY_UNICODE
        self.direction = EMPTY_UNICODE
        self.offset = EMPTY_UNICODE
        self.price = EMPTY_FLOAT
        self.volume = EMPTY_INT
        
        self.strategy = None             # PolicyObjectForTheNextStopOrder
        self.stopOrderID = EMPTY_STRING  # StopTheLocalNumberOfTheOrder
        self.status = EMPTY_STRING       # StopSingleState