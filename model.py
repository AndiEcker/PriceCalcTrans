'''
    data models for Price Calc Lua Script Transformer Model
    
Created on Feb 2, 2012

@author: andi
'''
import os, copy
from datetime import date       # needed for validation within eval expressions

from PyQt4.Qt import Qt
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant
from PyQt4.QtGui import QApplication, QMessageBox

from parse import parse

#############   Constants and Macros   ##################################################

from app_const import APP_TITLE

# dict field name suffixes for year, month and day parts of date values
# .. DON'T USE white-chars/spaces because of parse module bug
_Y = 'Year'
_M = 'Month'
_D = 'Day'

# lua code fragments and markers
_INDENT = '   '     # strip()-able white chars
_LINESEP = '\r\n'
_OP_AND = ' and ' 
_COND_ELSE = 'else'
_COND_IF_BEG = 'if ('
_COND_IF_END = ') then'
_COMM_BEG = '--[['
_COMM_END = '--]]'
_HEADER_PREFIX = _LINESEP + _COMM_BEG + _LINESEP + '      !!!   PLEASE NEVER CHANGE THE CONTENT OF THIS FILE   !!!' + _LINESEP \
                + _LINESEP + 'This file is exclusively maintained by the application ' + APP_TITLE + _LINESEP \
                + '\n'      # last newline is unix style to detect if script uses windows style
_HEADER_SUFFIX = _LINESEP + _COMM_END + _LINESEP

def _DAY_XLIT(field):  # dupl. lua-function-call curly brackets for string.format escaping
    return 'math.floor(os.time{{year={' + field+_Y + '}, month={' + field+_M \
                           + '}, day={' + field+_D + '}}} / (24*60*60))'

def _DAY_XVAR(vname):
    return 'math.floor(' + vname + ' / (24*60*60))'

# user messages macros
def _MAIN_WIN():
    qApp = QApplication.instance()
    if qApp:
        qAppWin = qApp.activeWindow()
    return qAppWin if qApp else 0
def _WARNING(text):
    qAppWin = _MAIN_WIN()
    if qAppWin:
        qAppWin.statusBar().showMessage(text.replace('<p>', '  '), 12900)
    else:
        print text.replace('<p>', '  ')
def _ERROR(text):
    qAppWin = _MAIN_WIN()
    if qAppWin:
        qAppWin.statusBar().showMessage(text.replace('<p>', '  '), 18600)
    else:
        print text.replace('<p>', '  ')
        QMessageBox.critical(None, APP_TITLE, text)

# i18n helper macro
def _TR(text):
    qAppWin = _MAIN_WIN()
    if qAppWin:
        text = str(_MAIN_WIN().tr(text))
    return text


# separator chars and formatting strings used in UI
_DATE_SEP = _TR("-")
_DATE_RANGE_SEP = _TR("..")
def _DATE_FORMAT(field):
    return '{' + field+_D + '}' + _DATE_SEP + '{' + field+_M + '}' + _DATE_SEP + '{' + field+_Y + '}'
# helper macro for to create _CodeFragment.params dictionaries
def _DATE_RANGE_DICT(field, year, month, day, field2, year2, month2, day2, 
                     xkey = None, xval = None):
    ret = {}
    ret[field+_Y] = year
    ret[field+_M] = month
    ret[field+_D] = day
    ret[field2+_Y] = year2
    ret[field2+_M] = month2
    ret[field2+_D] = day2
    if xkey:
        ret[xkey] = xval
    return ret
def _DATE_RANGE_VALID_EXPR(field, field2):
    return 'date({' + field+_Y + '},{' + field+_M + '},{' + field+_D \
        + '}) <= date({' + field2+_Y + '},{' + field2+_M + '},{' + field2+_D + '})'

_INT_RANGE_SEP = _DATE_RANGE_SEP


######################   _CodeFragTypes base class with specializations CondTypes and ActTypes   #################################


class _CodeFragTypes(object):
    _name = ''
    _typeCaptions = []
    _isExclusives = []
    _paramTemplates = []
    _luaTemplates = []
    _luaTemplSupportedVersionss = [[]]
    _params = []
    _validationTemplates = []
    _validationCaptions = []

