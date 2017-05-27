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
def convertdicttoexcel():
    security_history= {}
    indexs = security_history[0][:3]
    i = 1
    while i <= 5:
        #make the table title
        added = ['T+%dOdds' %(i),'T+%dRet' %(i),'T+%d MaxProfit' %(i),'T+%dMaxLose' %(i),'T+%dOpenret' %(i),'T+%dCloseret' %(i)]
        indexs = indexs + added
        i = i + 1
    tradedates = [v[0] for k,v in security_history.items()]
    print security_history
    print tradedates[1],tradedates[-1],indexs[2][-1]
    data = pd.DataFrame.from_dict(data= security_history,orient='index')
    data.to_excel(u'龙回头模拟交易%s-%s-%s.xlsx'%(tradedates[1],tradedates[-1],indexs[2][-1]),header=indexs) 
    pass
#convertdicttoexcel()
dateindex = []
def format_date(x,pos=None):
    thisind = numpy.clip(int(x+0.5), 0, len(dateindex)-1)
    return dateindex[thisind]
def plotret(odds,rets):
    sum = index = 0
    odds_his=[]
    for x in odds:
        sum = sum + x
        index = index + 1.
        odds_his.append(sum/index)
    sum = 0
    rets_his=[]
    for x in rets:
        sum = sum + x
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
        sum = 0.
        for e in translice:
            sum = sum + e
            if sum < summin:
                sumstartindex = i
                summin = sum
    return summin,sumstartindex
    
#his_5 = pd.read_excel('龙回头模拟交易实际交易.xlsx')
his_5 = pd.read_excel('龙回头模拟交易V120160101-20170526-EMA-2.xlsx')
#add one row for ending row
his_5.loc[len(his_5)] =his_5.irow(0)
#check the last 30 trancations
his_5 = his_5[-60:]
his_5.index = range(0,len(his_5))

#list_5 = filterhis(his_5,'T+1Closeret',True)
#list_5 = filterhis(his_5,'T+1MyRet',True)
#list_5 = filterhis(his_5,'T+1Ret',True)
list_5 = filterhis(his_5,'T+1Openret',True)
list_5_odds = filterhis(his_5,'T+1Odds',True)
print len((list_5)), (list_5)
dateindex = [e[0] for e in list_5]
l1 = [e[1] for e in list_5]
lodds = [e[1] for e in list_5_odds]
f,d = maxdown(l1)
print '最大回撤',f,list_5[d]
plotret(lodds,l1)
