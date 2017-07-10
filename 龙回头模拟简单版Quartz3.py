#1.Qartz3 backend
#2.Context.history() API 获取历史行情，比DataAPI接口更快。需要注意的是只能获取前复权行情，停牌期间的行情不会被过滤，而是会以停牌前的收盘价补齐，其余参数补零。
#3.回测频率以天计算，回测T+1日的收益，平均收益是开盘，收盘，最高，最低价的平均，概率是平均收益大于零算1.
#4.也可以回测T+4日，把1改为相应数字
#        #only test T+1
#        if g_difflist[i] > 1:
#            break
#5.Context.history() API 没有换手率，只有成交量和成交金额，所以选股标准换成平均成交金额1亿元。
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
import lib.mymath
import lib.selstock_debug as xg
reload(lib.mymath)
reload(xg)
g_EMA = True
g_security_return_value = ['T+%dOdds','T+%dRet','T+%dMaxProfit','T+%dMaxLose','T+%dOpenret' ,'T+%dCloseret']
g_head_indexs = ['tradedate','secID','tradeprice']
purchased = {}
ma5f=5./4
ma10f=10./9
ma20f=20./19
_oneday = 24*60*60
g_candidates = {}
g_security_history = {}
g_currnetdate = ''
g_previousdate = ''
now = time.strftime('%Y%m%d')
start = '20160101'  # 回测起始时间
end = now   # 回测结束时间
benchmark = 'HS300'    # 参考标准
universe = set_universe('A') # 证券池，支持股票和基金
refresh_rate = 1       # 调仓频率，即每 refresh_rate 个交易日执行一次 handle_data() 函数
freq = 'd'
accounts = {
    'stock_account':AccountConfig(account_type='security',capital_base=1000000)
}
max_history_window = 200

if freq == 'm':
    g_ifreq = 240
else:
    g_ifreq = 1
g_imaxback = 5 #最大回测天数 T+imaxback后的收益
g_targetprice = 3#买入的价格，1，3，5对应黄金分割0.809，0.618，0.5。2，4，6对应5日10日20日均线价格

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

def yesterday(_tradedate):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y%m%d'))-_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y%m%d',_tradedate)
    return _tradedate

def someday(_tradedate,howlong):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y%m%d'))+howlong*_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y%m%d',_tradedate)
    return _tradedate   

#if a) T day 没有停牌
#   b) T day(currentdate)'s lowest price below targetprice,
#   c) not bought before g_imaxback day 
# then we can buy the stock
def canbuy(s,targetprice,date,interval=g_imaxback):
    _lastdate = date
    _i = len(g_security_history)-1
    while _i > 0:
        _e = g_security_history[_i]
        if _e[1].find(s) >=0:
            _lastdate = _e[0]
            break
        _i = _i - 1
    data = DataAPI.MktEqudAdjGet(beginDate=_lastdate,endDate=date,secID=s,field=['tradeDate','openPrice','lowestPrice'],isOpen=1,pandas='1')
    #停牌
    if len(data) == 0 or data['tradeDate'].iloc[-1].replace('-','').find(date) < 0:
        return 0
    #最近几天没有买且股价满足条件
    if (len(data) >= interval or _i == 0) and data['lowestPrice'].iloc[-1] <= targetprice:
        return data['openPrice'].iloc[-1]
    return 0

def initialize(context): # 初始化虚拟账户状态
    global g_security_history
    #init the fist element of g_security_history
    _val = copy.copy(g_head_indexs)
    _val[2] = _val[2]+'-'+str(g_targetprice)
    i = len(g_security_return_value)*g_imaxback
    while i > 0:
        _val.append(0.)
        i = i - 1
    if(len(g_security_history) == 0):
        g_security_history[len(g_security_history)] = _val
    pass