class CondTypes(_CodeFragTypes):
    _name = 'ConditionType'

class ActTypes(_CodeFragTypes):
    _name = 'ActionType'


"""
#############   Raw Data   ##################################################
"""


#############   Rules   ##################################################


# raw rules data == extended list of _Rule objects
class _Rules(list):
    def __init__(self, luaScriptCode = None, *args, **kwargs):
        super(_Rules, self).__init__(*args, **kwargs)
        if luaScriptCode:
            # skip first two/three lines: function calcPrice()//day_price = ... (if exists)
            # .. (v1.6 skips only 2 lines because doesn't have the code line: day_price = sn_standardamount)
            # .. and skip/remove empty lines and last three lines: end//return.../end
            luaCodeLines = []
            for luaCodeLine in luaScriptCode.split(_LINESEP):
                if len(luaCodeLines) == 0:
                    if not luaCodeLine.startswith(_INDENT + _COND_IF_BEG):
                        continue
                    luaCodeLines.append(_INDENT + _COND_ELSE + luaCodeLine[len(_INDENT):])
                elif luaCodeLine.startswith(_INDENT + 'end') or luaCodeLine.startswith(_INDENT + 'return ('):
                    break               # reached the end of the LUA elseif statement
                elif luaCodeLine:       # skip empty code line
                    luaCodeLines.append(luaCodeLine)
            luaRulesCode = _LINESEP.join(luaCodeLines).split(_INDENT + _COND_ELSE + _COND_IF_BEG)[1:]   # first item is empty
            for luaRuleCode in luaRulesCode:  
                self.append(_Rule(luaRuleCode))

    def luaCodeGen(self):
        elseifs = [ r.luaCodeGen() for r in self ]
        return _LINESEP \
            + 'function calcPrice()' + _LINESEP \
            + _INDENT + 'day_price = sn_standardamount' + _LINESEP \
            + _INDENT + _LINESEP.join(elseifs)[len(_INDENT) + len(_COND_ELSE):] + _LINESEP \
            + _INDENT + ('end' if len(elseifs) else '') + _LINESEP \
            + _INDENT + 'return ( day_price )' + _LINESEP \
            + 'end' + _LINESEP

    def validate(self):
        ret = ''
        try:
            for r in self:
                validationErrorMsg = r.validate()
                if validationErrorMsg:
                    ret += _TR("<p><p>Rule <b>'{0}'</b> has the following validation errors:<p>")\
                            .format(r.name) \
                           + validationErrorMsg
        except Exception as e:
            ret = _TR("_Rules validation system error: {0}").format(e)
        return ret


# helper method for to parse lua code and recognize conditions/actions of actual and previous versions
def luaCodeParse(luaCode, typeClass):
    res = None
    for nI in range(len(typeClass._types._luaTemplates)):
        templates = typeClass._types._luaTemplSupportedVersionss[nI]
        templates.insert(0, typeClass._types._luaTemplates[nI])
        for formatStr in templates:
            try:
                res = parse(formatStr, luaCode)
            except:
                res = None
            if res:
                break
        if res:
            break
    if res:
        res = dict(params = res.named, typeI = nI)
    return res
    
    
