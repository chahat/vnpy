# encoding: UTF-8

"""
Download the data to the database immediately for manual update operations.
"""

from dataService import *


if __name__ == '__main__':
    downMinuteBarBySymbol('BINANCE_SPOT_BTC_USDT', '1MIN', '20170725', '20180726')