# encoding: UTF-8

import psutil
import traceback

from vnpy.trader.vtFunction import loadIconPath
from vnpy.trader.vtGlobal import globalSetting

from uiCryptoWidget import *


########################################################################
class MainWindow(QtWidgets.QMainWindow):
    """MainWindow"""

    signalStatusBar = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""          
        super(MainWindow, self).__init__()
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        l = self.mainEngine.getAllGatewayDetails()
        self.gatewayNameList = [d['gatewayName'] for d in l]        
        
        self.widgetDict = {}    # a dictionary for saving child windows
        
        # Get the upper application information in the main engine
        self.appDetailList = self.mainEngine.getAllAppDetails()
        
        self.initUi()
        self.loadWindowSettings('custom')
        
    #----------------------------------------------------------------------
    def initUi(self):
        """initializationInterface"""
        self.setWindowTitle('VnTrader')
        self.initCentral()
        self.initMenu()
        self.initStatusBar()
        
    #----------------------------------------------------------------------
    def initCentral(self):
        """initializeTheCentralArea"""
        widgetTradingW, dockTradingW = self.createDock(TradingWidget, vtText.TRADING, QtCore.Qt.RightDockWidgetArea) 
        widgetMarketM, dockMarketM = self.createDock(MarketMonitor, vtText.MARKET_DATA, QtCore.Qt.LeftDockWidgetArea)
        
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, vtText.ORDER, QtCore.Qt.LeftDockWidgetArea)
        widgetWorkingOrderM, dockWorkingOrderM = self.createDock(WorkingOrderMonitor, vtText.WORKING_ORDER, QtCore.Qt.LeftDockWidgetArea)
        widgetTradeM, dockTradeM = self.createDock(TradeMonitor, vtText.TRADE, QtCore.Qt.LeftDockWidgetArea)
        
        widgetAccountM, dockAccountM = self.createDock(AccountMonitor, vtText.ACCOUNT, QtCore.Qt.RightDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(PositionMonitor, vtText.POSITION, QtCore.Qt.RightDockWidgetArea)        
        widgetLogM, dockLogM = self.createDock(LogMonitor, vtText.LOG, QtCore.Qt.RightDockWidgetArea)
        
        self.tabifyDockWidget(dockOrderM, dockWorkingOrderM)
        self.tabifyDockWidget(dockPositionM, dockAccountM)
        
        # saveDefaultSettings
        self.saveWindowSettings('default')
        
    #----------------------------------------------------------------------
    def initMenu(self):
        """InitializationMenu"""
        # Create menu
        menubar = self.menuBar()
        
        # Designed to display only existing interfaces
        gatewayDetails = self.mainEngine.getAllGatewayDetails()
        
        sysMenu = menubar.addMenu(vtText.SYSTEM)
        
        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_FUTURES:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()
        
        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_EQUITY:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()
        
        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_INTERNATIONAL:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])       
        sysMenu.addSeparator()
                
        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_BTC:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()
                
        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_DATA:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        
        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(vtText.CONNECT_DATABASE, self.mainEngine.dbConnect, loadIconPath('database.ico')))
        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(vtText.EXIT, self.close, loadIconPath('exit.ico')))
        
        # Functional application
        appMenu = menubar.addMenu(vtText.APPLICATION)
        
        for appDetail in self.appDetailList:
            # If there is no application interface, no menu button is added
            if not appDetail['appWidget']:
                continue
            
            function = self.createOpenAppFunction(appDetail)
            action = self.createAction(appDetail['appDisplayName'], function, loadIconPath(appDetail['appIco']))
            appMenu.addAction(action)
        
        # help
        helpMenu = menubar.addMenu(vtText.HELP)
        helpMenu.addAction(self.createAction(vtText.CONTRACT_SEARCH, self.openContract, loadIconPath('contract.ico')))
        helpMenu.addAction(self.createAction(vtText.EDIT_SETTING, self.openSettingEditor, loadIconPath('editor.ico')))
        helpMenu.addSeparator()
        helpMenu.addAction(self.createAction(vtText.RESTORE, self.restoreWindow, loadIconPath('restore.ico')))
        helpMenu.addAction(self.createAction(vtText.ABOUT, self.openAbout, loadIconPath('about.ico')))
        helpMenu.addSeparator()
        helpMenu.addAction(self.createAction(vtText.TEST, self.test, loadIconPath('test.ico')))
    
    #----------------------------------------------------------------------
    def initStatusBar(self):
        """InitializeStatusBar"""
        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)
        
        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())
        
        self.sbCount = 0
        self.sbTrigger = 10     # Refresh once every 10 seconds
        self.signalStatusBar.connect(self.updateStatusBar)
        self.eventEngine.register(EVENT_TIMER, self.signalStatusBar.emit)
        
    #----------------------------------------------------------------------
    def updateStatusBar(self, event):
        """Update CPU and memory information in the status bar"""
        self.sbCount += 1
        
        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory())
    
    #----------------------------------------------------------------------
    def getCpuMemory(self):
        """Get CPU and memory status information"""
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return vtText.CPU_MEMORY_INFO.format(cpu=cpuPercent, memory=memoryPercent)
        
    #----------------------------------------------------------------------
    def addConnectAction(self, menu, gatewayName, displayName=''):
        """Increase connection function"""
        if gatewayName not in self.gatewayNameList:
            return
        
        def connect():
            self.mainEngine.connect(gatewayName)
            
        if not displayName:
            displayName = gatewayName
        
        actionName = vtText.CONNECT + displayName
        connectAction = self.createAction(actionName, connect, 
                                          loadIconPath('connect.ico'))
        menu.addAction(connectAction)
        
    #----------------------------------------------------------------------
    def createAction(self, actionName, function, iconPath=''):
        """Create operational features"""
        action = QtWidgets.QAction(actionName, self)
        action.triggered.connect(function)
        
        if iconPath:
            icon = QtGui.QIcon(iconPath)
            action.setIcon(icon)
            
        return action
    
    #----------------------------------------------------------------------
    def createOpenAppFunction(self, appDetail):
        """Create a function that opens the app UI"""
        def openAppFunction():
            appName = appDetail['appName']
            try:
                self.widgetDict[appName].show()
            except KeyError:
                appEngine = self.mainEngine.getApp(appName)
                self.widgetDict[appName] = appDetail['appWidget'](appEngine, self.eventEngine)
                self.widgetDict[appName].show()
                
        return openAppFunction
        
    #----------------------------------------------------------------------
    def test(self):
        """Test button function"""
        # There is a need to use a manually triggered test function can be written here
        pass

    #----------------------------------------------------------------------
    def openAbout(self):
        """openAbout"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()
    
    #----------------------------------------------------------------------
    def openContract(self):
        """Open contract query"""
        try:
            self.widgetDict['contractM'].show()
        except KeyError:
            self.widgetDict['contractM'] = ContractManager(self.mainEngine)
            self.widgetDict['contractM'].show()
            
    #----------------------------------------------------------------------
    def openSettingEditor(self):
        """Open configuration editing"""
        try:
            self.widgetDict['settingEditor'].show()
        except KeyError:
            self.widgetDict['settingEditor'] = SettingEditor(self.mainEngine)
            self.widgetDict['settingEditor'].show()    
    
    #----------------------------------------------------------------------
    def closeEvent(self, event):
        """closingEvent"""
        reply = QtWidgets.QMessageBox.question(self, vtText.EXIT,
                                           vtText.CONFIRM_EXIT, QtWidgets.QMessageBox.Yes | 
                                           QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes: 
            for widget in self.widgetDict.values():
                widget.close()
            self.saveWindowSettings('custom')
            
            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()
            
    #----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """CreateDockingComponents"""
        widget = widgetClass(self.mainEngine, self.eventEngine)
        dock = QtWidgets.QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
    
    #----------------------------------------------------------------------
    def saveWindowSettings(self, settingName):
        """SaveWindowSettings"""
        settings = QtCore.QSettings('vn.trader', settingName)
        settings.setValue('state', self.saveState())
        settings.setValue('geometry', self.saveGeometry())
        
    #----------------------------------------------------------------------
    def loadWindowSettings(self, settingName):
        """LoadWindowSettings"""
        settings = QtCore.QSettings('vn.trader', settingName)           
        state = settings.value('state')
        geometry = settings.value('geometry')
        
        # NotInitializedYet
        if state is None:
            return
        # OldVersionOfPyQt
        elif isinstance(state, QtCore.QVariant):
            self.restoreState(state.toByteArray())
            self.restoreGeometry(geometry.toByteArray())
        # NewVersionOfPyQt
        elif isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)
        # Default
        else:
            content = u'Loading window configuration exception, please check'
            self.mainEngine.writeLog(content)
        
    #----------------------------------------------------------------------
    def restoreWindow(self):
        """Restore default window settings (restore docking component location)"""
        self.loadWindowSettings('default')
        self.showMaximized()


########################################################################
class AboutWidget(QtWidgets.QDialog):
    """showInformationAbout"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(vtText.ABOUT + 'VnTrader')

        text = u"""
            Developed by Traders, for Traders.

            License：MIT
            
            Website：www.vnpy.org

            Github：www.github.com/vnpy/vnpy
            
            """

        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)
    