class _Rule(object):
    def __init__(self, luaRuleCode = None):
        # set default values for new rule
        self.enabled = True
        self.name = _TR("(new rule)")
        self.conditions = []
        self.actions = []
        if luaRuleCode:         # rule definition passed as lua script code
            # format: condition[<_LINESEP>action0[<_LINESEP>action1...]]
            parts = luaRuleCode.split(_LINESEP)     # parts[0]==enable-flag/conditions/ruleName
            condPosBeg = 0
            condPosEnd = parts[0].find(_COMM_BEG)
            if condPosEnd == -1:                    # exception for old format from previous version (< 3.1)
                self.enabled = True                 # old format integrates only the enabled rules in lua code
                self.name = _TR('(imported rule)')  # .. also the rule name is only stored in the pickled header
                condPosBeg += 4 if parts[0].startswith('true') else 0
            else:
                self.enabled = parts[0].startswith('true')
                self.name = parts[0][condPosEnd + len(_COMM_BEG):-len(_COMM_END)]
                condPosBeg += (4 if self.enabled else 5) + len(_OP_AND)
            condPosEnd = parts[0].find(_COND_IF_END)
            
            # because each condition can contain also _OP_AND operators we have to determine the end of each condition here
            combinedExpr = ''
            for expr in parts[0][condPosBeg:condPosEnd].strip().split(_OP_AND):
                combinedExpr += _OP_AND + expr
                res = luaCodeParse(combinedExpr[len(_OP_AND):], Condition)
                if res:
                    self.conditions.append(Condition(combinedExpr[len(_OP_AND):]))
                    combinedExpr = ''
            if combinedExpr:      # left overs because of import/parse error
                self.name = combinedExpr + _TR(' (condition import/parse error)')

            # parts[1:]==actions        
            if len(parts) > 1:
                self.actions = [Action(ca.strip()) for ca in parts[1:] if ca.strip()]

    def luaCodeGen(self):
        # check for empty/TRUE condition
        conditions = filter(lambda c: c.typeI >= 0, self.conditions)
        if len(conditions):
            condCode = _OP_AND.join([ c.luaCodeGen() for c in conditions ]) 
        else:
            condCode = 'true'
        return _INDENT + _COND_ELSE + _COND_IF_BEG + ('true' if self.enabled else 'false') + _OP_AND + condCode + _COND_IF_END + ' ' + _COMM_BEG + str(self.name) + _COMM_END + _LINESEP \
            + _LINESEP.join([ _INDENT + _INDENT + a.luaCodeGen() for a in self.actions 
                              if a.typeI >= 0 ]) + _LINESEP


    def validate(self):
        return "".join([ c.validate() for c in self.conditions ]
                       + [ a.validate() for a in self.actions ]) \
            if self.enabled else ""     # don't validate disabled rule




######################   _CodeFragment base class with specializations Condition and Action   #################################

# single instance of conditionTypes and actionTypes (for all Condition/Action classes instances) - overloaded by config file content
actionTypes = ActTypes()
conditionTypes = CondTypes()



# base class for Condition and Action
class _CodeFragment(object):
    typeI = -1
    params = {}
    _name = ''
    _types = None
    def __init__(self, luaCodeFrag = None):
        self.params = dict()     # or {} - needed for to create individual dict for each instance
        if luaCodeFrag:
            res = luaCodeParse(luaCodeFrag, self)
            if res:
                self.typeI = res['typeI']
                self.params = res['params']

    def luaCodeGen(self):
        return self._types._luaTemplates[self.typeI].format(**self.params) if self.typeI >= 0 else ''

    def setTypeIndex(self, typeI, types):
        if self._types._isExclusives[typeI]:     # prevent duplicate exclusive condition/action type
            ret = len(filter(lambda c: c.typeI == typeI and c is not self, types)) == 0
            if not ret:
                _WARNING(_TR("{0} Type '{1}' is already added to this rule.<p>" \
                             + " If you want to specify another value of this {0} Type then add a new rule instead.")\
                          .format(self._name, self._types._typeCaptions[typeI]))
        else:
            ret = True
        if ret:
            if typeI != self.typeI and self.params.keys() != self._types._params[typeI].keys():
                self.params = dict(self._types._params[typeI])
            self.typeI = typeI
        return ret

    def typeIndex(self):
        return self.typeI
    def caption(self):
        typeI = self.typeI
        return self._types._typeCaptions[typeI] if typeI >= 0 \
          else _TR("(Select {0} Type)").format(self._name)
    def formatParams(self):
        typeI = self.typeI
        return self._types._paramTemplates[typeI].format(**self.params) if typeI >= 0 else ''
    def parseParams(self, userinput):
        return _parseStrToDict(userinput, self._types._paramTemplates[self.typeI], self.params) \
            if self.typeI >= 0 else False #and userinput else False
    def validate(self):
        ret = ""
        if self.typeI >= 0:
            try:
                if not eval(self._types._validationTemplates[self.typeI].format(**self.params)):
                    ret = _TR("<p>{0} <b>{1}</b> evaluation error: {2}!")\
                            .format(self._name, self.caption(),
                                    self._types._validationCaptions[self.typeI].format(**self.params))
            except Exception as e:
                ret = _TR("<p>{0} <b>{1}</b> format error: {2}!")\
                        .format(self._name, self.caption(), e)
        return ret


