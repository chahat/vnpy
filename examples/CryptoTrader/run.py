# encoding: UTF-8

# Overload sys module, set the default string encoding mode to utf8
try:
    reload         # Python 2
except NameError:  # Python 3
    from importlib import reload
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# vn.trader Module
from vnpy.event import EventEngine
from vnpy.trader.vtEngine import MainEngine
from vnpy.trader.uiQt import createQApp

# Load the underlying interface
from vnpy.trader.gateway import (huobiGateway, okexGateway, okexfGateway,
                                 binanceGateway, bitfinexGateway,
                                 bitmexGateway, fcoinGateway,
                                 bigoneGateway, lbankGateway,
                                 coinbaseGateway, ccxtGateway)

# Load the upper application
from vnpy.trader.app import (algoTrading)

# Current directory component
from uiCryptoWindow import MainWindow

#----------------------------------------------------------------------
def main():
    """Main program entry"""
    # Create a Qt application object
    qApp = createQApp()

    # Create an event engine
    ee = EventEngine()

    # Create a main engine
    me = MainEngine(ee)

    # Add transaction interface
    me.addGateway(okexfGateway)
    me.addGateway(ccxtGateway)
    me.addGateway(coinbaseGateway)
    me.addGateway(lbankGateway)
    me.addGateway(bigoneGateway)
    me.addGateway(fcoinGateway)
    me.addGateway(bitmexGateway)
    me.addGateway(huobiGateway)
    me.addGateway(okexGateway)
    me.addGateway(binanceGateway)
    me.addGateway(bitfinexGateway)
    
    # Add upper application
    me.addApp(algoTrading)
    
    # Create main window
    mw = MainWindow(me, ee)
    mw.showMaximized()

    # Start the Qt event loop in the main thread
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
