# encoding: UTF-8

"""
Download data to the database now for manual update operations。
"""

from dataService import *


if __name__ == '__main__':
    #downMinuteBarBySymbol('BTC/USDT.OKEX', '20181012')
    #downMinuteBarBySymbol('BTC/USDT.HUOBIPRO', '20181012')
    #downMinuteBarBySymbol('BTC/USDT.BINANCE', '20181012')
    downloadAllMinuteBar('20181012')