class Condition(_CodeFragment):
    _name = 'Condition'
    _types = conditionTypes
        
class Action(_CodeFragment):
    _name = 'Action'
    _types = actionTypes



######################   QT Table Models   #################################


class RulesModel(QAbstractTableModel):
    def __init__(self, scriptFileName, *args):
        QAbstractTableModel.__init__(self, *args)
        self._scriptFileName = scriptFileName
        self._rules = _Rules(_loadScript(scriptFileName))    # also set by setRawRules() method
        self._modified = False
        self._sourceRowForNextAdd = -1
        self.dataChanged.connect(self._dataModified) 
           
    def rowCount(self, parent = None):  # changed to allow parent as opt param
        return len(self._rules)
    def columnCount(self, parent):
        return 4
        
    def data(self, index, role):
        ret = None
        if index.isValid():
            row = index.row()
            if row in range(len(self._rules)):
                col = index.column()
                if col == 0 and (role == Qt.CheckStateRole or role == Qt.EditRole):
                    ret = Qt.Checked if self._rules[row].enabled else Qt.Unchecked
                elif col == 1 and (role == Qt.DisplayRole or role == Qt.EditRole):
                    ret = self._rules[row].name
                elif col == 2 and role == Qt.DisplayRole:
                    ret = '\n'.join([c.caption() + ': ' + c.formatParams() for c in self.ruleConditions(row)])
                elif col == 3 and role == Qt.DisplayRole:
                    ret = '\n'.join([a.caption() + ': ' + a.formatParams() for a in self.ruleActions(row)])
        return QVariant(ret)

    def headerData(self, section, orientation, role):
        ret = None
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                ret = self.tr("A")
            elif section == 1:
                ret = self.tr("Rule Name")
            elif section == 2:
                ret = self.tr("Conditions")
            elif section == 3:
                ret = self.tr("Actions")
        elif role == Qt.DisplayRole and orientation == Qt.Vertical:
            ret = self.tr(str(section + 1))
        return ret

    def insertRows(self, row, rows, parent):
        self.beginInsertRows(QModelIndex(), row, row + rows - 1)
        for _ in range(rows):
            if self._sourceRowForNextAdd == -1:
                newRule = _Rule()
            else:
                newRule = copy.deepcopy(self._rules[self._sourceRowForNextAdd])
                newRule.name += ' COPY'
            self._rules.insert(row, newRule)
        self._sourceRowForNextAdd = -1
        self.endInsertRows()
        return True
    def removeRows(self, row, rows, parent):
        self.beginRemoveRows(QModelIndex(), row, row + rows - 1)
        for _ in range(rows):
            self._rules.pop(row)
        self.endRemoveRows()
        return True
    
    def setData(self, index, value, role):
        ret = False
        if index.isValid():
            row = index.row()
            column = index.column()
            if column == 0 and (role == Qt.EditRole or role == Qt.CheckStateRole):
                self._rules[row].enabled = value.toBool()
            elif column == 1 and role == Qt.EditRole:
                self._rules[row].name = value.toString()
            self.dataChanged.emit(index, index)
            ret = True
        return ret

    def flags(self, index):
        if index.isValid():
            ret = QAbstractTableModel.flags(self, index)
            ret = ret | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            column = index.column()
            if column in (0, 1):
                ret = ret | Qt.ItemIsEditable
            if column == 0:
                ret = ret | Qt.ItemIsUserCheckable
        else:
            ret = Qt.ItemIsEnabled
        return ret
    
    ####  helping methods  ####
    
    def moveRule(self, row, delta = 1):
        rowCnt = len(self._rules)  # == self.rowCount(0)
        if row in range(rowCnt) and row + delta in range(rowCnt):
            self.beginMoveRows(QModelIndex(), row, row, 
                               QModelIndex(), row + delta + (1 if delta > 0 else 0))
            tmp = self._rules.pop(row)
            self._rules.insert(row + delta, tmp)
            self.endMoveRows()
            self._dataModified()
    
    def _dataModified(self):
        self._modified = True
    def isModified(self):
        return self._modified
    def getRawRules(self):
        return self._rules
    def setRawRules(self, rawRules):
        self._rules = rawRules
    def ruleConditions(self, row):
        return self._rules[row].conditions
    def ruleActions(self, row):
        return self._rules[row].actions
    def setSourceRowForNextAdd(self, sourceRowForNextAdd):
        self._sourceRowForNextAdd = sourceRowForNextAdd
    def saveScript(self):
        _saveScript(self._scriptFileName, self._rules.luaCodeGen())
        
    
    
