# -*- coding: UTF-8 -*-
#optimize K graph, skip the dates when no trading
#for chinese font display

from CAL.PyCAL import font
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as madates
import matplotlib.finance as maf
from matplotlib import gridspec
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator
import time
import talib
g_oneday = 24*60*60
def MktDaPan():
    global _dptradedatelist
    global _dpEMA
    global _dfdp
    _dfdp = DataAPI.MktIdxdGet(beginDate='20151001',endDate='20170126',indexID='399317.ZICN',field=['tradeDate','closeIndex'],pandas='1')
    _dpEMA = talib.EMA(_dfdp['closeIndex'].values,timeperiod=30)
    _dptradedatelist = list(_dfdp['tradeDate'])
    _dptradedatelist =[(x.replace('-',''))  for x in _dptradedatelist]
    pass
MktDaPan()
def dpsituationat(thisdate):
    _inde = _dptradedatelist.index(thisdate)
    return _dfdp['closeIndex'].iloc[_inde] > _dpEMA[_inde]

def someday(_tradedate,howlong):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y%m%d'))+howlong*g_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y%m%d',_tradedate)
    return _tradedate   
#plot buy/sell point
def plotbsp(_period,security):
    dates = [x for i,x in enumerate(security['tradeDate']) if (security['action'].iloc[i]==u'证券买入')|(security['action'].iloc[i]==u'融资买入')]
    dates2ind = [_period.index(str(x)) for x in dates]
    prices = [x for i,x in enumerate(security['price'])  if (security['action'].iloc[i]==u'证券买入')|(security['action'].iloc[i]==u'融资买入')]
    plt.plot(dates2ind,prices,'ro')
    dates = [x for i,x in enumerate(security['tradeDate']) if security['action'].iloc[i]==u'证券卖出']
    dates2ind = [_period.index(str(x)) for x in dates]
    prices = [x for i,x in enumerate(security['price'])  if security['action'].iloc[i] ==u'证券卖出']
    plt.plot(dates2ind,prices,'go')
    return

def filter_trans(filename):
    data = pd.read_excel(filename)
    data = data[[u'成交日期',u'证券代码',u'证券名称',u'操作',u'成交均价',u'发生金额',u'成交数量']]
    data.columns = ['tradeDate','ticker','name','action','price','amount','volume']
    data = data[(data['action']==u'证券买入')|(data['action']==u'证券卖出')|(data['action']==u'融资买入')]
    return data

#按代码选取所有行，然后按买入，卖出切片，画出点图
def plot_security_his(data,security_name):
    security = data[data['ticker']==security_name]
    #reset figure for plot
    fig = plt.figure(figsize=(8,6))
    gs = gridspec.GridSpec(1,2,width_ratios=[3,1])
    ax0 = plt.subplot(gs[0])
    ax1 = plt.subplot(gs[1])
    plt.sca(ax0)
    plt.cla()
    #plot title
    ax0.set_title(u'%s%s 回报%f'%(security_name,security['name'].iloc[0],security['amount'].sum()),fontproperties=font,fontsize='16')
    #plot candlestick graph
    _period = plot_security_k(security_name,someday(str(security['tradeDate'].iloc[0]),0),someday(str(security['tradeDate'].iloc[-1]),2))
    _period =[(x.replace('-','')) for x in _period]
    plotbsp(_period,security)
    plt.grid() 
    plottranlog(ax1,security)
    plt.tight_layout()#to avoid the axis label is cut
    plt.show()
    plt.savefig('%s_his.svg'%(security_name))
    pass
