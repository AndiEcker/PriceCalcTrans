'''
    main application and UI
    
Created on Feb 2, 2012

@author: andi
@ToDo:  
- tableView column width restore
'''
import sys, os
import ConfigParser

from PyQt4.Qt import Qt
from PyQt4.QtCore import QSettings, pyqtSlot, QVariant, QModelIndex
from PyQt4.QtGui import QApplication, QMainWindow, QStatusBar, QMessageBox, \
    QVBoxLayout, QSizePolicy, QSplitter, QGroupBox, QLabel, QPushButton, QComboBox, \
    QTableView, QAbstractItemView, QStyledItemDelegate, QFont, QPixmap, QCloseEvent

from app_const import APP_TITLE, APP_VERSION
# import data models (PriceCalcScript encapsulates RulesModel)
from model import Condition, Action, ConditionsModel, ActionsModel, PriceCalcScript

# used for entering condition/action type
class ComboBoxDelegate(QStyledItemDelegate): #QItemDelegate):
    def __init__(self, typeCaptions, parent = None):
        QStyledItemDelegate.__init__(self, parent)
        self.typeCaptions = typeCaptions
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        i = 0
        for c in self.typeCaptions:
            editor.insertItem(i, c)
            i += 1
        return editor
    def setEditorData(self, comboBox, index):
        value = index.data(Qt.EditRole)
        comboBox.setCurrentIndex(value.toInt()[0])
    def setModelData(self, editor, model, index):
        value = editor.currentIndex()
        model.setData(index, QVariant(value), Qt.EditRole)
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        