# base data table model class for ConditionsModel and ActionsModel
class _CodeFragsModel(QAbstractTableModel):
    def __init__(self, frags, fragClass, parent, *args): # parent is a rulesModel instance
        QAbstractTableModel.__init__(self, parent, *args)
        self._frags = frags
        self._fragClass = fragClass
        self.dataChanged.connect(parent._dataModified)
         
    def rowCount(self, parent = None):
        return len(self._frags)
    def columnCount(self, parent):
        return 2
        
    def data(self, index, role):
        ret = None
        if index.isValid():
            row = index.row()
            if row in range(len(self._frags)):
                col = index.column()
                frag = self._frags[row]
                if col == 0:
                    if role == Qt.DisplayRole:
                        ret = frag.caption()
                    elif role == Qt.EditRole:
                        ret = frag.typeIndex()
                elif col == 1 and role in (Qt.DisplayRole, Qt.EditRole):
                    ret = frag.formatParams()
        return QVariant(ret)

    def headerData(self, section, orientation, role):
        ret = None
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                ret = self.tr("{0} Type".format(self._fragClass._name))
            elif section == 1:
                ret = self.tr("{0} Type Values".format(self._fragClass._name))
        return ret

    def insertRows(self, row, rows, parent):
        self.beginInsertRows(QModelIndex(), row, row + rows - 1)
        for _ in range(rows):
            self._frags.insert(row, self._fragClass())
        self.endInsertRows()
        return True
    def removeRows(self, row, rows, parent):
        self.beginRemoveRows(QModelIndex(), row, row + rows - 1)
        for _ in range(rows):
            self._frags.pop(row)
        self.endRemoveRows()
        return True

    def setData(self, index, value, role):
        ret = False
        if index.isValid():
            row = index.row()
            column = index.column()
            if column == 0 and role == Qt.EditRole:
                ret = self._frags[row].setTypeIndex(value.toInt()[0], self._frags)
            elif column == 1 and role == Qt.EditRole:
                ret = self._frags[row].parseParams(str(value.toString()))   # toString() return QString
            self.dataChanged.emit(index, index)
        return ret

    def flags(self, index):
        if index.isValid():
            ret = QAbstractTableModel.flags(self, index)
            ret = ret | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            ret = Qt.ItemIsEnabled
        return ret
    

class ConditionsModel(_CodeFragsModel):
    def __init__(self, frags, parent, *args): # parent is a rulesModel instance
        _CodeFragsModel.__init__(self, frags, Condition, parent, *args)


class ActionsModel(_CodeFragsModel):
    def __init__(self, frags, parent, *args): # parent is a rulesModel instance
        _CodeFragsModel.__init__(self, frags, Action, parent, *args)


    
# helping function for to reverse the formatting operator (%)
from string import Formatter, punctuation
_parseStr = lambda x: x.isalpha() and x \
                    or x.isdigit() and int(x) \
                    or x.isalnum() and x \
                    or len(set(punctuation).intersection(x)) == 1 and x.count('.') == 1 and float(x) \
                    or x
