
from CAL.PyCAL import font
import matplotlib.pyplot as plt
from matplotlib import gridspec
import time
import quartz
from quartz.api import *
import pandas as pd
import numpy as np
from datetime import datetime
from matplotlib import pylab
import copy
import talib
import lib.mymath as mymath
import lib.selstock_debug as xg
reload(mymath)
reload(xg)
g_security_return_value = ['T+%dOdds','T+%dRet','T+%dMaxProfit','T+%dMaxLose','T+%dOpenret' ,'T+%dCloseret']
g_head_indexs = ['tradedate','secID','tradeprice']
ma5f=5./4
ma10f=10./9
ma20f=20./19
_oneday = 24*60*60
g_security_history = {}
g_currnetdate = ''
now = time.strftime('%Y-%m-%d')
start = '20160101'  # 回测起始时间
end = now   # 回测结束时间
universe = set_universe('A') # 证券池，支持股票和基金
g_imaxback = 5 #最大回测天数 T+imaxback后的收益

def get_week_day(date):
    week_day_dict={0:'星期一',1:'星期二',2:'星期三',3:'星期四',4:'星期五',5:'星期六',6:'星期天'}
    if date.find('-') >=0:
        day = time.strptime(date,'%Y-%m-%d')
    else:
        day = time.strptime(date,'%Y%m%d')
    return week_day_dict[day.tm_wday]

def is_weekend(date):
    if date.find('-')>=0:
        day = time.strptime(date,'%Y-%m-%d')
    else:
        day = time.strptime(date,'%Y%m%d')
    return day.tm_wday == 5 or day.tm_wday == 6

def someday(_tradedate,howlong):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y-%m-%d'))+howlong*_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y-%m-%d',_tradedate)
    return _tradedate   

#if not bought before g_imaxback day 
# then we can buy the stock
def boughtbefore(s,date,his,interval=g_imaxback):
    _lastdate = date
    _i = len(g_security_history)-1
    while _i > 0:
        _e = g_security_history[_i]
        if _e[1].find(s) >=0:
            _lastdate = _e[0]
            break
        _i = _i - 1
    data = his[(his.tradeDate>=_lastdate)]
    data = data[(data.tradeDate <= date)]
    #最近几天没有买
    if (len(data) >= interval or _i == 0):
        return True
    return False

#计算股票连续涨停次数,根据不复权的数据
#return : [连续涨停次数，是否满足买入条件，买入价格]
def zt_findcandidate(_his,_Divhis,bzszt=False,turnrate=0.03):
    #股票除权数据
    _Divhis = _Divhis.set_index('exDivDate')
    _Divdate = '0000-00-00'
    for _date in _Divhis.index:
        if _date >= _his.index[0] and _date <= _his.index[-1]:
            _Divdate = _date#只考虑区间内有一次除权
            break      
    zt,bzt_lastday = howmanyzt(_his[:-1],_Divdate,bzszt,turnrate)
    bcanbuy,price = canbuy(_his.iloc[-1],_Divdate)
    return [zt,bcanbuy and bzt_lastday,price]

def canbuy(_dayTran,_Divdate):
    #除权单天的开盘价除权
    if _dayTran['tradeDate'] == _Divdate:
        _closep = AdjP(_Divhis,_Divdate,_dayTran['actPreClosePrice'])
    else:
        _closep = _dayTran['actPreClosePrice']

    #T 天开盘价是否小于涨停价
    if _dayTran['openPrice'] < mymath.rod(_closep*1.1,2):
        bcanbuy = True
        targetprice = _dayTran['openPrice']*_dayTran['accumAdjFactor']
        return bcanbuy,targetprice
    return False,0

def howmanyzt(_his,_Divdate,bzszt=False,turnrate=0.03):
    bzt_T = False
    #不除权历史数据
    _his = _his.set_index('tradeDate')
    #计算区间内涨停情况
    i = 0
    zt = 0
    previouszt = 0
    _closep = 0
    previousztdate = '0000-00-00'
    while True:
        #除权单天的开盘价除权
        if _his.index[i+1] == _Divdate:
            _closep = AdjP(_Divhis,_Divdate,_his['closePrice'].iloc[i])
        else:
            _closep = _his['closePrice'].iloc[i]
            
        if _his['closePrice'].iloc[i+1] == mymath.rod(_closep*1.1,2):
            #T 天是否涨停
            if i == len(_his)-2:
                if bzszt == False:
                    bzt_T = True
                elif _his['turnoverRate'].iloc[i+1] >= turnrate or _his['openPrice'].iloc[i+1] != _his['closePrice'].iloc[i+1]:
                    bzt_T = True
           
            #除权日前涨停价格除权
            if previousztdate < _Divdate and _his.index[i+1] >= _Divdate:
                previouszt = AdjP(_Divhis,_Divdate,previouszt)
            if _his['closePrice'].iloc[i+1] >= previouszt:
                zt = zt + 1
                previouszt = _his['closePrice'].iloc[i+1]
                previousztdate = _his.index[i+1]
        i = i + 1
        if i > len(_his)-2:
            break
    return zt,bzt_T

