# encoding: UTF-8

import json
import csv
import os
import platform
from collections import OrderedDict

from six import text_type

from vnpy.event import *
from vnpy.trader import vtText
from vnpy.trader.vtEvent import *
from vnpy.trader.vtConstant import *
from vnpy.trader.vtFunction import *
from vnpy.trader.vtGateway import *
from vnpy.trader.uiQt import QtGui, QtWidgets, QtCore, BASIC_FONT


COLOR_RED = QtGui.QColor('red')
COLOR_GREEN = QtGui.QColor('green')


########################################################################
class BasicCell(QtWidgets.QTableWidgetItem):
    """BasicCell"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BasicCell, self).__init__()
        self.data = None
        
        self.setTextAlignment(QtCore.Qt.AlignCenter)
        
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        if text == '0' or text == '0.0':
            self.setText('')
        else:
            self.setText(text)


########################################################################
class NumCell(BasicCell):
    """TheCellUsedToDisplayTheNumber"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NumCell, self).__init__(text)
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        # Considering that NumCell is mainly used to display integer fields such as OrderID and TradeID,
        # The data conversion method here uses the int type. But due to the commission of part of the trading interface
        # The number and the transaction number may not be in the form of a pure number, so a supplement is added. try...except
        try:
            num = int(text)
            self.setData(QtCore.Qt.DisplayRole, num)
        except ValueError:
            self.setText(text)
            

########################################################################
class DirectionCell(BasicCell):
    """The cell used to display the direction of purchase and sale"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(DirectionCell, self).__init__(text)
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        if text == DIRECTION_LONG or text == DIRECTION_NET:
            self.setForeground(QtGui.QColor('red'))
        elif text == DIRECTION_SHORT:
            self.setForeground(QtGui.QColor('green'))
        self.setText(text)


########################################################################
class NameCell(BasicCell):
    """TheCellUsedToDisplayTheContractChinese"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NameCell, self).__init__()
        
        self.mainEngine = mainEngine
        self.data = None
        
        if text:
            self.setContent(text)
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        if self.mainEngine:
            # FirstTryToGetTheContractObjectNormally
            contract = self.mainEngine.getContract(text)
            
            # IfYouCanReadTheContractInformation
            if contract:
                self.setText(contract.name)


########################################################################
class BidCell(BasicCell):
    """BidPriceCell"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BidCell, self).__init__(text)
        
        self.setForeground(QtGui.QColor('black'))
        self.setBackground(QtGui.QColor(255,174,201))
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        self.setText(text)


########################################################################
class AskCell(BasicCell):
    """SellingPriceCell"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(AskCell, self).__init__(text)
        
        self.setForeground(QtGui.QColor('black'))
        self.setBackground(QtGui.QColor(160,255,160))
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        self.setText(text)