def _parseStrToDict(inpStr, formatStr, valDict):
    # parse is converting formatStr into list of (prefix, field, format_spec, conversion) tuples
    # .. - one for each valDict key
    frags = []
    pos = 0
    for ffrag in Formatter().parse(formatStr):
        prefix, field, spec, _ = ffrag
        pos = inpStr.find(prefix, pos) + len(prefix)
        frags.append((prefix, field, spec, pos))
    for nI in range(len(frags) - 1):
        _, field, spec, pos = frags[nI]
        prefix2, _, _, pos2 = frags[nI + 1]
        val = inpStr[pos : pos2 - len(prefix2)]
        valDict[field] = val if 's' in spec else _parseStr(val)
    _, field, spec, pos = frags[-1]
    if field:
        val = inpStr[pos:]
        valDict[field] = val if 's' in spec else _parseStr(val)
    return True   


def _loadScript(fnam):
    if not os.path.isfile(fnam):
        _WARNING(_TR("The lua script {0} could not be found!").format(fnam))
        return
    if os.stat(fnam).st_size == 0:
        _WARNING(_TR("The lua script {0} is empty!").format(fnam))
        return
    ret = None
    fileObj = open(fnam, 'rb')
    try:
        hdr = fileObj.read(len(_HEADER_PREFIX))
        rest = fileObj.read()
        if hdr != _HEADER_PREFIX and hdr[-1] == '\r':   # file corrupted by Windows?
            hdr = hdr[:-1] + '\n'                       # .. repair Windows detection trap
            rest = rest[1:].replace(_LINESEP, '\n')     # .. and replace CrLf with Lf in pickle
        if hdr == _HEADER_PREFIX:
            pos = rest.find(_HEADER_SUFFIX)
            if pos >= 0:
                ret = rest[pos + len(_HEADER_SUFFIX):]
            else:
                _ERROR(_TR("Header suffix not found in lua script {0}.").format(fnam))
        else:
            _ERROR(_TR("Header prefix not found in lua script {0}.").format(fnam))
    except Exception as e:
        _ERROR(_TR("Error on opening lua script {0}: {1}").format(fnam, e))
    fileObj.close()
    return ret

def _saveScript(fnam, luaCode):
    fileObj = open(fnam, 'wb')
    try:
        fileObj.write(_HEADER_PREFIX)
        fileObj.write(_HEADER_SUFFIX)
        fileObj.write(luaCode)
    except Exception as e:
        _ERROR(_TR("Error on writing lua script {0}: {1}").format(fnam, e))
    fileObj.close()


def _loadCodeFragTypes(config, codeFragTypeClass):
    codeFragCount = config.getint('main', 'Num' + codeFragTypeClass._name + 's')
    if codeFragCount:                     # Conditions/Actions are specified within config - load/overwrite within class/type (either Condition or Action)
        # overwrite configurable class attributes (_luaTemplates, _validationTemplates, _typeCaptions, _isExclusives, _params, _paramTemplates, _validationCaptions, _luaTemplSupportedVersionss)
        for attr in [a for a in dir(codeFragTypeClass) if not a.startswith('__') and not a.startswith('_name')]:
            attrVals = []
            for nI in range(codeFragCount):
                attrVals.append(eval(config.get(codeFragTypeClass._name + str(nI), attr[1:-1])))
            setattr(codeFragTypeClass, attr, attrVals)
    return codeFragTypeClass()    



# public helper method for app init: types, data/script file handling and providing RulesModel for UI
def initTypesDataAndModel(fnam, config):
    # if .cfg exists then overwrite the both (single instance) code fragment type classes
    if config:                                
        conditionTypes = _loadCodeFragTypes(config, CondTypes)
        actionTypes = _loadCodeFragTypes(config, ActTypes)
    # return rules/root model instance
    return RulesModel(fnam)

        


#
#if __name__ == '__main__':
#    from modeltest import ModelTest
#    ModelTest(RulesModel, None)
#    ModelTest(ConditionsModel, None)
#    ModelTest(ActionsModel, None)