g_difflist = {} 
def handle_data(context): #在每个交易日开盘之前运行，用来执行策略，判断交易指令下达的时机和细节
    global g_candidates
    global g_security_history
    global g_currentdate
    global g_previousdate
    global g_difflist
    bchanged = False
    #calculate T day candidate
    g_currentdate = context.current_date.strftime('%Y%m%d')
    g_previousdate = context.previous_date.strftime('%Y%m%d')
    print '%s %s' %(g_currentdate,get_week_day(g_currentdate))
    g_candidates.clear()
    for s in context.get_universe(exclude_halt=True):
        _his = context.history(symbol=s,attribute=['openPrice','closePrice','highPrice','lowPrice','turnoverValue'],time_range=max_history_window, freq='1d', style='sat', rtype='frame')
        _his = _his[s]
        _his['tradeDate'] = _his.index
        _his = _his[(_his.turnoverValue > 0)]
        _his.rename(columns={'openPrice':'openPrice','closePrice':'closePrice','highPrice':'highestPrice','lowPrice':'lowestPrice','turnoverValue':'turnoverRate'}, inplace = True)
        val = xg.findsinglecandidate(s,g_previousdate,_his,g_targetprice,0.35,5,g_EMA,60,False,100000000)
        if val:
            g_candidates[s]=val
            
    if len(g_candidates)>0:
        print 'todays candidate %d %s'%(len(g_candidates),[k[:6] for k,v in g_candidates.items()])
        
    #每个交易日开始执行一次，计算当天的标的股票，然后看是否能买入，这需要知道当天的最低成交价，所以真实交易的时候不行
    #try to buy the candidates
    for s,v in g_candidates.items():
        targetprice = round(v[g_targetprice],2)
        openprice = canbuy(s,targetprice,g_currentdate,g_imaxback+2)
        if openprice > 0:
            _val =[g_currentdate,s,min(targetprice,openprice)]
            i = len(g_security_return_value)*g_imaxback
            while i > 0:
                _val.append(0.)
                i = i - 1
            g_security_history[len(g_security_history)] = _val
            bchanged = True
        
    #量化收益 T+1。1.当天卖出的盈利概率 2.当天卖出的盈利百分比 
    i = len(g_security_history) - 1
    while i >0:
        v = g_security_history[i]
        if(v[0].find(g_currentdate)>=0):#ignore the current day
            i = i -1
            continue
        _his = DataAPI.MktEqudAdjGet(beginDate=v[0],endDate=g_currentdate,secID=v[1],field=['tradeDate','openPrice','closePrice','highestPrice','lowestPrice'],isOpen='1',pandas='1')
        g_difflist[i]=len(_his)-1
        if len(_his) > 0 and _his['tradeDate'].iloc[-1].find(context.current_date.strftime('%Y-%m-%d')) < 0:#ting pai
            g_difflist[i] = 0
            
        if g_difflist[i] == 0:
            i = i -1
            continue
        #only test T+1
        if g_difflist[i] > 1:
            break
        #T-i日买入的股票当天收益
        interval = len(g_security_return_value)*(g_difflist[i]-1)+len(g_head_indexs)
        #first reset the sum
        g_security_history[0][interval]=g_security_history[0][interval] - v[interval]
        g_security_history[0][interval+1]=g_security_history[0][interval+1] - v[interval+1]
        g_security_history[0][interval+2]=g_security_history[0][interval+2] - v[interval+2]
        g_security_history[0][interval+3]=g_security_history[0][interval+3] - v[interval+3]
        g_security_history[0][interval+4]=g_security_history[0][interval+4] - v[interval+4]
        g_security_history[0][interval+5]=g_security_history[0][interval+5] - v[interval+5]

        #caculate T+1 return
        v[interval+2] = _his['highestPrice'].iloc[-1]/v[2]-1#the max possible profit
        v[interval+3] = _his['lowestPrice'].iloc[-1]/v[2]-1#the max possible lose
        v[interval+4] = _his['openPrice'].iloc[-1]/v[2]-1#the open price profit
        v[interval+5] = _his['closePrice'].iloc[-1]/v[2]-1#the close price profit
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
        bchanged = True
    if bchanged:
        print 'len%d security_history %s' %(len(g_security_history),g_security_history)
    return
def continuefrom(filename):
    excel = pd.read_excel(filename)
    _i = 0
    while _i < len(excel):
        g_security_history[_i] = excel.iloc[_i].tolist()
        _i=_i+1
    return excel['tradedate'].iloc[-1]

def startsimulate(_continueday,_end,_benchmark,_universe,_initialize,_handle_data,_refresh_rate,_freq):
    bt, perf,bt_by_account  =  quartz.backtest(start = _continueday,end = _end,benchmark = _benchmark,universe = _universe,initialize = _initialize,handle_data = _handle_data,refresh_rate = _refresh_rate,freq = _freq,accounts =  accounts,max_history_window=max_history_window)
    indexs = copy.copy(g_head_indexs)
    i = 1
    while i <= g_imaxback:
        #make the table title
        added = [x %(i) for x in g_security_return_value]
        indexs = indexs + added
        i = i + 1
    data = pd.DataFrame.from_dict(data= g_security_history,orient='index')
    if g_EMA:
        data.to_excel('龙回头模拟交易SQT1%s-%s-EMA-%d.xlsx' %(start,_end,g_targetprice),header=indexs)  
    else:
        data.to_excel('龙回头模拟交易SQ%s-%s-%d.xlsx' %(start,_end,g_targetprice),header=indexs)  
    cansfiltered = {}
    for k,v in g_candidates.iteritems():#filter the candidates already bought before
        if canbuy(k,99999999.,_end,g_imaxback+1) > 0:
            cansfiltered[k]=v
    g_security_history.clear()
    return cansfiltered
    pass

def plot_candidate(s,lines):
    fig = plt.figure(figsize=(12,9))
    gs = gridspec.GridSpec(2,1,height_ratios=[4,1])
    _ax1 = plt.subplot(gs[0])
    gs.update(left=0.05, right=0.48, hspace=0.0)
    ax1 = plt.subplot(gs[1])
    _gdfquotes = DataAPI.MktEqudAdjGet(ticker=s,endDate=now,field=[u'secShortName','tradeDate','openPrice','highestPrice','lowestPrice','closePrice','turnoverVol'],isOpen=1)
    _beginindex = max(len(_gdfquotes)-60,0)
    print _gdfquotes[u'secShortName'].iloc[-1],v[0]
    _ax1.set_title(u'%s'%(k[:6]),fontproperties=font,fontsize='16')
    fig.sca(_ax1)
    xg.plot_dragonpoint(_ax1,_gdfquotes,_beginindex,lines,60) 
    #成交量
    fig.sca(ax1)
    xg.plot_volume_overlay(ax1,_gdfquotes,_beginindex)
    ax1.yaxis.set_visible(False)
    plt.show()

start='20161230'
continueday = start
#print continueday
now=someday(now,-2)
for i in range(2,3):
    #continueday = someday(continuefrom('龙回头模拟交易20170324-20170616-EMA-%d.xlsx'%i),0)
    #continueday='20170616'
    g_targetprice = i
    g_candidates.clear()
    _list = (startsimulate(continueday,now,benchmark,universe,initialize,handle_data,refresh_rate,freq))
    for k,v in _list.iteritems():
        plot_candidate(k[:6],v[1:])
