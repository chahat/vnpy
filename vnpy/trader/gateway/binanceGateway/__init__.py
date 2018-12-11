# encoding: UTF-8

from vnpy.trader import vtConstant
from .binanceGateway import BinanceGateway

gatewayClass = BinanceGateway
gatewayName = 'BINANCE'
gatewayDisplayName = 'BINANCE'
gatewayType = vtConstant.GATEWAYTYPE_BTC
gatewayQryEnabled = True