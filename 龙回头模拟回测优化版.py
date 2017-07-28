'''
1.API调用最小化
2.内存消耗减少
3.回测速度提高
4.回测调用方法，设定回测区间（start,now],设定回测开始日期continueday
'''
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
universe = set_universe('A') # 证券池，支持股票和基金
g_imaxback = 5 #最大回测天数 T+imaxback后的收益
g_targetprice = 2

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
    data = his.query("tradeDate>=@_lastdate & tradeDate<=@date")
    #最近几天没有买
    if (len(data) >= interval or _i == 0):
        return True
    return False

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

start='20160101'#历史数据开始时间
now='2017-07-21'#回测结束时间
continueday = '2017-01-01'#回测开始时间
init()
print start,now
for s in universe:
    #非复权历史数据
    _his = DataAPI.MktEqudGet(beginDate=start,endDate=now,secID=s,isOpen=1,field=['tradeDate','closePrice','openPrice','highestPrice','lowestPrice','accumAdjFactor','actPreClosePrice','turnoverRate'],pandas='1')
    #历史除权信息
    _Divhis = DataAPI.EquDivGet(secID=s,eventProcessCD='6',field=['exDivDate','perShareDivRatio','perShareTransRatio','perCashDiv'],pandas="1")
    value = []
    #遍历历史数据
    for id in range(20,len(_his)):
        g_currentdate = _his['tradeDate'].iloc[id]
        if g_currentdate < continueday:
            continue
        accumAdjFactor = _his['accumAdjFactor'].iloc[id]
        #买入
        if len(value) > 0 and boughtbefore(s,g_currentdate,_his[id-20:id+1],g_imaxback+2):
            targetprice = mymath.rod(value[g_targetprice],2)
            _lowestprice = mymath.rod(_his['lowestPrice'].iloc[id]*accumAdjFactor,2)
            if targetprice >= _lowestprice:
                _openprice = mymath.rod(_his['openPrice'].iloc[id]*accumAdjFactor,2)
                _val =[g_currentdate,s,min(targetprice,_openprice)]
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
            if difflist > 1:#g_imaxback:
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
        #为下一个交易日选股
        value = xg.findsinglecandidate(s,_his['tradeDate'].iloc[id],_his[id-59:id+1],2,0.35,5,True,60,False,0.06,_Divhis)
        #if len(value)>0 and boughtbefore(s,_his['tradeDate'].iloc[id],_his,g_imaxback+1):
            #print s,value
    #endof for id in range(20,len(_his)):
#endof for s in universe:
indexs = copy.copy(g_head_indexs)
i = 1
while i <= g_imaxback:
    #make the table title
    added = [x %(i) for x in g_security_return_value]
    indexs = indexs + added
    i = i + 1
g_security_history[0][0] = '0000-00-00'
data = pd.DataFrame.from_dict(data= g_security_history,orient='index')
data.to_excel('龙回头模拟交易快速版%s-%s.xlsx' %(start,now),header=indexs)  

print 'len%d security_history %s' %(len(g_security_history),g_security_history[0])