########################################################################
class PnlCell(BasicCell):
    """CellShowingProfitAndLoss"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(PnlCell, self).__init__()
        self.data = None
        self.color = ''
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """SettingContent"""
        self.setText(text)

        try:
            value = float(text)
            if value >= 0 and self.color != 'red':
                self.color = 'red'
                self.setForeground(COLOR_RED)
            elif value < 0 and self.color != 'green':
                self.color = 'green'
                self.setForeground(COLOR_GREEN)
        except ValueError:
            pass


########################################################################
class BasicMonitor(QtWidgets.QTableWidget):
    """
    BasicMonitoring
    
    headerDictThe dictionary format corresponding to the value in the following is as follows
    {'chinese': u'ChineseName', 'cellType': BasicCell}
    
    """
    signal = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicMonitor, self).__init__(parent)
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # SaveTheHeaderTag
        self.headerDict = OrderedDict()  # Ordered dictionary, key is the English name, value is the corresponding configuration dictionary
        self.headerList = []             # CorrespondingToSelfHeaderDictKeys
        
        # SaveRelevantData
        self.dataDict = {}  # Dictionary, key is the data corresponding to the field, and value is the dictionary that holds the relevant cell.
        self.dataKey = ''   # The data field corresponding to the dictionary key
        
        # MonitoredEventType
        self.eventType = ''
        
        # Column width adjustment state (just adjust column width once when data is first updated)
        self.columnResized = False
        
        # Font
        self.font = None
        
        # SaveDataObjectToCell
        self.saveData = False
        
        # By default, sorting based on the header is not allowed, and the required components can be turned on.
        self.sorting = False
        
        # DefaultHeaderCanBeAdjusted
        self.resizeMode = QtWidgets.QHeaderView.Interactive
        
        # InitializeTheContextMenu
        self.initMenu()
        
    #----------------------------------------------------------------------
    def setHeaderDict(self, headerDict):
        """SetTheHeaderOrderedDictionary"""
        self.headerDict = headerDict
        self.headerList = headerDict.keys()
        
    #----------------------------------------------------------------------
    def setDataKey(self, dataKey):
        """SetTheKeyOfTheDataDictionary"""
        self.dataKey = dataKey
        
    #----------------------------------------------------------------------
    def setEventType(self, eventType):
        """SetTheTypeOfEventBeingMonitored"""
        self.eventType = eventType
        
    #----------------------------------------------------------------------
    def setFont(self, font):
        """SetFont"""
        self.font = font
    
    #----------------------------------------------------------------------
    def setSaveData(self, saveData):
        """SetWhetherYouWantToSaveDataToTheCell"""
        self.saveData = saveData
        
    #----------------------------------------------------------------------
    def initTable(self):
        """InitializationForm"""
        # SetTheNumberOfColumnsInTheTable
        col = len(self.headerDict)
        self.setColumnCount(col)
        
        # SetListHeader
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.setHorizontalHeaderLabels(labels)
        
        # CloseTheVerticalHeaderOnTheLeft
        self.verticalHeader().setVisible(False)
        
        # SetToNotEditable
        self.setEditTriggers(self.NoEditTriggers)
        
        # SetToLineAlternateColor
        self.setAlternatingRowColors(True)
        
        # SetAllowSorting
        self.setSortingEnabled(self.sorting)
        
        # SetToHeadExtension
        self.horizontalHeader().setSectionResizeMode(self.resizeMode)

    #----------------------------------------------------------------------
    def registerEvent(self):
        """RegisterGUIUpdateRelatedEventListeners"""
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)
        
    #----------------------------------------------------------------------
    def updateEvent(self, event):
        """ReceiveEventUpdates"""
        data = event.dict_['data']
        self.updateData(data)
    
    #----------------------------------------------------------------------
    def updateData(self, data):
        """UpdateTheDataToTheTable"""
        # If sorting is allowed, it must be turned off before inserting data, otherwise inserting new data will be messy
        if self.sorting:
            self.setSortingEnabled(False)
        
        # If the dataKey is set, the inventory update mode is used.
        if self.dataKey:
            key = data.__getattribute__(self.dataKey)
            # If the key does not exist in the data dictionary, insert a new line first and create the corresponding cell
            if key not in self.dataDict:
                self.insertRow(0)     
                d = {}
                for n, header in enumerate(self.headerList):                  
                    content = safeUnicode(data.__getattribute__(header))
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)
                    
                    if self.font:
                        cell.setFont(self.font)  # Make cell settings if special fonts are set
                    
                    if self.saveData:            # If the save data object is set, save the object
                        cell.data = data
                        
                    self.setItem(0, n, cell)
                    d[header] = cell
                self.dataDict[key] = d
            # Otherwise, if it already exists, update the relevant cell directly
            else:
                d = self.dataDict[key]
                for header in self.headerList:
                    content = safeUnicode(data.__getattribute__(header))
                    cell = d[header]
                    cell.setContent(content)
                    
                    if self.saveData:            # If the save data object is set, save the object
                        cell.data = data                    
        # Otherwise use incremental update mode
        else:
            self.insertRow(0)  
            for n, header in enumerate(self.headerList):
                content = safeUnicode(data.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content, self.mainEngine)
                
                if self.font:
                    cell.setFont(self.font)

                if self.saveData:
                    cell.data = data                

                self.setItem(0, n, cell)                        
                
        ## Adjust column width
        #if not self.columnResized:
            #self.resizeColumns()
            #self.columnResized = True
        
        # ReopenSort
        if self.sorting:
            self.setSortingEnabled(True)
    
    #----------------------------------------------------------------------
    def resizeColumns(self):
        """AdjustTheSizeOfEachColumn"""
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)    
        
    #----------------------------------------------------------------------
    def setSorting(self, sorting):
        """Set whether to allow sorting according to the header"""
        self.sorting = sorting
    
    #----------------------------------------------------------------------
    def setResizeMode(self, mode):
        """"""
        self.resizeMode = mode
        
    #----------------------------------------------------------------------
    def saveToCsv(self):
        """SaveTheTableContentsToACSVFile"""
        # HideTheRightClickMenuFirst
        self.menu.close()
        
        # GetTheNameOfTheFileYouWantToSave
        path, fileType = QtWidgets.QFileDialog.getSaveFileName(self, vtText.SAVE_DATA, '', 'CSV(*.csv)')

        try:
            #if not path.isEmpty():
            if path:
                with open(unicode(path), 'wb') as f:
                    writer = csv.writer(f)
                    
                    # SaveLabel
                    headers = [header.encode('gbk') for header in self.headerList]
                    writer.writerow(headers)
                    
                    # SaveEachLineOfContent
                    for row in range(self.rowCount()):
                        rowdata = []
                        for column in range(self.columnCount()):
                            item = self.item(row, column)
                            if item is not None:
                                rowdata.append(
                                    text_type(item.text()).encode('gbk'))
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)     
        except IOError:
            pass

    #----------------------------------------------------------------------
    def initMenu(self):
        """InitializeTheContextMenu"""
        self.menu = QtWidgets.QMenu(self)    
        
        resizeAction = QtWidgets.QAction(vtText.RESIZE_COLUMNS, self)
        resizeAction.triggered.connect(self.resizeColumns)        
        
        saveAction = QtWidgets.QAction(vtText.SAVE_DATA, self)
        saveAction.triggered.connect(self.saveToCsv)
        
        self.menu.addAction(resizeAction)
        self.menu.addAction(saveAction)
        
    #----------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """RightClickEvent"""
        self.menu.popup(QtGui.QCursor.pos())    


########################################################################
class MarketMonitor(BasicMonitor):
    """MarketMonitoringComponent"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(MarketMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        # SetTheHeaderOrderedDictionary
        d = OrderedDict()
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['lastPrice'] = {'chinese':vtText.LAST_PRICE, 'cellType':BasicCell}
        d['volume'] = {'chinese':vtText.VOLUME, 'cellType':BasicCell}
        d['openPrice'] = {'chinese':vtText.OPEN_PRICE, 'cellType':BasicCell}
        d['highPrice'] = {'chinese':vtText.HIGH_PRICE, 'cellType':BasicCell}
        d['lowPrice'] = {'chinese':vtText.LOW_PRICE, 'cellType':BasicCell}
        d['bidPrice1'] = {'chinese':vtText.BID_PRICE_1, 'cellType':BidCell}
        d['bidVolume1'] = {'chinese':vtText.BID_VOLUME_1, 'cellType':BidCell}
        d['askPrice1'] = {'chinese':vtText.ASK_PRICE_1, 'cellType':AskCell}
        d['askVolume1'] = {'chinese':vtText.ASK_VOLUME_1, 'cellType':AskCell}
        d['time'] = {'chinese':vtText.TIME, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtSymbol')
        self.setEventType(EVENT_TICK)
        self.setFont(BASIC_FONT)
        self.setSorting(False)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.initTable()
        self.registerEvent()
        
        self.setFixedHeight(400)


########################################################################
class LogMonitor(BasicMonitor):
    """LogMonitoring"""
    signalError = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()        
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['logTime'] = {'chinese':vtText.TIME, 'cellType':BasicCell}
        d['logContent'] = {'chinese':vtText.CONTENT, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_LOG)
        self.setFont(BASIC_FONT)        
        self.initTable()
        self.registerEvent()
        
        self.signalError.connect(self.processErrorEvent)
        self.eventEngine.register(EVENT_ERROR, self.signalError.emit)
        
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.setFixedHeight(200)
    
    #----------------------------------------------------------------------
    def processErrorEvent(self, event):
        """"""
        error = event.dict_['data']
        logContent = u'An error occurred, error code: %s, error message: %s' %(error.errorID, error.errorMsg)
        
        self.insertRow(0)
        cellLogTime = BasicCell(error.errorTime)
        cellLogContent = BasicCell(logContent)
        cellGatewayName = BasicCell(error.gatewayName)
        
        self.setItem(0, 0, cellGatewayName)
        self.setItem(0, 1, cellLogTime)
        self.setItem(0, 2, cellLogContent)



########################################################################
class TradeMonitor(BasicMonitor):
    """TransactionMonitoring"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradeMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['tradeID'] = {'chinese':vtText.TRADE_ID, 'cellType':NumCell}
        d['orderID'] = {'chinese':vtText.ORDER_ID, 'cellType':NumCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}
        d['price'] = {'chinese':vtText.PRICE, 'cellType':BasicCell}
        d['volume'] = {'chinese':vtText.VOLUME, 'cellType':BasicCell}
        d['tradeTime'] = {'chinese':vtText.TRADE_TIME, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_TRADE)
        self.setFont(BASIC_FONT)
        self.setSorting(True)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.initTable()
        self.registerEvent()

        self.setFixedHeight(200)
        

########################################################################
class OrderMonitor(BasicMonitor):
    """CommissionMonitoring"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(OrderMonitor, self).__init__(mainEngine, eventEngine, parent)

        self.mainEngine = mainEngine
        
        d = OrderedDict()
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['orderID'] = {'chinese':vtText.ORDER_ID, 'cellType':NumCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}
        d['price'] = {'chinese':vtText.PRICE, 'cellType':BasicCell}
        d['totalVolume'] = {'chinese':vtText.ORDER_VOLUME, 'cellType':BasicCell}
        d['tradedVolume'] = {'chinese':vtText.TRADED_VOLUME, 'cellType':BasicCell}
        d['status'] = {'chinese':vtText.ORDER_STATUS, 'cellType':BasicCell}
        d['orderTime'] = {'chinese':vtText.ORDER_TIME, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtOrderID')
        self.setEventType(EVENT_ORDER)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setSorting(True)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.initTable()
        self.registerEvent()
        self.connectSignal()
        
    #----------------------------------------------------------------------
    def connectSignal(self):
        """ConnectionSignal"""
        # DoubleClickOnTheCellToWithdrawTheOrder
        self.itemDoubleClicked.connect(self.cancelOrder) 
    
    #----------------------------------------------------------------------
    def cancelOrder(self, cell):
        """DataWithdrawalBasedOnCell"""
        order = cell.data
        
        req = VtCancelOrderReq()
        req.symbol = order.symbol
        req.exchange = order.exchange
        req.frontID = order.frontID
        req.sessionID = order.sessionID
        req.orderID = order.orderID
        self.mainEngine.cancelOrder(req, order.gatewayName)


########################################################################
class PositionMonitor(BasicMonitor):
    """PositionMonitoring"""
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}
        d['position'] = {'chinese':vtText.POSITION, 'cellType':BasicCell}
        d['frozen'] = {'chinese':vtText.FROZEN, 'cellType':BasicCell}
        d['price'] = {'chinese':vtText.PRICE, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtPositionName')
        self.setEventType(EVENT_POSITION)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.initTable()
        self.registerEvent()
        
        
########################################################################
class AccountMonitor(BasicMonitor):
    """AccountMonitoring"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        d['accountID'] = {'chinese':vtText.ACCOUNT_ID, 'cellType':BasicCell}
        d['balance'] = {'chinese':vtText.BALANCE, 'cellType':BasicCell}
        d['available'] = {'chinese':vtText.AVAILABLE, 'cellType':BasicCell}
        self.setHeaderDict(d)

        self.setDataKey('vtAccountID')
        self.setEventType(EVENT_ACCOUNT)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)

        self.initTable()
        self.registerEvent()
    
    #----------------------------------------------------------------------
    def updateData(self, data):
        """UpdateData"""
        super(AccountMonitor, self).updateData(data)

        # Hide the line if the delegate has completed
        vtAccountID = data.vtAccountID
        cellDict = self.dataDict[vtAccountID]
        cell = cellDict['balance']
        row = self.row(cell)

        if data.balance == 0:
            self.hideRow(row)
        else:
            self.showRow(row)


########################################################################
class DepthMonitor(QtWidgets.QTableWidget):
    """DeepMonitoringOfQuotation"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(DepthMonitor, self).__init__()    
        
        self.mainEngine = mainEngine
        
        self.contractSize = 1   # 合约乘数
        self.cellDict = {}
        
        self.initUi()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        labels = [u'Price',
                  u'Quantity',
                  u'Total']
        
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setRowCount(11)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)   
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch) 
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch) 
        
        left = QtCore.Qt.AlignLeft
        right = QtCore.Qt.AlignRight
        
        # Cell
        askColor = 'green'
        bidColor = 'red'
        lastColor = 'orange'
        
        self.addCell('askPrice5', 0, 0, askColor)
        self.addCell('askPrice4', 1, 0, askColor)
        self.addCell('askPrice3', 2, 0, askColor)
        self.addCell('askPrice2', 3, 0, askColor)
        self.addCell('askPrice1', 4, 0, askColor)
        self.addCell('lastPrice', 5, 0, lastColor)
        self.addCell('bidPrice1', 6, 0, bidColor)
        self.addCell('bidPrice2', 7, 0, bidColor)
        self.addCell('bidPrice3', 8, 0, bidColor)
        self.addCell('bidPrice4', 9, 0, bidColor)
        self.addCell('bidPrice5', 10, 0, bidColor)
        
        self.addCell('askVolume5', 0, 1, askColor)
        self.addCell('askVolume4', 1, 1, askColor)
        self.addCell('askVolume3', 2, 1, askColor)
        self.addCell('askVolume2', 3, 1, askColor)
        self.addCell('askVolume1', 4, 1, askColor)
        self.addCell('todayChange', 5, 1, lastColor)
        self.addCell('bidVolume1', 6, 1, bidColor)
        self.addCell('bidVolume2', 7, 1, bidColor)
        self.addCell('bidVolume3', 8, 1, bidColor)
        self.addCell('bidVolume4', 9, 1, bidColor)
        self.addCell('bidVolume5', 10, 1, bidColor)
        
        self.addCell('askValue5', 0, 2, askColor)
        self.addCell('askValue4', 1, 2, askColor)
        self.addCell('askValue3', 2, 2, askColor)
        self.addCell('askValue2', 3, 2, askColor)
        self.addCell('askValue1', 4, 2, askColor)
        self.addCell('bidValue1', 6, 2, bidColor)
        self.addCell('bidValue2', 7, 2, bidColor)
        self.addCell('bidValue3', 8, 2, bidColor)
        self.addCell('bidValue4', 9, 2, bidColor)
        self.addCell('bidValue5', 10, 2, bidColor)
        
    #----------------------------------------------------------------------
    def addCell(self, name, row, col, color, alignment=None):
        """AddANewCell"""
        cell = QtWidgets.QTableWidgetItem()
        self.setItem(row, col, cell)
        self.cellDict[name] = cell
        
        if color:
            cell.setForeground(QtGui.QColor(color))
        
        if alignment:
            cell.setTextAlignment(alignment)
        else:
            cell.setTextAlignment(QtCore.Qt.AlignCenter)
    
    #----------------------------------------------------------------------
    def updateCell(self, name, value, decimals=None, data=None):
        """UpdateCell"""
        if decimals is not None:
            text = '%.*f' %(decimals, value)
        else:
            text = '%s' %value
            
        cell = self.cellDict[name]
        cell.setText(text)
        
        if data:
            cell.price = data
    
    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """UpdateTick"""
        valueDecimals = 2
        
        # bid
        self.updateCell('bidPrice1', tick.bidPrice1, data=tick.bidPrice1)
        self.updateCell('bidPrice2', tick.bidPrice2, data=tick.bidPrice2)
        self.updateCell('bidPrice3', tick.bidPrice3, data=tick.bidPrice3)
        self.updateCell('bidPrice4', tick.bidPrice4, data=tick.bidPrice4)
        self.updateCell('bidPrice5', tick.bidPrice5, data=tick.bidPrice5)
        
        self.updateCell('bidVolume1', tick.bidVolume1, data=tick.bidPrice1)
        self.updateCell('bidVolume2', tick.bidVolume2, data=tick.bidPrice2)
        self.updateCell('bidVolume3', tick.bidVolume3, data=tick.bidPrice3)
        self.updateCell('bidVolume4', tick.bidVolume4, data=tick.bidPrice4)
        self.updateCell('bidVolume5', tick.bidVolume5, data=tick.bidPrice5)
        
        self.updateCell('bidValue1', tick.bidPrice1*tick.bidVolume1*self.contractSize, valueDecimals, data=tick.bidPrice1)
        self.updateCell('bidValue2', tick.bidPrice2*tick.bidVolume2*self.contractSize, valueDecimals, data=tick.bidPrice2)
        self.updateCell('bidValue3', tick.bidPrice3*tick.bidVolume3*self.contractSize, valueDecimals, data=tick.bidPrice3)
        self.updateCell('bidValue4', tick.bidPrice4*tick.bidVolume4*self.contractSize, valueDecimals, data=tick.bidPrice4)
        self.updateCell('bidValue5', tick.bidPrice5*tick.bidVolume5*self.contractSize, valueDecimals, data=tick.bidPrice5)
        
        # ask
        self.updateCell('askPrice1', tick.askPrice1, data=tick.askPrice1)
        self.updateCell('askPrice2', tick.askPrice2, data=tick.askPrice2)
        self.updateCell('askPrice3', tick.askPrice3, data=tick.askPrice3)
        self.updateCell('askPrice4', tick.askPrice4, data=tick.askPrice4)
        self.updateCell('askPrice5', tick.askPrice5, data=tick.askPrice5)
        
        self.updateCell('askVolume1', tick.askVolume1, data=tick.askPrice1)
        self.updateCell('askVolume2', tick.askVolume2, data=tick.askPrice2)
        self.updateCell('askVolume3', tick.askVolume3, data=tick.askPrice3)
        self.updateCell('askVolume4', tick.askVolume4, data=tick.askPrice4)
        self.updateCell('askVolume5', tick.askVolume5, data=tick.askPrice5)
        
        self.updateCell('askValue1', tick.askPrice1*tick.askVolume1*self.contractSize, valueDecimals, data=tick.askPrice1)
        self.updateCell('askValue2', tick.askPrice2*tick.askVolume2*self.contractSize, valueDecimals, data=tick.askPrice2)
        self.updateCell('askValue3', tick.askPrice3*tick.askVolume3*self.contractSize, valueDecimals, data=tick.askPrice3)
        self.updateCell('askValue4', tick.askPrice4*tick.askVolume4*self.contractSize, valueDecimals, data=tick.askPrice4)
        self.updateCell('askValue5', tick.askPrice5*tick.askVolume5*self.contractSize, valueDecimals, data=tick.askPrice5)
        
        # today
        self.updateCell('lastPrice', tick.lastPrice)
        
        if tick.openPrice:
            todayChange = tick.lastPrice/tick.openPrice - 1
        else:
            todayChange = 0
            
        self.updateCell('todayChange', ('%.2f%%' %(todayChange*100)))
    
    #----------------------------------------------------------------------
    def updateVtSymbol(self, vtSymbol):
        """ReplaceTheDisplayOfTheMarket"""
        for cell in self.cellDict.values():
            cell.setText('')
        
        contract = self.mainEngine.getContract(vtSymbol)
        if contract:
            self.contractSize = contract.size
        else:
            self.contractSize = 1


