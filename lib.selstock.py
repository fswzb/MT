#coding=utf-8

#lib.selstock
import pandas as pd
import numpy as np
import talib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import lib.mymath as mymath
reload(mymath)
import matplotlib.dates as madates
import matplotlib.finance as maf
from matplotlib import gridspec
from matplotlib.ticker import MultipleLocator

#K线图
def format_date(x,pos=None):
    global dfqoutes
    global _tickerstart
    thisind = np.clip(int(x+0.5), 0, len(dfquotes[u'tradeDate'][_tickerstart:])-1)
    return dfquotes[u'tradeDate'][_tickerstart:].iloc[thisind]

def plot_volume_overlay(ax,_dfquotes,begin,_locatormulti=40):
    """
    plot volume bar with m5,10 line
    Args:
        _dfquotes (dataframe): the seurity dataframe which include'openPrice''closePrice''turnoverVol''tradeDate'
        ax : matplotlib ax object
        begin : the index of first volume bar, _dfquotes[begin:] will be plot
        _locatormulti (int): adjust the axis's ticker display interval
    Returns:
        lineandbars : return volume_overlay's lineandbars objects

    Examples:
        >> 
    """
    global _tickerstart
    global dfquotes
    dfquotes = _dfquotes
    _tickerstart = begin
    lineandbars = maf.volume_overlay(ax,dfquotes[u'openPrice'][_tickerstart:].values,\
                          dfquotes[u'closePrice'][_tickerstart:].values,\
                          dfquotes[u'turnoverVol'][_tickerstart:].values,\
                          colorup='r',colordown='g',width=0.5,alpha=1.0)
    lineandbars.set_edgecolor(lineandbars.get_facecolor())
    _multilocator = int((len(dfquotes)-_tickerstart)/_locatormulti)#超过40个交易日，日期刻度单位加一天
    ax.xaxis.set_major_locator(MultipleLocator(1+_multilocator))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.gcf().autofmt_xdate()
    _doublelist = [float(x) for x in dfquotes[u'turnoverVol'].values]
    _doublenparray = np.array(_doublelist)
    plotEMA([5,10],_doublenparray,_tickerstart)
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(90)
    return lineandbars

def plot_security_k(ax,_dfquotes,begin,_locatormulti=40):
    """
    plot k graph with ma5,10,20,30 line
    Args:
        _dfquotes (dataframe): the seurity dataframe which include'openPrice''closePrice''highestPrice''lowestPrice''tradeDate'
        ax : matplotlib ax object
        begin : the index of first k bar, _dfquotes[begin:] will be plot
        _locatormulti (int): adjust the axis's ticker display interval
    Returns:
        lineandbars : return candlestick2_ohlc's lineandbars objects

    Examples:
        >> 
    """
    global _tickerstart
    global dfquotes
    dfquotes = _dfquotes
    _tickerstart = begin
    lineandbars = maf.candlestick2_ohlc(ax,dfquotes[u'openPrice'][_tickerstart:].values,\
                          dfquotes[u'highestPrice'][_tickerstart:].values,\
                          dfquotes[u'lowestPrice'][_tickerstart:].values,\
                          dfquotes[u'closePrice'][_tickerstart:].values,\
                          colorup='r',colordown='g',width=0.5,alpha=1.0)
    #adjust the k graph's color
    lineandbars[1].set_edgecolor(lineandbars[1].get_facecolor())
    lineandbars[0].set_color(lineandbars[1].get_facecolor())
    _multilocator = int((len(dfquotes)-_tickerstart)/_locatormulti)#超过40个交易日，日期刻度单位加一天
    ax.xaxis.set_major_locator(MultipleLocator(1+_multilocator))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.gcf().autofmt_xdate()
    plotEMA([5,10,20,30],dfquotes[u'closePrice'].values,_tickerstart)
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(90)
    return lineandbars
#plot EMA
#input MAlist, for example [5,10,20]
def linecolor(num):
    _i = num%5
    if _i == 0:
        return 'r'
    elif _i == 1:
        return 'y'
    elif _i == 2:
        return 'k'
    elif _i == 3:
        return 'g'
    else:
        return 'b'
    pass
def plotEMA(malist,closearray,startticker):
    for _das in malist:
        _ema = talib.EMA(closearray,timeperiod=_das)
        plt.plot(_ema[startticker:],linecolor(malist.index(_das)))