# main window
class MainWindow(QMainWindow):
    """
        Initialization
    """
    def __init__(self, rulesModel, logoFnam, config, *args):
        QMainWindow.__init__(self, *args)
        
        self.rulesModel = rulesModel
        self.config = config
        
        self.rulesModel.dataChanged.connect(self._statusRefresh)
        
        self.cancelled = True   # for to handle win close box the same as Cancel button
        
        self.mainHSplit = QSplitter(self)   # data | buttons
        self.mainHSplit.setChildrenCollapsible(False)
        self.setCentralWidget(self.mainHSplit)

        self.mainVSplit = QSplitter(Qt.Vertical)
        self.mainVSplit.setChildrenCollapsible(False)
        self.mainHSplit.addWidget(self.mainVSplit)
        
        self._drawRules()
        self.mainVSplit.addWidget(self.rulesView)
        self.condActSplit = QSplitter()
        self.condActSplit.setChildrenCollapsible(False)
        self._drawCondAct()
        self.mainVSplit.addWidget(self.condActSplit)
        # let rules view resize vertically two times faster than cond/action view
        self.rulesView.setSizeIncrement(self.rulesView.sizeIncrement().width(), 
                                        2 * self.condView.sizeIncrement().height())
        
        self._drawButtons(logoFnam)
        self.setStatusBar(QStatusBar())
        self.condView.horizontalHeader().setCascadingSectionResizes(True)
        self.rulesView.selectRow(0)
                                
    def _drawRules(self):
        self.rulesView = QTableView()
        self.rulesView.setModel(self.rulesModel)
        self.rulesView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.rulesView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rulesView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rulesView.horizontalHeader().setStretchLastSection(True)
        self.rulesView.resizeColumnsToContents()
        #self.rulesView.verticalHeader().setMovable(True)  # row remapping - see QHeaderView.logicalIndex()
        #self.rulesView.verticalHeader().setCascadingSectionResizes(True)  # takes space from next row
        self.rulesView.selectionModel().currentRowChanged.connect(self._ruleRowChanged)
        self.rulesView.verticalHeader().sectionResized[int,int,int].connect(self._ruleRowHeightChanged)
        
    def _drawCondAct(self):
        if getattr(self, 'condGB', None):
            m_settings.setValue('spl_condAct', self.condActSplit.saveState())
            self.condGB.deleteLater() # or .destroy()
            del self.condGB
            self.actionGB.deleteLater()
            del self.actionGB
            
        row = self._ruleCurrRow()
        rcount = self.rulesModel.rowCount()
        
        self.condGB = QGroupBox(self.tr('Conditions'))
        self.condView = QTableView()
        conds = self.rulesModel.ruleConditions(row) if row in range(rcount) \
                else []
        self.condModel = ConditionsModel(conds, self.rulesModel, self.config)
        self.condModel.dataChanged.connect(self._codeFragChanged)
        self.condView.setModel(self.condModel)
        self.condTypeDelegate = ComboBoxDelegate(Condition._typeCaptions)
        self.condView.setItemDelegateForColumn(0, self.condTypeDelegate)
        self.condView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.condView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.condView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.condView.horizontalHeader().setStretchLastSection(True)
        self.condView.resizeColumnsToContents()
        self.condView.selectionModel().currentRowChanged.connect(self._statusRefresh)
        vbox = QVBoxLayout()
        vbox.addWidget(self.condView)
        self.condGB.setLayout(vbox)
        self.condActSplit.addWidget(self.condGB)
        
        self.actionGB = QGroupBox(self.tr('Actions'))
        self.actionView = QTableView()   # parent = self.actionGB)
        actions = self.rulesModel.ruleActions(row) if row in range(rcount) \
                else []
        self.actionModel = ActionsModel(actions, self.rulesModel, self.config)
        self.actionModel.dataChanged.connect(self._codeFragChanged)
        self.actionView.setModel(self.actionModel)
        self.actionTypeDelegate = ComboBoxDelegate(Action._typeCaptions)
        self.actionView.setItemDelegateForColumn(0, self.actionTypeDelegate)
        self.actionView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.actionView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.actionView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.actionView.horizontalHeader().setStretchLastSection(True)
        self.actionView.resizeColumnsToContents()
        self.actionView.selectionModel().currentRowChanged.connect(self._statusRefresh)
        vbox = QVBoxLayout()
        vbox.addWidget(self.actionView)
        self.actionGB.setLayout(vbox)
        self.condActSplit.addWidget(self.actionGB)
        
        self.condActSplit.restoreState(m_settings.value('spl_condAct').toByteArray())

        
    def _drawButton(self, vbox, caption, slot, ena = False):
        but = QPushButton(self.tr(caption))
        but.setEnabled(ena)
        but.clicked.connect(getattr(self, slot))
        vbox.addWidget(but)     # add to VBoxLayout
        return but
    
    def _drawButtons(self, logoFnam):
        gbox = QGroupBox()
        spol = QSizePolicy()
        spol.horizontalPolicy = QSizePolicy.Maximum
        gbox.setSizePolicy(spol)
        vbox = QVBoxLayout()
        
        if os.path.isfile(logoFnam):
            img = QPixmap(logoFnam)    #.scaled(64, 64)
            lblLogo = QLabel()
            lblLogo.setPixmap(img)
            lblLogo.setAlignment(Qt.AlignTop | Qt.AlignRight)
            vbox.addWidget(lblLogo)
            #vbox.addSpacing(3) 
        
        self.butSave = self._drawButton(vbox, "M&odify", 'closeSave')
        font = QFont()
        font.setBold(True)
        self.butSave.setFont(font)
        self.butCancel = self._drawButton(vbox, "Cancel", 'closeCancel', True)
        vbox.addSpacing(36)
        self.butAddRule = self._drawButton(vbox, "Add Rule", 'addRule', True)
        self.butCopyRule = self._drawButton(vbox, "Copy Rule", 'copyRule')
        self.butDelRule = self._drawButton(vbox, "Delete Rule", 'delRule')
        self.butMoveRuleUp = self._drawButton(vbox, "Move Rule Up", 'moveRuleUp')
        self.butMoveRuleDn = self._drawButton(vbox, "Move Rule Down", 'moveRuleDown')
        vbox.addSpacing(24)
        self.butAddCond = self._drawButton(vbox, "Add Condition", 'addCond')
        self.butDelCond = self._drawButton(vbox, "Delete Condition", 'delCond')
        vbox.addSpacing(15)
        self.butAddAction = self._drawButton(vbox, "Add Action", 'addAction')
        self.butDelAction = self._drawButton(vbox, "Delete Action", 'delAction')
        
        gbox.setLayout(vbox)
        self.mainHSplit.addWidget(gbox) 
    
    """
        Internal Bindings Signal Receivers
    """
    # main win close events
    # .. (cancel closing with event.ignore(); QMainWindow calls event.accept())       
    @pyqtSlot(QCloseEvent)
    def closeEvent(self, event):
        self._saveAppState()
        # save rules if not empty and user clicked Modified/Save button
        if self.rulesModel.rowCount() > 0 and not self.cancelled:
            text = self.rulesModel.getRawRules().validate()
            if text:
                self.cancelled = True
                QMessageBox.information(self, APP_TITLE, 
                                        self.tr("Validation failed because of:<p><p>") + text)
                event.ignore()
                return              #  RETURN - cancel app closing ######
            m_script.save()
        # accept window closing
        QMainWindow.closeEvent(self, event)
        # quit application
        m_app.quit()
    @pyqtSlot()
    def _statusRefresh(self):       # dis/enable buttons, display view selections
        ruleRow = self._ruleCurrRow()
        condRow = self._condCurrRow()
        actionRow = self._actionCurrRow()
        self.butSave.setEnabled(self.rulesModel.isModified())
        ruleCnt = self.rulesModel.rowCount()
        self.butCopyRule.setEnabled(ruleRow >= 0)
        self.butDelRule.setEnabled(ruleRow >= 0)
        self.butMoveRuleUp.setEnabled(ruleRow > 0)
        self.butMoveRuleDn.setEnabled(ruleRow >= 0 and ruleRow + 1 < ruleCnt)
        self.butAddCond.setEnabled(ruleRow >= 0)
        self.butDelCond.setEnabled(condRow >= 0)  
        self.butAddAction.setEnabled(ruleRow >= 0)
        self.butDelAction.setEnabled(actionRow >= 0)
        # display currently selected list rows in the status bar - if empty
        if ruleRow >= 0 and False:    # replace False with ~self.statusBar().isEmpty()?!?!?
            text = str(self.tr("Selected Rule: {ruleI}"))\
                .format(ruleI = ruleRow + 1)
            if condRow >= 0:
                text += "      " \
                    + str(self.tr("Selected Condition: {typeI}"))\
                    .format(typeI = condRow + 1)
            if actionRow >= 0:
                text += "      " \
                    + str(self.tr("Selected Action: {typeI}"))\
                    .format(typeI = actionRow + 1)
            self.statusBar().showMessage(text, 3000)
    @pyqtSlot(int,int,int)
    def _ruleRowHeightChanged(self, section, oldsize, newsize):
        hdr = self.rulesView.verticalHeader()
        for row in range(hdr.count()):
            if row != section:
                hdr.resizeSection(row, newsize)
    @pyqtSlot()
    def _ruleRowChanged(self):
        self._drawCondAct()
        self._statusRefresh()
    @pyqtSlot()
    def _codeFragChanged(self):     # refresh the rules list columns Conditions and Actions
        row = self._ruleCurrRow()
        leftColIndex = self.rulesModel.index(row, 2, QModelIndex())
        rightColIndex = self.rulesModel.index(row, 3, QModelIndex())
        self.rulesView.dataChanged(leftColIndex, rightColIndex)
        self._statusRefresh()
        
    """
        User Action Signal Receivers
    """
    @pyqtSlot()
    def closeSave(self):
        self.cancelled = False
        self.close()
    @pyqtSlot()
    def closeCancel(self):
        self.cancelled = True
        self.close()
    @pyqtSlot()
    def addRule(self):
        row = self._ruleCurrRow()
        self.rulesModel.insertRow(row)
        self.rulesView.selectRow(row)
        self._statusRefresh()
    @pyqtSlot()
    def copyRule(self):
        row = self._ruleCurrRow()
        self.rulesModel.setSourceRowForNextAdd(row)
        self.rulesModel.insertRow(row)
        self.rulesView.selectRow(row)
        self._statusRefresh()
    @pyqtSlot()
    def delRule(self):
        self.rulesModel.removeRow(self._ruleCurrRow())
        self._statusRefresh()
    @pyqtSlot()
    def moveRuleUp(self):
        row = self._ruleCurrRow()
        self.rulesModel.moveRule(row, -1)
        self._statusRefresh()
    @pyqtSlot()
    def moveRuleDown(self):
        row = self._ruleCurrRow()
        self.rulesModel.moveRule(row)
        self._statusRefresh()
    @pyqtSlot()
    def addCond(self):
        cnt = self.condModel.rowCount()
        self.condModel.insertRow(cnt)
        self.condView.selectRow(cnt)
        self._statusRefresh()
    @pyqtSlot()
    def delCond(self):
        self.condModel.removeRow(self._condCurrRow())
        self._statusRefresh()
    @pyqtSlot()
    def addAction(self):
        cnt = self.actionModel.rowCount()
        self.actionModel.insertRow(cnt)
        self.actionView.selectRow(cnt)
        self._statusRefresh()
    @pyqtSlot()
    def delAction(self):
        self.actionModel.removeRow(self._actionCurrRow())
        self._statusRefresh()
    
    """
        Helping Methods
    """
    def _ruleCurrRow(self):
        #idxs = self.rulesView.selectedIndexes()
        #return idxs[0].row() if idxs else -1
        return self.rulesView.currentIndex().row()
    def _condCurrRow(self):
        return self.condView.currentIndex().row()
    def _actionCurrRow(self):
        return self.actionView.currentIndex().row()
    
    # main win save/restore
    def _saveAppState(self):
        m_app.processEvents()
        # save win geometry and splitter positions
        _UI_SAVE(self, 'win_geometry')
        _UI_SAVE(self.mainHSplit, 'spl_mainH')
        _UI_SAVE(self.mainVSplit, 'spl_mainV')
        _UI_SAVE(self.condActSplit, 'spl_condAct')
        #_UI_SAVE(self.condView.horizontalHeader(), 'tvh_condHdr')
    def _restoreAppState(self):
        try:    # will fail on first app startup after installation
            # restore last win position, -size and 3 splitter positions
            _UI_RESTORE(self, 'win_geometry')
            _UI_RESTORE(self.mainHSplit, 'spl_mainH')
            _UI_RESTORE(self.mainVSplit, 'spl_mainV')
            _UI_RESTORE(self.condActSplit, 'spl_condAct')
            #_UI_RESTORE(self.condView.horizontalHeader(), 'tvh_condHdr')
        except: # first start
            screenWidth = QApplication.desktop().width()
            screenHeight = QApplication.desktop().height()
            self.setGeometry(screenWidth / 9, screenHeight / 12,
                            screenWidth / 1.26, screenHeight / 1.56)
        
    

       