########################################################################
class TradingWidget(QtWidgets.QFrame):
    """SimpleTransactionComponent"""
    signal = QtCore.Signal(type(Event()))
    
    directionList = [DIRECTION_LONG,
                     DIRECTION_SHORT]

    priceTypeList = [PRICETYPE_LIMITPRICE,
                     PRICETYPE_MARKETPRICE]
    
    offsetList = [OFFSET_OPEN,
                  OFFSET_CLOSE]
    
    gatewayList = ['']

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradingWidget, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        self.vtSymbol = ''
        
        # AddTransactionInterface
        l = mainEngine.getAllGatewayDetails()
        gatewayNameList = [d['gatewayName'] for d in l]
        self.gatewayList.extend(gatewayNameList)

        self.initUi()
        self.registerEvent()

    #----------------------------------------------------------------------
    def initUi(self):
        """InitializationInterface"""
        self.setWindowTitle(vtText.TRADING)
        self.setFixedHeight(400)
        self.setFixedWidth(600)
        self.setFrameShape(self.Box)    # SetBorder
        self.setLineWidth(1)           

        # LeftPart
        labelPriceType = QtWidgets.QLabel(vtText.PRICE_TYPE)
        labelSymbol = QtWidgets.QLabel(u'VT代码')
        labelPrice = QtWidgets.QLabel(vtText.PRICE)
        labelVolume = QtWidgets.QLabel(u'数量')
        labelOffset = QtWidgets.QLabel(u'开平')
        
        self.comboPriceType = QtWidgets.QComboBox()
        self.comboPriceType.addItems(self.priceTypeList)
        
        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(self.offsetList)
        
        self.lineSymbol = QtWidgets.QLineEdit()
        
        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)        

        self.linePrice = QtWidgets.QLineEdit()
        self.linePrice.setValidator(validator)
        
        self.lineVolume = QtWidgets.QLineEdit()
        self.lineVolume.setValidator(validator)
        
        gridLeft = QtWidgets.QGridLayout()
        gridLeft.addWidget(labelPriceType, 0, 0)
        gridLeft.addWidget(labelOffset, 1, 0)
        gridLeft.addWidget(labelSymbol, 2, 0)
        gridLeft.addWidget(labelPrice, 3, 0)
        gridLeft.addWidget(labelVolume, 4, 0)
        
        gridLeft.addWidget(self.comboPriceType, 0, 1)
        gridLeft.addWidget(self.comboOffset, 1, 1)
        gridLeft.addWidget(self.lineSymbol, 2, 1)
        gridLeft.addWidget(self.linePrice, 3, 1)
        gridLeft.addWidget(self.lineVolume, 4, 1)
        
        # RightPart
        self.depthMonitor = DepthMonitor(self.mainEngine, self.eventEngine)

        # BillingButton
        buttonBuy = QtWidgets.QPushButton(u'买入')
        buttonSell = QtWidgets.QPushButton(u'卖出')
        buttonCancelAll = QtWidgets.QPushButton(vtText.CANCEL_ALL)
        
        size = buttonBuy.sizeHint()
        buttonBuy.setMinimumHeight(size.height()*2)
        buttonSell.setMinimumHeight(size.height()*2)
        buttonCancelAll.setMinimumHeight(size.height()*2)
        
        buttonBuy.clicked.connect(self.sendBuyOrder)
        buttonSell.clicked.connect(self.sendSellOrder)
        buttonCancelAll.clicked.connect(self.cancelAll)
        
        buttonBuy.setStyleSheet('color:white;background-color:red')
        buttonSell.setStyleSheet('color:white;background-color:green')
        buttonCancelAll.setStyleSheet('color:black;background-color:yellow')
        
        gridButton = QtWidgets.QGridLayout()
        gridButton.addWidget(buttonBuy, 0, 0)
        gridButton.addWidget(buttonSell, 0, 1)
        gridButton.addWidget(buttonCancelAll, 1, 0, 1, 2)
        
        # IntegratedLayout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(gridLeft)
        vbox.addLayout(gridButton)
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.depthMonitor)
        
        self.setLayout(hbox)

        # AssociatedUpdate
        self.lineSymbol.returnPressed.connect(self.updateSymbol)
        self.depthMonitor.itemDoubleClicked.connect(self.updatePrice)

    #----------------------------------------------------------------------
    def updateSymbol(self):
        """ContractChange"""
        self.vtSymbol = str(self.lineSymbol.text())
        contract = self.mainEngine.getContract(self.vtSymbol)
        
        if not contract:
            return
        
        # ClearThePriceQuantity
        self.linePrice.clear()
        self.lineVolume.clear()

        self.depthMonitor.updateVtSymbol(self.vtSymbol)
        
        # SubscriptionContract
        req = VtSubscribeReq()
        req.symbol = contract.symbol
        self.mainEngine.subscribe(req, contract.gatewayName)

    #----------------------------------------------------------------------
    def updateTick(self, event):
        """UpdateMarket"""
        tick = event.dict_['data']
        if tick.vtSymbol != self.vtSymbol:
            return
        self.depthMonitor.updateTick(tick)

    #----------------------------------------------------------------------
    def registerEvent(self):
        """RegisterEventListener"""
        self.signal.connect(self.updateTick)
        self.eventEngine.register(EVENT_TICK, self.signal.emit)        
    
    #----------------------------------------------------------------------
    def updatePrice(self, cell):
        """"""
        try:
            price = cell.price
        except AttributeError:
            return
        self.linePrice.setText(str(price))

    #----------------------------------------------------------------------
    def sendOrder(self, direction):
        """Billing"""
        vtSymbol = str(self.lineSymbol.text())
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            return

        # GetThePrice
        priceText = self.linePrice.text()
        if not priceText:
            return
        price = float(priceText)
        
        # GetQuantity
        volumeText = self.lineVolume.text()
        if not volumeText:
            return
        
        if '.' in volumeText:
            volume = float(volumeText)
        else:
            volume = int(volumeText)
        
        # Delegate
        req = VtOrderReq()
        req.symbol = contract.symbol
        req.price = price
        req.volume = volume
        req.direction = direction
        req.priceType = text_type(self.comboPriceType.currentText())
        req.offset = text_type(self.comboOffset.currentText())
        
        self.mainEngine.sendOrder(req, contract.gatewayName)
    
    #----------------------------------------------------------------------
    def sendBuyOrder(self):
        """"""
        self.sendOrder(DIRECTION_LONG)
        
    #----------------------------------------------------------------------
    def sendSellOrder(self):
        """"""
        self.sendOrder(DIRECTION_SHORT)
        
    #----------------------------------------------------------------------
    def cancelAll(self):
        """OneClickToCancelAllDelegates"""
        l = self.mainEngine.getAllWorkingOrders()
        for order in l:
            req = VtCancelOrderReq()
            req.symbol = order.symbol
            req.exchange = order.exchange
            req.frontID = order.frontID
            req.sessionID = order.sessionID
            req.orderID = order.orderID
            self.mainEngine.cancelOrder(req, order.gatewayName)