''' 
fig = plt.figure(figsize=(8,6))
gs = gridspec.GridSpec(2,1,height_ratios=[4,1])
ax = plt.subplot(gs[0])
gs.update(left=0.05, right=0.48, hspace=0.0)
ax1 = plt.subplot(gs[1])
#fig,ax = plt.subplots()
gdfquotes = DataAPI.MktEqudAdjGet(ticker='600984',beginDate='20161101',endDate='20170218',field=['tradeDate','openPrice','highestPrice','lowestPrice','closePrice','turnoverVol'],isOpen=1)
fig.sca(ax)
plot_security_k(ax,gdfquotes,30)
fig.sca(ax1)
plot_volume_overlay(ax1,gdfquotes,30)
ax1.yaxis.set_visible(False)
plt.show()
'''
def format_percentage(y,pos=None):
    global dfquotes
    _ticklabel = mymath.rod(y/dfquotes['closePrice'].iloc[-1]-1,3)
    _per = '%.2f%%'%(_ticklabel*100)
    return _per

def plot_dragonpoint(ax1,_dfquotes,beginindex,targetprices,_imulti=40):
    """
    plot k graph with line of targetprices
    Args:
        _dfquotes (dataframe): the seurity dataframe which include'openPrice''closePrice''highestPrice''lowestPrice''tradeDate'
        ax1 : matplotlib ax object
        beginindex : the index of first k bar, _dfquotes[begin:] will be plot
        _locatormulti (int): adjust the axis's ticker display interval
    Returns:
        none

    Examples:
        >> 
    """
    global gdfquotes
    gdfquotes = _dfquotes
    plot_security_k(ax1,gdfquotes,beginindex,_locatormulti=_imulti)
    ax2 = ax1.twinx()
    ax2.set_ylim(ax1.get_ylim())
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_percentage))
    _zero = gdfquotes['closePrice'].iloc[-1]
    x1 = range(0,len(gdfquotes)-beginindex+1,len(gdfquotes)-beginindex)
    for _p in targetprices:
        y1 = [_p for n in x1]
        _percen = mymath.rod(_p/_zero-1,2)*100
        if _percen < 0 and _percen > -11:
            ax1.plot(x1,y1,'m--')
            ax1.text(targetprices.index(_p)*3,_p,'%.2f(%.2f%%)'%(mymath.rod(_p,2),_percen),rotation=90,va='bottom',color='m')
        else:
            ax1.plot(x1,y1,'b-')
            ax1.text(targetprices.index(_p)*3,_p,'%.2f(%.2f%%)'%(mymath.rod(_p,2),_percen),rotation=90,va='bottom')
        plt.minorticks_on()
    pass

'''
_gdfquotes = DataAPI.MktEqudAdjGet(ticker='000877',endDate='20170218',field=['tradeDate','openPrice','highestPrice','lowestPrice','closePrice'],isOpen=1)
_beginindex = max(len(_gdfquotes)-60,0)
fig, _ax1 = plt.subplots()
_targetprices = [_gdfquotes['closePrice'].iloc[-1],_gdfquotes['closePrice'].iloc[-1]*0.97]
plot_dragonpoint(_ax1,_gdfquotes,_beginindex,_targetprices)
'''
ma5f=5./4
ma10f=10./9
ma20f=20./19
# period 涨幅连续统计时间，change，涨幅标准, return true or false, and how long after the max
def continueup(dataturnover,datalowest,datahighest,period,change):
    _ret = False
    _len = len(dataturnover)
    _start = _len-1
    while _ret == False and _start-period >=0:
        _reverseindexs = range(_start,_start-period,-1)
        _count = _highest = 0
        _lowest = 9999999
        for _ir in _reverseindexs:
            if datahighest.iloc[_ir] > _highest:
                _highest = datahighest.iloc[_ir]
                _lowest = datalowest.iloc[_ir]
                _count = _len - _ir
            _lowest = min(_lowest,datalowest.iloc[_ir])
            if _highest/_lowest > change:
                _ret = True
                break
        _start = _start - 1
    return _ret,_count

def ztcs(data):
    data = data.tolist()
    if len(data) < 2:
        return 0
    i = 0
    zt = 0
    previouszt = 0
    while True:
        if(data[i+1] == mymath.rod(data[i]*1.1,2) and data[i+1] >= previouszt):
            zt = zt + 1
            previouszt = data[i+1]
        i = i + 1
        if i > len(data)-2:
            break
    return zt