# global settings repository and helping functions
m_settings = QSettings('AEcker', 'PriceCalcTrans')
def _UI_SAVE(widget, key):
    if key[:4] == 'win_':
        m_settings.setValue(key, widget.saveGeometry())
    #elif key[:4] == 'tvh_':
        # restoreState not working for table view header in win init phase - also failed if
        # .. delayed by timer/after win.show/... (TableView does auto col resize on content)
        # .. possibly use QHeaderView.sectionSize() and .resizeSection() instead?!?!?
    #    pass        
    else:
        m_settings.setValue(key, widget.saveState())
def _UI_RESTORE(widget, key):
    if key[:4] == 'win_':
        # win size not fully restored if too small for displayed content?!?!?
        widget.restoreGeometry(m_settings.value(key).toByteArray())
    #elif key[:4] == 'tvh_':
    #    pass        
    else:
        widget.restoreState(m_settings.value(key).toByteArray())


def main(args):
    # for single app instance check http://www.developer.nokia.com/Community/Wiki/Run_only_one_instance_of_a_Qt_application
    global m_app
    m_app = QApplication(args)
    luaFnam = args[1] if len(args) >= 2 else 'NewLuaScript.txt'
    logoFnam = args[2] if len(args) >= 3 else 'PriceCalcTrans.jpg'
    confFnam = args[3] if len(args) >= 4 else 'PriceCalcTrans.cfg'

    global m_script
    m_script = PriceCalcScript(luaFnam)
    m_script.load()

    config = ConfigParser.SafeConfigParser()
    try:
        config.readfp(open(confFnam))
    except:
        config = None
    win = MainWindow(m_script.rulesModel, logoFnam, config)
    win.setWindowTitle(win.tr(APP_TITLE) + " " + APP_VERSION + "      " + luaFnam)
    win.show()
    win._restoreAppState()
    sys.exit(m_app.exec_())

if __name__ == '__main__':
    main(sys.argv)