#plot buy/sell log beside the K graph  
def plottranlog(ax1,security):
    plt.sca(ax1)
    plt.cla()
    plt.axis([0,10,0,10])
    _ts = security[['tradeDate','price','amount','volume']]
    _tstr = ''
    _tsvol = 0
    _tsbuy = 0
    _tsamount = 0
    _ret = 0.
    for ind, x in _ts.iterrows():
        _date = str(int(x['tradeDate']))
        _tstr = _tstr+_date+', '+str(x['price'])+', '+str(x['amount'])+'\n'
        _tsvol = _tsvol + int(x['volume'])
        _tsamount = _tsamount + float(x['amount'])
        if float(x['amount']) < 0.:
            _tsbuy = _tsbuy + float(x['amount'])
            if dpsituationat(_date):
                _tstr = _tstr + 'OK\n'
            else:
                _tstr = _tstr +'BAD\n'
        if _tsvol == 0:
            _ret = -_tsamount/_tsbuy
            _tstr = _tstr + 'return:%.2f%%\n'%(_ret*100)
            _ret = 0.
            _tsbuy = 0
            _tsamount = 0
    
    ax1.text(-2,10,_tstr,fontsize=8,ha='left',va='top')
    ax1.set_axis_off()
    return

#K线图
def format_date(x,pos=None):
    thisind = np.clip(int(x+0.5), 0, len(dfquotes[u'tradeDate'][_tickerstart:])-1)
    return dfquotes[u'tradeDate'][_tickerstart:].iloc[thisind]
#begin day is the firt day when buy the security
#end day is the last day when sell the security
def plot_security_k(security_name,begin,end):
    global dfquotes
    global _tickerstart
    dfquotes = mktgethis(security_name,someday(begin,-365),end)
    dfquotes = dfquotes[[u'tradeDate',u'openPrice',u'highestPrice',u'lowestPrice',u'closePrice']]
    _period =[(x.replace('-','')) for x in dfquotes['tradeDate']]
    _tickerstart = _period.index(begin)
    if _tickerstart > 20:
        _tickerstart = _tickerstart - 20
    else:
        _tickerstart = 0
    ax = plt.gca()
    lineandbars = maf.candlestick2_ohlc(ax,dfquotes[u'openPrice'][_tickerstart:].values,\
                          dfquotes[u'highestPrice'][_tickerstart:].values,\
                          dfquotes[u'lowestPrice'][_tickerstart:].values,\
                          dfquotes[u'closePrice'][_tickerstart:].values,\
                          colorup='r',colordown='g',width=0.5,alpha=1.0)
    #adjust the k graph's color
    lineandbars[1].set_edgecolor(lineandbars[1].get_facecolor())
    lineandbars[0].set_color(lineandbars[1].get_facecolor())
    _multilocator = int((len(_period)-_tickerstart)/40)#超过40个交易日，日期刻度单位加一天
    ax.xaxis.set_major_locator(MultipleLocator(1+_multilocator))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.gcf().autofmt_xdate()
    
    plotEMA([5,10,20,30],dfquotes[u'closePrice'].values,_tickerstart)
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(90)
    return _period[_tickerstart:]
#plot EMA
#input MAlist, for example [5,10,20]
def linecolor(num):
    _i = num%4
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
    
def mktgethis(security_name,begin,end):
    _dfquotes = DataAPI.MktEqudAdjGet(ticker=security_name,beginDate=begin,endDate=end,isOpen=1)
    if len(_dfquotes) == 0:
        _dfquotes = DataAPI.MktFunddGet(ticker=security_name,beginDate=begin,endDate=end)
    return _dfquotes
def analytictrans(filelist):
    _dataset = pd.concat([filter_trans(_file) for _file in filelist])
    _dataset = _dataset.sort_values(['tradeDate'])
    _dataset['index'] = range(len(_dataset))
    _dataset.set_index('index',inplace=True,drop=True)
    #iterate the stock id and all set to right format.
    for i in _dataset['ticker'].index:
        _dataset.set_value(i,'ticker',(6-len(str(_dataset['ticker'][i])))*'0'+str(_dataset['ticker'][i])) 
    _dataset.to_excel('test.xlsx')
    #make unique stock set
    security_list = _dataset.sort_values(['amount'])['ticker'].values
    security_set = []
    for x in security_list:
        if not x in security_set:
            security_set.append(x)
    print security_set
    print len(security_set)
    for stock in security_set:
        plot_security_his(_dataset,stock)    
    #plot_security_his(_dataset,'511880')        
    #plot_security_his(_dataset,'600984')    
    return

analytictrans(['20160204-0726.xlsx','20160727.xlsx','20160101-0725xy.xlsx','20160726xy.xlsx'])