#target 1，3，5对应黄金分割0.809，0.618，0.5选股。2，4，6对应5日10日20日均线选股
def findcandidate(guci,_previousdate,target,incr=0.5,duration=7,_EMA=False,howlong=60,_enableprint=True,turnrate=0.06):
    """
    选龙回头标的股
    Args:
        guci  (list): 候选股票列表
        target (int): 1，3，5对应黄金分割0.809，0.618，0.5选股。2，4，6对应5日10日20日均线选股
        incr  (float): 选股标准之，涨幅大小
        duration (int): 选股标准之,涨幅区间(时间段)
        _EMA (bool): 选股标准，均线是EMA还是MA
    Returns:
        list: 股票编码列表

    Examples:
    """
    stocks = {}
    for s in guci:
        _shis = DataAPI.MktEqudAdjGet(endDate=_previousdate,secID=s,isOpen=1,pandas='1')
        count = len(_shis)
        if(count< howlong):#to caculdate the MA20 of 30 days need at lease 50 days transaction and also we don't cound new stock
            continue
        _closePrice = _shis['closePrice'][count-20:count]
        _lowestPrice = _shis['lowestPrice'][count-30:count]
        _highestPrice = _shis['highestPrice'][count-30:count]
        
        start = _lowestPrice.min()
        end   = _highestPrice.max()
        
        _closep = _closePrice.iloc[-1]
        if (end/start-1 >= incr) \
        and (_closep < end) \
        and ztcs(_shis['closePrice'][count-30:count]) >= 3:      
            period = end - start
            golden5 = start + 0.5*period
            golden618 = start + 0.618*period
            golden8 = start + 0.809*period
            MA30l=MA20l=MA10l=MA5l=_ma5=_ma10=_ma20=0.
            if _EMA:
                MA30l = talib.EMA(_shis['closePrice'].values,timeperiod=30)
                MA20l = talib.EMA(_shis['closePrice'].values,timeperiod=20)
                MA10l = talib.EMA(_shis['closePrice'].values,timeperiod=10)
                MA5l = talib.EMA(_shis['closePrice'].values,timeperiod=5)
                _ma5 = MA5l[-1]
                _ma10 = MA10l[-1]
                _ma20 = MA20l[-1]
            else:
                MA30l = talib.MA(_shis['closePrice'].values,timeperiod=30)
                MA20l = talib.MA(_shis['closePrice'].values,timeperiod=20)
                MA10l = talib.MA(_shis['closePrice'].values,timeperiod=10)
                MA5l = talib.MA(_shis['closePrice'].values,timeperiod=5)
                _ma5 = (MA5l[-1] - _closePrice.iloc[15]/5)*ma5f
                _ma10 = (MA10l[-1] - _closePrice.iloc[10]/10)*ma10f
                _ma20 = (MA20l[-1] - _closePrice.iloc[0]/20)*ma20f
            MA5 = MA5l[-1]
            MA10 = MA10l[-1]
            MA20 = MA20l[-1]
            MA30 = MA30l[-1]
            _closep5 = MA5l[-5]
            _closep10 = MA10l[-5]
            _closep20 = MA20l[-5]
            _closep30 = MA30l[-5]
            #股价T日还在均线/golden上，T+1日可能破均线/golden,并且均线向上
            if target == 2 and _closep10 < MA10 and MA5 < _closep and _ma5 > _closep*0.9\
            or target == 4 and _closep20 < MA20 and MA10 < _closep and _ma10 > _closep*0.9\
            or target == 6 and _closep30 < MA30 and MA20 < _closep and _ma20 > _closep*0.9\
            or target == 1 and _closep10 < MA10 and golden8 < _closep and golden8 > _closep*0.9\
            or target == 3 and _closep20 < MA20 and golden618 < _closep and golden618 > _closep*0.9\
            or target == 5 and _closep30 < MA30 and golden5 < _closep and golden5 > _closep*0.9:

                #check if continously up
                _cup,_dam = continueup(_shis['turnoverRate'][count-30:count],_lowestPrice,_highestPrice,duration,1+incr)
                if(_cup == False):
                    continue
                #check how long after max
                _days = 5
                if(target == 3 or target == 4):
                    _days = 10
                elif(target == 5 or target == 6):
                    _days = 20
                if(_dam > _days ):
                    continue
                #turnover 
                st = max(0,count-_dam-duration)
                if _shis['turnoverRate'][st:count-_dam].mean() < turnrate:
                    continue
                #check if history max
                history = DataAPI.MktEqudAdjGet(beginDate='19991219',endDate=_previousdate,secID=s,isOpen=1,pandas='1')
                _hmax = history['highestPrice'].max()
                _ratio = _closep/_hmax-1.
                if abs(_ratio) < 0.1:
                    value = ["(HMAX)",golden8,_ma5,golden618,_ma10,golden5,_ma20]
                else:
                     value = ["(Norm)",golden8,_ma5,golden618,_ma10,golden5,_ma20]
                cl = s[0:6]+_shis['secShortName'][0]
                stocks[s] = value
                if _enableprint:
                    print '%s : %s' %(cl,value)
    return stocks
#findcandidate(['002651.XSHE','002300.XSHE'],'20170208',4)