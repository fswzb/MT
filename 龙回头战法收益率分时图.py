'''
按天统计龙回头股票收益率分时图
'''
import talib as ta
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
import lib.selstock as xg
reload(mymath)
reload(xg)
g_EMA = True
g_security_return_value = ['T+%dOdds','T+%dRet','T+%d MaxProfit','T+%dMaxLose','T+%dOpenret' ,'T+%dCloseret']
g_head_indexs = ['tradedate','secID','tradeprice']
_numcandidate=1000
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
benchmark = 'HS300'    # 参考标准
universe = DynamicUniverse('A').apply_filter(Factor.VOL10.nlarge(_numcandidate))#&Factor.REVS10.nlarge(_numcandiate)) #set_universe('A') # 证券池，支持股票和基金
capital_base = 2000000  # 起始资金
refresh_rate = 1       # 调仓频率，即每 refresh_rate 个交易日执行一次 handle_data() 函数
freq = 'm'
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

def someday(_tradedate,howlong):
    _tradedate = time.mktime(time.strptime(_tradedate,'%Y%m%d'))+howlong*_oneday
    _tradedate = time.localtime(_tradedate)
    _tradedate = time.strftime('%Y%m%d',_tradedate)
    return _tradedate   

def initialize(account): # 初始化虚拟账户状态
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
g_vardic = {}
ticks = 0
def initgvardic():
    global g_security_history
    global g_vardic
    for k,v in g_security_history.items():
        g_vardic[k]={'checked':False,'fenshi':[],'soldpoint':[],'unit':3,'soldticks':[],'closeprice':0,'highestprice':0,'lowestprice':0,'cost':v[2]}
    pass
def handle_data(account): #在每个交易日开盘之前运行，用来执行策略，判断交易指令下达的时机和细节
    global g_vardic
    global ticks
    global g_security_history
    global g_currentdate
    ticks = ticks%g_ifreq
    if ticks ==  0:
        g_currentdate = account.current_date.strftime('%Y%m%d')
    for k,v in g_security_history.items():
        if g_vardic[k]['checked']:
            continue
        if ticks == 0:
            df = DataAPI.MktEqudAdjGet(beginDate=v[0],endDate=g_currentdate,secID=v[1],field=['accumAdjFactor','closePrice','highestPrice','lowestPrice'],isOpen='1',pandas='1')
            g_vardic[k]['before']=len(df)
            if g_vardic[k]['before'] == 2:
                g_vardic[k]['closeprice'] = df['closePrice'].iloc[0]
                g_vardic[k]['highestprice'] = df['highestPrice'].iloc[-1]
                g_vardic[k]['lowestprice'] = df['lowestPrice'].iloc[-1]
                g_vardic[k]['cost'] = g_vardic[k]['cost']*df['accumAdjFactor'].iloc[-1]
        if g_vardic[k]['before'] != 2:
            continue #only T+1 day
        g_vardic[k]['fenshi'].append(account.reference_price[v[1]])
        if ticks == 239:
            g_vardic[k]['checked']=True
               
    ticks = ticks+1
    return

def continuefrom(filename,_index=-1):
    excelfull = pd.read_excel(filename)
    excel = excelfull[(excelfull.tradedate == excelfull.iloc[_index]['tradedate'])]
    _i = 1
    while _i <= g_imaxback:
        excel['T+%dOpenret'%_i][0] = 0
        _i = _i + 1
    _i = 0
    g_security_history.clear()
    while _i < len(excel):
        g_security_history[_i] = excel.iloc[_i].tolist()
        _i=_i+1
    #print g_security_history
    initgvardic()
    return excel['tradedate'].iloc[0],someday(excel['tradedate'].iloc[0],5)

def startsimulate(_continueday,_end,_benchmark,_universe,_capital_base,_initialize,_handle_data,_refresh_rate,_freq):
    bt, perf,bt_by_account =  quartz.backtest(start = _continueday,end = _end,benchmark = _benchmark,universe = _universe,capital_base = _capital_base,initialize = _initialize,handle_data = _handle_data,refresh_rate = _refresh_rate,freq = _freq)
    pass
start='20170101'
continueday = start
#print continueday
end=someday(now,-1)
ax = plt.subplots()
recenttrancations = 3
for i in range(2,3):
    g_targetprice = i
    lastcontinue = lastend = '00000000'
    for j in range(-4,0):#回测最近n天收益率分时图
        continueday,end = continuefrom('龙回头模拟交易V120160101-20170725-EMA-2.xlsx',j)
        if lastcontinue != continueday and lastend != end:
            lastcontinue = continueday
            lastend = end
            print continueday,'买入第二天龙回头交易股票收益率分时'
            print [v[0] for k,v in g_security_history.iteritems()]
            startsimulate(continueday,end,benchmark,universe,capital_base,initialize,handle_data,refresh_rate,freq)
            sumret = []
            for n in range(0,240):
                sumr = 0
                for k,v in g_vardic.iteritems():
                    if(len(v['fenshi'])==0):
                        break
                    sumr = sumr + v['fenshi'][n]/v['cost']-1
                sumret.append(sumr)
            plt.title('return in time')
            plt.plot(sumret,'y-')
            plt.grid()
            plt.xlim(0,239)
            plt.xticks(range(0,240,15))
            print '最大收益:',max(sumret), " ",'最大收益卖出时机是开盘后:',sumret.index(max(sumret)),'分钟'
            #print sumret
            plt.show()
            plt.savefig('%d.svg'%(j))
        
