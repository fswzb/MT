import time,datetime
from fractions import Fraction
import numpy
import pandas as pd
import talib
_oneday = 24*60*60
g_filterma = 30
now = time.strftime('%Y%m%d')
def convertdicttoexcel():
    security_history= {0: ['tradedate', 'secID', 'tradeprice', 26.737499999999997, -0.32289339915965737, 2.0411337887181817, -2.5623261492358362, 23.383333333333336, -0.6820693131674701, 1.504106462623688, -3.0984957290622948, 20.924999999999994, -0.95434602768030752, 1.5213469591190838, -3.1946500832917257, 21.912499999999998, -0.98601046501294776, 1.3332484201909509, -3.0467368662212992, 20.358333333333334, -1.8144454024084757, 0.1607384740107648, -3.5823195805660148]}

    indexs = ['tradedate','secID','tradeprice']
    i = 1
    while i <= 5:
        #make the table title
        added = ['T+%dOdds' %(i),'T+%dRet' %(i),'T+%d MaxProfit' %(i),'T+%dMaxLose' %(i)]
        indexs = indexs + added
        '''
        #caculate the average of return and odds
        g_security_history[0][4*i-1] = g_security_history[0][4*i-1]/g_number[i]# average odds
        g_security_history[0][4*i] = g_security_history[0][4*i]/g_number[i]#average return
        g_security_history[0][4*i+1] = g_security_history[0][4*i+1]/g_number[i]#average max profilt
        g_security_history[0][4*i+2] = g_security_history[0][4*i+2]/g_number[i]#average max lose
        '''
        i = i + 1
    data = pd.DataFrame.from_dict(data= security_history,orient='index')
    data.to_excel('龙回头模拟交易选时20150101-20151231-1.xlsx',header=indexs) 
    pass
def someday(_tradedate,howlong):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y%m%d'))+howlong*_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y%m%d',_tradedate)
    return _tradedate   

def CantBuy(data,i):
    if g_filterma == 0:
        return False
    if data['filterma%d' %g_filterma].iloc[i] == -321:
        return True
    elif data['filterma%d' %g_filterma].iloc[i] == -123:
        return False
    _date = data['tradedate'].iloc[i]
    _start = someday(_date,-100)
    _data = DataAPI.MktIdxdGet(beginDate=_start,endDate=someday(_date,-1),indexID='399317.ZICN',field=u'',pandas='1')
    _man_30 = _data['closeIndex'][-30:].mean()
    _man_10 = _data['closeIndex'][-10:].mean()
    _man_20 = _data['closeIndex'][-20:].mean()
    
    data['filterma%d' %g_filterma][i] = -321
    if _man_30 < _man_20 and _man_20 < _man_10:
        data['filterma%d'%g_filterma][i] = -123 #duo tou
        return False
    return True
     
def Outputhandle(filename):
    global Tquit
    R=[-0.08,-0.07,-0.06,-0.05,-0.04,-0.03,-0.02,-0.01]
    Tquit = []
    DictRMulti = {}
    excel = pd.read_excel(filename)
    #add filter to excel data
    if not 'filterma%d'%g_filterma in excel.columns:
        excel['filterma%d' %g_filterma] = range(len(excel))
    #excel = excel.transpose()
    for _r in R:
        DictRMulti[_r] = []
    _i = 0
    while _i < len(excel):
        Tquit.append(False)
        _i = _i+1

    for _r in R:
        _j = 1
        d = 0
        for e in range(len(Tquit)):
            Tquit[e] = False
        while _j <= 5:
            a,a0,a1,b,c,d,e,f = caculateRMulti(_j,_r,excel)
            print '初始风险%f，T+%d日平均总回报%f，最大平均回报%f，最小平均回报%f，最大回报%f，止损%f，交易次数%d,止损次数%d,赚钱交易次数%d'%(_r,_j,a,a0,a1,b,c,d,e,f)
            DictRMulti[_r] = DictRMulti[_r] + [a,a0,a1,b,c,e,f]
            _j = _j + 1 
        DictRMulti[_r].insert(0,d)
    _i = 1
    indexs=['交易次数']
    while _i <= 5:
        #make the table title
        added = ['T+%dRet' %(_i),'平均最低回报','平均最高回报','T+%dMaxProfit' %(_i),'T+%dMaxLose' %(_i),'触发停价','盈利']
        indexs = indexs + added
        _i = _i+1
    data = pd.DataFrame(DictRMulti,index=indexs)
    data.to_excel('RMulti-MA%d21-%s'%(g_filterma,filename))
    excel.to_excel(filename)
    pass
def caculateRMulti(n,r,data):
    _i = 1
    _TnMaxLose = 0.
    _TnMaxProfit = 0.
    _TnRet = 0.   
    _TnValid = 0
    _TnStop = 0
    _TnProfit = 0
    _TnMinRet = 0
    _TnMaxRet = 0
    while _i < len(data):
        if CantBuy(data,_i):
            _i = _i + 1
            continue
        _TnValid = _TnValid + 1
        Tquit[_i] = Tquit[_i] or data['T+%dMaxLose'%n][_i] <= r
        if Tquit[_i]:
            _TnMaxLose = _TnMaxLose + min([r,data['T+%dRet'%n][_i]])
            _TnStop = _TnStop + 1
            _TnRet = _TnRet + min([r,data['T+%dRet'%n][_i]])
            _TnMaxProfit = _TnMaxProfit + min([r,data['T+%dRet'%n][_i]])
        else:
            _TnMaxProfit = _TnMaxProfit + data['T+%d MaxProfit'%n][_i]
            _TnRet = _TnRet + data['T+%dRet'%n][_i]
            if data['T+%dRet'%n][_i] > 0:
                _TnProfit = _TnProfit + 1
        if _TnRet < _TnMinRet:
            _TnMinRet = _TnRet
        if _TnRet > _TnMaxRet:
            _TnMaxRet = _TnRet
        _i = _i + 1
    return _TnRet,_TnMinRet,_TnMaxRet,_TnMaxProfit,_TnMaxLose,_TnValid,_TnStop,_TnProfit

#Outputhandle('龙回头模拟交易20140101-20141231-1.xlsx')        