def AdjP(_Divhis,_Divdate,p):
    if np.isnan(_Divhis['perCashDiv'].loc[_Divdate]) == False:
        p = p - _Divhis['perCashDiv'].loc[_Divdate]
    _div = 1.
    if np.isnan(_Divhis['perShareDivRatio'].loc[_Divdate]) == False:
        _div = _div + _Divhis['perShareDivRatio'].loc[_Divdate]
    if np.isnan(_Divhis['perShareTransRatio'].loc[_Divdate]) == False:
        _div = _div + _Divhis['perShareTransRatio'].loc[_Divdate]
    ap = p/_div
    return ap

def init():
    global g_security_history
    #init the fist element of g_security_history
    _val = copy.copy(g_head_indexs)
    i = len(g_security_return_value)*g_imaxback
    while i > 0:
        _val.append(0.)
        i = i - 1
    if(len(g_security_history) == 0):
        g_security_history[len(g_security_history)] = _val
    pass

start='20160930'
continueday = start
now=someday(now,-2)
init()
for s in universe:
    #非复权历史数据
    _his = DataAPI.MktEqudGet(beginDate=start,endDate=now,secID=s,isOpen=1,field=['tradeDate','closePrice','openPrice','highestPrice','lowestPrice','accumAdjFactor','actPreClosePrice','turnoverRate'],pandas='1')
    #历史除权信息
    _Divhis = DataAPI.EquDivGet(secID=s,eventProcessCD='6',field=['exDivDate','perShareDivRatio','perShareTransRatio','perCashDiv'],pandas="1")
    #遍历历史数据
    for id in range(20,len(_his)):
        g_currentdate = _his['tradeDate'].iloc[id]
        accumAdjFactor = _his['accumAdjFactor'].iloc[id]
        #选股，卖入
        value = zt_findcandidate(_his[id-20:id+1],_Divhis)
        if value[0] > 1 and value[1] and boughtbefore(s,g_currentdate,_his[id-20:id+1],3):
            _val =[g_currentdate,s,value[2]]
            i = len(g_security_return_value)*g_imaxback
            while i > 0:
                _val.append(0.)
                i = i - 1
            g_security_history[len(g_security_history)] = _val
        #计算之前买入股票目前收益
        #1.当天卖出的盈利概率 2.当天卖出的盈利百分比 
        i = len(g_security_history) - 1
        while i >0:
            v = g_security_history[i]
            if v[0] == g_currentdate or v[1] != s:#ignore the current day and not the same stock
                i = i -1
                continue
            _parthis = _his[(_his.tradeDate > v[0])]
            _parthis = _parthis[(_parthis.tradeDate <= g_currentdate)]
            difflist = len(_parthis)
            #only test T+g_imaxback
            if difflist > g_imaxback:
                break
            #T-i日买入的股票当天收益
            interval = len(g_security_return_value)*(difflist-1)+len(g_head_indexs)
            #first reset the sum
            g_security_history[0][interval]=g_security_history[0][interval] - v[interval]
            g_security_history[0][interval+1]=g_security_history[0][interval+1] - v[interval+1]
            g_security_history[0][interval+2]=g_security_history[0][interval+2] - v[interval+2]
            g_security_history[0][interval+3]=g_security_history[0][interval+3] - v[interval+3]
            g_security_history[0][interval+4]=g_security_history[0][interval+4] - v[interval+4]
            g_security_history[0][interval+5]=g_security_history[0][interval+5] - v[interval+5]

            #caculate T+1 return
            v[interval+2] = accumAdjFactor*_his['highestPrice'].iloc[id]/v[2]-1#the max possible profit
            v[interval+3] = accumAdjFactor*_his['lowestPrice'].iloc[id]/v[2]-1#the max possible lose
            v[interval+4] = accumAdjFactor*_his['openPrice'].iloc[id]/v[2]-1#the open price profit
            v[interval+5] = accumAdjFactor*_his['closePrice'].iloc[id]/v[2]-1#the close price profit
            v[interval+1] = (v[interval+2]+v[interval+3]+v[interval+4]+v[interval+5])/4#the return
            if v[interval+1] > 0:
                v[interval] = 1.#the odds
            else:
                v[interval] = 0        

            g_security_history[0][interval]=g_security_history[0][interval] + v[interval]
            g_security_history[0][interval+1]=g_security_history[0][interval+1] + v[interval+1]
            g_security_history[0][interval+2]=g_security_history[0][interval+2] + v[interval+2]
            g_security_history[0][interval+3]=g_security_history[0][interval+3] + v[interval+3]
            g_security_history[0][interval+4]=g_security_history[0][interval+4] + v[interval+4]
            g_security_history[0][interval+5]=g_security_history[0][interval+5] + v[interval+5]
            i = i - 1
        #endof while i >0:
    #endof for id in range(20,len(_his)):
#endof for s in universe:
indexs = copy.copy(g_head_indexs)
i = 1
while i <= g_imaxback:
    #make the table title
    added = [x %(i) for x in g_security_return_value]
    indexs = indexs + added
    i = i + 1
data = pd.DataFrame.from_dict(data= g_security_history,orient='index')
data.to_excel('涨停股模拟交易%s-%s.xlsx' %(start,now),header=indexs)  

print 'len%d security_history %s' %(len(g_security_history),g_security_history)
