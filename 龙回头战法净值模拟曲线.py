import time,datetime
from fractions import Fraction
import numpy
import pandas as pd
import talib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator
import lib.mymath as mymath
reload(mymath)
dateindex = []
def format_date(x,pos=None):
    thisind = numpy.clip(int(x+0.5), 0, len(dateindex)-1)
    return dateindex[thisind]
def plotjingzhi(odds,rets):
    sum = index = 0
    odds_his=[]
    for x in odds:
        sum = sum + x
        index = index + 1.
        odds_his.append(sum/index)
    sum = 1
    rets_his=[]
    for x in rets:
        sum = sum*(1+x*position)
        rets_his.append(sum)
    plt.figure(figsize=(12,9))
    ax = plt.subplot()
    oddleg, = plt.plot(odds_his,'b-',label='odds')
    retleg, =plt.plot(rets_his,'r--o',label='return')
    ylimit = (0,max(max(rets_his),max(odds_his)))
    ax.set_ylim(ylimit)
    _multilocator = len(rets)/40
    ax.xaxis.set_major_locator(MultipleLocator(1+_multilocator))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(90)
    plt.yticks(numpy.arange(-0.2,ylimit[1]+0.1,0.1))
    plt.grid()
    plt.legend(handles=[retleg,oddleg],loc="lower right")
    ax1 = ax.twinx()
    ax1.set_ylim(ylimit)
    plt.yticks(numpy.arange(-0.2,ylimit[1]+0.1,0.1))
    plt.show()
    pass
def filterhis(trancations,field,baverage):
    tradedate = ''
    retofdate = number = 0
    his = []
    #trancations['T+0ret']=numpy.arange(0,len(trancations),1.0)
    for i in trancations.index:
        if i == 0:
            tradedate=trancations['tradedate'][1]
            continue
        #closes = DataAPI.MktEqudAdjGet(secID=trancations['secID'][i],beginDate=trancations['tradedate'][i],endDate=trancations['tradedate'][i],field=['closePrice'],isOpen='1')
        #trancations['T+0ret'][i] = closes['closePrice'][0]/trancations['tradeprice'][i] - 1
        if tradedate.find(trancations['tradedate'][i])>=0:
            number = number + 1
            retofdate = trancations[field][i]+retofdate
        else:
            if baverage:
                retofdate = retofdate/number
                number = 1
            his.append([tradedate,retofdate])
            retofdate = trancations[field][i]
            tradedate = trancations['tradedate'][i]
    return his
def maxdown(trans):
    summin = 9999.
    for i in range(0,len(trans)):
        translice = trans[i:]
        sum = 1.
        for e in translice:
            sum = sum*(1+e*position)
            if sum < summin:
                sumstartindex = i
                summin = sum
    return summin,sumstartindex
#股票仓位
position=0.5   
#his_5 = pd.read_excel('龙回头模拟交易实际交易.xlsx')
#his_5 = pd.read_excel('龙回头模拟交易V120160101-20170721-EMA-2.xlsx')
his_5 = pd.read_excel('龙回头模拟交易快速版-3_20170101-2017-08-24.xlsx')
#check the last 30 trancations
#checkstandard='T+1Openret'
#checkstandard='T+1Closeret'
#checkstandard='T+1MyRet'
#checkstandard='T+1Ret'
checkstandard=u'5%,0.8TR,closeprice，止损6%'

his_5 = his_5[1:147]
his_5 = his_5[['tradedate','T+1Odds',checkstandard]]
his_5 = his_5.dropna(axis=0,how='any') 
his_5.index = range(0,len(his_5))

list_5 = filterhis(his_5,checkstandard,True)
list_5_odds = filterhis(his_5,'T+1Odds',True)
print len((list_5)), (list_5)
dateindex = [e[0] for e in list_5]
l1 = [e[1] for e in list_5]
lodds = [e[1] for e in list_5_odds]
f,d = maxdown(l1)
print '最大回撤',f-1,'最大回测日期',list_5[d]
plotjingzhi(lodds,l1)