########################################################################
class ContractMonitor(BasicMonitor):
    """ContractInquiry"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """constructor"""
        super(ContractMonitor, self).__init__(parent=parent)
        
        self.mainEngine = mainEngine
        
        d = OrderedDict()
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['exchange'] = {'chinese':vtText.EXCHANGE, 'cellType':BasicCell}
        d['vtSymbol'] = {'chinese':vtText.VT_SYMBOL, 'cellType':BasicCell}
        d['productClass'] = {'chinese':vtText.PRODUCT_CLASS, 'cellType':BasicCell}
        d['size'] = {'chinese':vtText.CONTRACT_SIZE, 'cellType':BasicCell}
        d['priceTick'] = {'chinese':vtText.PRICE_TICK, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        # FilterTheStringForDisplay
        self.filterContent = EMPTY_STRING
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """InitializationInterface"""
        self.setMinimumSize(800, 800)
        self.setFont(BASIC_FONT)
        self.setResizeMode(QtWidgets.QHeaderView.Stretch)
        self.initTable()
        self.addMenuAction()
    
    #----------------------------------------------------------------------
    def showAllContracts(self):
        """ShowAllContractData"""
        l = self.mainEngine.getAllContracts()
        d = {'.'.join([contract.exchange, contract.symbol]):contract for contract in l}
        l2 = list(d.keys())
        l2.sort(reverse=True)

        self.setRowCount(len(l2))
        row = 0
        
        for key in l2:
            # Does not display if filter information is set and the filter code does not contain filtering information
            if self.filterContent and self.filterContent not in key:
                continue
            
            contract = d[key]
            
            for n, header in enumerate(self.headerList):
                content = safeUnicode(contract.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content)
                
                if self.font:
                    cell.setFont(self.font)  # Make cell settings if special fonts are set
                    
                self.setItem(row, n, cell)          
            
            row = row + 1        
    
    #----------------------------------------------------------------------
    def refresh(self):
        """refresh"""
        self.menu.close()   # CloseMenu
        self.clearContents()
        self.setRowCount(0)
        self.showAllContracts()
    
    #----------------------------------------------------------------------
    def addMenuAction(self):
        """AddRightClickMenuContent"""
        refreshAction = QtWidgets.QAction(vtText.REFRESH, self)
        refreshAction.triggered.connect(self.refresh)
        
        self.menu.addAction(refreshAction)
    
    #----------------------------------------------------------------------
    def show(self):
        """Show"""
        super(ContractMonitor, self).show()
        self.refresh()
        
    #----------------------------------------------------------------------
    def setFilterContent(self, content):
        """SetFilterString"""
        self.filterContent = content
    

########################################################################
class ContractManager(QtWidgets.QWidget):
    """ContractManagementComponent"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """Constructor"""
        super(ContractManager, self).__init__(parent=parent)
        
        self.mainEngine = mainEngine
        
        self.initUi()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """InitializationInterface"""
        self.setWindowTitle(vtText.CONTRACT_SEARCH)
        
        self.lineFilter = QtWidgets.QLineEdit()
        self.buttonFilter = QtWidgets.QPushButton(vtText.SEARCH)
        self.buttonFilter.clicked.connect(self.filterContract)        
        self.monitor = ContractMonitor(self.mainEngine)
        self.monitor.refresh()
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.lineFilter)
        hbox.addWidget(self.buttonFilter)
        hbox.addStretch()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.monitor)
        
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def filterContract(self):
        """ShowFilteredContract"""
        content = str(self.lineFilter.text())
        self.monitor.setFilterContent(content)
        self.monitor.refresh()


########################################################################
class WorkingOrderMonitor(OrderMonitor):
    """ActivityCommissionMonitoring"""
    STATUS_COMPLETED = [STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED]

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(WorkingOrderMonitor, self).__init__(mainEngine, eventEngine, parent)
        
    #----------------------------------------------------------------------
    def updateData(self, data):
        """UpdateData"""
        super(WorkingOrderMonitor, self).updateData(data)

        # HideTheLineIfTheDelegateHasCompleted
        if data.status in self.STATUS_COMPLETED:
            vtOrderID = data.vtOrderID
            cellDict = self.dataDict[vtOrderID]
            cell = cellDict['status']
            row = self.row(cell)
            self.hideRow(row)    
    

########################################################################
class SettingEditor(QtWidgets.QWidget):
    """ConfigurationEditor"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """Constructor"""
        super(SettingEditor, self).__init__(parent)
        
        self.mainEngine = mainEngine
        self.currentFileName = ''
        
        self.initUi()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """InitializationInterface"""
        self.setWindowTitle(vtText.EDIT_SETTING)
        
        self.comboFileName = QtWidgets.QComboBox()
        self.comboFileName.addItems(jsonPathDict.keys())
        
        buttonLoad = QtWidgets.QPushButton(vtText.LOAD)
        buttonSave = QtWidgets.QPushButton(vtText.SAVE)
        buttonLoad.clicked.connect(self.loadSetting)
        buttonSave.clicked.connect(self.saveSetting)
        
        self.editSetting = QtWidgets.QTextEdit()
        self.labelPath = QtWidgets.QLabel()
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.comboFileName)
        hbox.addWidget(buttonLoad)
        hbox.addWidget(buttonSave)
        hbox.addStretch()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.editSetting)
        vbox.addWidget(self.labelPath)
        
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def loadSetting(self):
        """LoadConfiguration"""
        self.currentFileName = str(self.comboFileName.currentText())
        filePath = jsonPathDict[self.currentFileName]
        self.labelPath.setText(filePath)
        
        with open(filePath) as f:
            self.editSetting.clear()
            
            for line in f:
                line = line.replace('\n', '')   # RemoveLineBreaks
                line = line.decode('UTF-8')
                self.editSetting.append(line)
    
    #----------------------------------------------------------------------
    def saveSetting(self):
        """SaveConfiguration"""
        if not self.currentFileName:
            return
        
        filePath = jsonPathDict[self.currentFileName]
        
        with open(filePath, 'w') as f:
            content = self.editSetting.toPlainText()
            content = content.encode('UTF-8')
            f.write(content)
        
    #----------------------------------------------------------------------
    def show(self):
        """Show"""
        # UpdateProfileDropDownBox
        self.comboFileName.clear()
        self.comboFileName.addItems(jsonPathDict.keys())
        
        # UI
        super(SettingEditor, self).show()

    
    
