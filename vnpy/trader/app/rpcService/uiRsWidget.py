# encoding: UTF-8

from vnpy.trader.uiQt import QtWidgets


########################################################################
class RsEngineManager(QtWidgets.QWidget):
    """RPC服务组件管理"""

    #----------------------------------------------------------------------
    def __init__(self, rsEngine, eventEngine, parent=None):
        """Constructor"""
        super(RsEngineManager, self).__init__(parent)
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'RPC Service')
        
        label = QtWidgets.QLabel(u'TheModuleRunsOnTheServer')
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        self.setLayout(vbox)
        
        
        
    
    