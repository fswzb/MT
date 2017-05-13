
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
import lib.selstock as xg
reload(lib.mymath)
reload(xg)
g_EMA = True
g_security_return_value = ['T+%dOdds','T+%dRet','T+%d MaxProfit','T+%dMaxLose','T+%dOpenret' ,'T+%dCloseret']
g_head_indexs = ['tradedate','secID','tradeprice']
_numcandidate=3000
purchased = {}
ma5f=5./4
ma10f=10./9
ma20f=20./19
_oneday = 24*60*60
g_candidates = {'000001.XSHE':'globalcandidates'}
g_security_history = {}
g_currnetdate = ''
g_previousdate = ''
now = time.strftime('%Y%m%d')
start = '20160101'  # 回测起始时间
end = now   # 回测结束时间
universe = DynamicUniverse('A').apply_filter(Factor.VOL10.nlarge(_numcandidate))#&Factor.REVS10.nlarge(_numcandiate)) #set_universe('A') # 证券池，支持股票和基金
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
    data = DataAPI.MktEqudAdjGet(beginDate=_lastdate,endDate=date,secID=s,isOpen=1,pandas='1')
    #停牌
    if len(data) == 0 or data['tradeDate'].iloc[-1].replace('-','').find(date) < 0:
        return False
    #最近几天没有买且股价满足条件
    if (len(data) >= interval or _i == 0) and data['lowestPrice'].iloc[-1] <= targetprice:
        return True
    return False

def continuefrom(filename):
    excel = pd.read_excel(filename)
    _i = 0
    while _i < len(excel):
        g_security_history[_i] = excel.iloc[_i].tolist()
        _i=_i+1
    return excel['tradedate'].iloc[-1]

def startsimulate(T_1day,_end):
#1.T-1日选股
    global g_candidates
    print T_1day,_end
    gc = universe.preview(T_1day,skip_halted=True)
    g_candidates = xg.findcandidate(gc,T_1day,g_targetprice,0.35,5,g_EMA,60,False,0.06)
    print g_candidates
#2.遍历交易日志文件，调用API获得T日分钟线计算T+n日股票收益
    for k,pos in g_security_history.items():
        if(pos[-6]==pos[-5]==pos[-4]==0):#T+5Odds，Ret，MaxProfit
            dfminutes = DataAPI.MktBarRTIntraDayGet(securityID=pos[1],startTime=u"",endTime=u"15:00",unit=u"",pandas="1")
            diffs = DataAPI.MktEqudAdjGet(beginDate=pos[0],endDate=_end,secID=pos[1],field='closePrice',isOpen='1',pandas='1')
            inter = len(diffs)-1
            if inter == 0\
            or inter > 5:
                continue
            print pos[0],pos[1],inter
            inters = 6*(inter-1)
            pos[3+inters] = sum([1.0 for item in dfminutes['closePrice'] if item > pos[2]])/len(dfminutes)#T+nOdds
            pos[4+inters] = dfminutes['closePrice'].mean()/pos[2]-1#T+nRet
            pos[5+inters] = dfminutes['closePrice'].max()/pos[2]-1#T+nMaxprofit
            pos[6+inters] = dfminutes['closePrice'].min()/pos[2]-1#T+nMinprofix
            pos[7+inters] = dfminutes['closePrice'].iloc[0]/pos[2]-1#T+nOpenRet
            pos[8+inters] = dfminutes['closePrice'].iloc[-1]/pos[2]-1#T+nCloseRet
            g_security_history[0][3+inters] += pos[3+inters]
            g_security_history[0][4+inters] += pos[4+inters] 
            g_security_history[0][5+inters] += pos[5+inters] 
            g_security_history[0][6+inters] += pos[6+inters] 
            g_security_history[0][7+inters] += pos[7+inters] 
            g_security_history[0][8+inters] += pos[8+inters] 

#3.T日线复盘，根据最低价和交易日志，确定T日买入股票
    for s,v in g_candidates.items():
        targetprice = round(v[g_targetprice],2)
        if canbuy(s,targetprice,_end,g_imaxback+2):
            _val =[g_currentdate,s,min(targetprice,dfminutes['closePrice'].iloc[0])]
            i = len(g_security_return_value)*g_imaxback
            while i > 0:
                _val.append(0.)
                i = i - 1
            g_security_history[len(g_security_history)] = _val
#4.T日选股
    gc = universe.preview(_end,skip_halted=True)
    g_candidates = xg.findcandidate(gc,_end,g_targetprice,0.35,5,g_EMA,60,False,0.06)
    if len(g_candidates)>0:
        print 'tomorrow candidate %s'%[k[:6] for k,v in g_candidates.items()]
#5.更新交易日志文件
    indexs = copy.copy(g_head_indexs)
    i = 1
    while i <= g_imaxback:
        #make the table title
        added = [x %(i) for x in g_security_return_value]
        indexs = indexs + added
        i = i + 1
    data = pd.DataFrame.from_dict(data= g_security_history,orient='index')
    if g_EMA:
        data.to_excel('龙回头模拟交易V1%s-%s-EMA-%d.xlsx' %(start,_end,g_targetprice),header=indexs)  
    else:
        data.to_excel('龙回头模拟交易V1%s-%s-%d.xlsx' %(start,_end,g_targetprice),header=indexs)  
    cansfiltered = {}
    for k,v in g_candidates.iteritems():#filter the candidates already bought before
        if canbuy(k,99999999.,_end,g_imaxback+1):
            cansfiltered[k]=v
    g_security_history.clear()
    return cansfiltered

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

start='20160101'
continueday = start
#print continueday
now=someday(now,0)
end=now
for i in range(2,3):
    continueday = someday(continuefrom('龙回头模拟交易V120160101-20170511-EMA-%d.xlsx'%i),0)
    continueday='20170511'
    g_targetprice = i
    g_candidates.clear()
    _list = (startsimulate(continueday,end))
    for k,v in _list.iteritems():
        plot_candidate(k[:6],v[1:])
