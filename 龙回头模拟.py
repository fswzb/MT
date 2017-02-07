'''
change log
2017-01-16
1. xuan gu biao zhun xiu gai, li shi hui ce biao xian bu hao
  a) 10 ri huan shou he zhang fu kao qian

2017 -01-15 13:36
1. test start 20070101, target price 1

2017-01-13 21:00
1. 150% in 7 days

2017-01-13
1.the highest price recently should be the max of an continuous up
2.exclude the new released stock lower 90 days
3.continue up and turnoverrate should greater 3%
4.now we can use target price 1,3,5

2017-01-11 22:26
1.revert the last change, 买点还是只按均线。双重标准回报很低。

2017-01-11 13:44
1.买点改进。黄金分割和均线最低。
    b）买入标准 g_targetprice，只能是2,4,6

2017-01-10 13:44
1.可以以上次生成的结果文件为起点继续运行，避免了重复,注意输入和当前模拟条件的匹配，最大回测时间，买入标准等
   模拟前，调用 continuefrom(filename)

2017-01-09 10:55
1.修改excel输出，行列互换

2017-01-08 17：49
1.修改一个bug，因为股票当天停牌造成的错误

2017-01-08 14：12
1.增加最大收益和最大亏损统计

2017-01-08 10：00
1.T日开盘9点半首先龙回头标准选股，然后如果T日股价低于龙回头买入价格标准并且T-g_imaxback日内没有买入过则买入:
    龙回头选股标准是：
    候选股池是最近10天平均换手排名前600
    a）连续n天内涨幅超一个标准:
        目前标准是连续7天涨幅超40%
    b）T日的股价有可能破T日的均线价格:
        目前标准是T日的跌停价小于T日均线价格。T-1日股价大于T-1日的均线价格
    c）更大均线的趋势向上:
        目前的标准是如果标准是5日均线价格买入的时候，10日均线应该是向上，如果10日均线价格买入的时候，20日均线价格向上。这个标准也可以变，比如统一用30日均线为标准。
    d）近期的价格高点不小于T-m日，当前价格离最高点不超过m个交易日:
        目前m的标准是，如果是5日均线买入，则不超过T-5，10日均线不超过T-10，20日均线买入不超过T-20
    e) 当日换手率排名靠前的股票，目前标准是前600，A股的20%。
2.T日遍历T日前已经买入的股票，计算收益率，赚钱概率。
    a）收益率的计算是把头寸分成240份每分钟以当前价格卖出一份股票，直到收盘卖完的平均收益率。
    b）赚钱概率是每分钟当前卖出价格高于买入价格的次数除以240。
3.可调参数
    a）最大回测统计时间 g_imaxback, 例如 5 表示T日买入后，最大统计T+5日的赚钱概率和收益   
    b）买入标准 g_targetprice，买入标准现在支持5，10，20日均线买入  
    c）start/end 统计时间段
4.输出龙回头模拟交易XXX.xlsx
'''
import time
import quartz
from quartz.api import *
import pandas as pd
import numpy as np
from datetime import datetime
from matplotlib import pylab
import copy
g_security_return_value = ['T+%dOdds','T+%dRet','T+%d MaxProfit','T+%dMaxLose','T+%dOpenret' ,'T+%dCloseret']
g_head_indexs = ['tradedate','secID','tradeprice']
_numcandidate=300
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
start = '20170101'  # 回测起始时间
end = now    # 回测结束时间
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
g_targetprice = 1#买入的价格，1，3，5对应黄金分割0.809，0.618，0.5。2，4，6对应5日10日20日均线价格


# round函数四舍五入
def rod(origin,n):
    rd = round(origin,n)
    ird = int(rd*10**(n+1))
    yu = 5
    origin = round(origin,n+1)
    diff = int(origin*10**(n+1)) - ird
    diff = diff - yu
    if  diff >= 0:
        rd = rd + 1./10**n
    return round(rd,n)

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

def ztcs(data):
    data = data.tolist()
    if len(data) < 2:
        return 0
    i = 0
    zt = 0
    previouszt = 0
    while True:
        if(data[i+1] == rod(data[i]*1.1,2) and data[i+1] >= previouszt):
            zt = zt + 1
            previouszt = data[i+1]
        i = i + 1
        if i > len(data)-2:
            break
    return zt

# period 涨幅连续统计时间，change，涨幅标准, return true or false, and how long after the max
def continueup(dataturnover,datalowest,datahighest,period,change):
    _ret = False
    _count = len(datalowest)
    _i = _count
    while _i >= period and period <= _count:
        _dataL = datalowest[_i-period:_i]
        _dataH = datahighest[_i-period:_i]
        _dataT = dataturnover[_i-period:_i]
        _max = _dataH.max()
        if(_dataH.iloc[-1] > _dataL.iloc[0] and _max/_dataL.min() > change and _dataT.mean() > 0.03):
            _ret = True
            return _ret,datahighest.index[-1] - _dataH[_dataH == _max].index[0]
        _i = _i - 1
    return _ret,_count #if go here, ret must be false


#target 1，3，5对应黄金分割0.809，0.618，0.5选股。2，4，6对应5日10日20日均线选股
def findcandidate(guci,_previousdate,target):
    stocks = {}
    for s in guci:
        _shis = DataAPI.MktEqudAdjGet(endDate=_previousdate,secID=s,isOpen=1,pandas='1')
        count = len(_shis)
        if(count< 90):#to caculdate the MA20 of 30 days need at lease 50 days transaction and also we don't cound new stock
            continue
        _closePrice = _shis['closePrice'][count-20:count]
        _lowestPrice = _shis['lowestPrice'][count-30:count]
        _highestPrice = _shis['highestPrice'][count-30:count]
        
        start = _lowestPrice.min()
        end   = _highestPrice.max()
        
        _closep = _closePrice.iloc[-1]
        if (end/start >= 1.5) \
        and (_closep < end) \
        and ztcs(_shis['closePrice'][count-30:count]) >= 3:      
            period = end - start
            golden5 = start + 0.5*period
            golden618 = start + 0.618*period
            golden8 = start + 0.809*period
            
            MA20 = _closePrice.mean()
            MA10 = _closePrice[-10:20].mean()
            MA5 = _closePrice[-5:20].mean()
            _closep5 = _closePrice.iloc[15]
            _closep10 = _closePrice.iloc[10]
            _closep20 = _closePrice.iloc[0]
            _ma5 = (MA5 - _closep5/5)*ma5f
            _ma10 = (MA10 - _closep10/10)*ma10f
            _ma20 = (MA20 - _closep20/20)*ma20f
            _closep30 = _shis['closePrice'].iloc[-30]
            MA30 = _shis['closePrice'][count-30:count].mean()
            #股价T日还在均线/golden上，T+1日可能破均线/golden,并且均线向上
            if target == 2 and _closep10 < MA10 and MA5 < _closep and _ma5 > _closep*0.9\
            or target == 4 and _closep20 < MA20 and MA10 < _closep and _ma10 > _closep*0.9\
            or target == 6 and _closep30 < MA30 and MA20 < _closep and _ma20 > _closep*0.9\
            or target == 1 and _closep10 < MA10 and golden8 < _closep and golden8 > _closep*0.9\
            or target == 3 and _closep20 < MA20 and golden618 < _closep and golden618 > _closep*0.9\
            or target == 5 and _closep30 < MA30 and golden5 < _closep and golden5 > _closep*0.9:

                #check if continously up
                _cup,_dam = continueup(_shis['turnoverRate'][count-30:count],_lowestPrice,_highestPrice,7,1.5)
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
                print '%s : %s' %(cl,value)
    return stocks

#if a) T day 没有停牌
#   b) T day(currentdate)'s lowest price below targetprice,
#   c) not bought before g_imaxback day 
# then we can buy the stock
def canbuy(s,targetprice,date):
    _lastdate = date
    _i = len(g_security_history)-1
    while _i > 0:
        _e = g_security_history[_i]
        if _e[1].find(s) >=0:
            _lastdate = _e[0]
            break
        _i = _i - 1
    data = DataAPI.MktEqudAdjGet(beginDate=_lastdate,endDate=date,secID=s,isOpen=1,pandas='1')
    if (len(data) >= g_imaxback+2 or len(data) ==1) and data['lowestPrice'].iloc[-1] <= targetprice:
        return True
    return False

def initialize(account): # 初始化虚拟账户状态
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
g_difflist = {} 
def handle_data(account): #在每个交易日开盘之前运行，用来执行策略，判断交易指令下达的时机和细节
    global g_candidates
    global g_security_history
    global g_currentdate
    global g_previousdate
    global g_difflist
    #每个交易日开始执行一次，计算当天的标的股票，然后看是否能买入，这需要知道当天的最低成交价，所以真实交易的时候不行
    if account.current_minute.find('09:30') >= 0:
        g_currentdate = account.current_date.strftime('%Y%m%d')
        g_previousdate = account.previous_date.strftime('%Y%m%d')
        g_candidates = findcandidate(account.universe,g_previousdate,g_targetprice)
        #try to buy the candidates
        for s,v in g_candidates.items():
            targetprice = v[g_targetprice]
            if canbuy(s,targetprice,g_currentdate):
                _val =[g_currentdate,s,min(targetprice,account.reference_price[s])]
                i = len(g_security_return_value)*g_imaxback
                while i > 0:
                    _val.append(0.)
                    i = i - 1
                g_security_history[len(g_security_history)] = _val
        #if g_currentdate[-2:].find('01')>=0 or g_currentdate[-2:].find('15')>=0:#every month
        print '%s %s' %(g_currentdate,get_week_day(g_currentdate))
        print 'security_history %s' %g_security_history
        
    #量化收益 T+n，假设手里的股票分成240份，每分钟卖出一份。1.当天卖出的盈利概率 2.当天卖出的盈利百分比 
    i = len(g_security_history) - 1
    while i >0:
        v = g_security_history[i]
        if(v[0].find(g_currentdate)>=0):#ignore the current day
            i = i -1
            continue
        if account.current_minute.find('09:30') >= 0:
            _his = DataAPI.MktEqudAdjGet(beginDate=v[0],endDate=g_currentdate,secID=v[1],isOpen='1',pandas='1')
            g_difflist[i]=len(_his)-1
            if len(_his) > 0 and _his['tradeDate'].iloc[-1].find(account.current_date.strftime('%Y-%m-%d')) < 0:#ting pai
                g_difflist[i] = 0
            
        if g_difflist[i] == 0:
            i = i -1
            continue
        if g_difflist[i] > g_imaxback:
            break
        #T-i日买入的股票当天收益
        interval = len(g_security_return_value)*(g_difflist[i]-1)+len(g_head_indexs)
        if account.reference_price[v[1]] > v[2]:
            v[interval] = v[interval]+1
        v[interval+1] = account.reference_price[v[1]]/v[2]-1 + v[interval+1]

        #at the end of a day, caculate the result
        if(account.current_minute.find('14:59')>=0):
            _his = DataAPI.MktEqudAdjGet(beginDate=g_currentdate,endDate=g_currentdate,secID=v[1],isOpen='1',pandas='1')
            v[interval] = v[interval]/g_ifreq#the odds
            v[interval+1] = v[interval+1]/g_ifreq#the return
            v[interval+2] = _his['highestPrice'][0]/v[2]-1#the max possible profit
            v[interval+3] = _his['lowestPrice'][0]/v[2]-1#the max possible lose
            v[interval+4] = _his['openPrice'][0]/v[2]-1#the open price profit
            v[interval+5] = _his['closePrice'][0]/v[2]-1#the close price profit
            g_security_history[0][interval]=g_security_history[0][interval] + v[interval]
            g_security_history[0][interval+1]=g_security_history[0][interval+1] + v[interval+1]
            g_security_history[0][interval+2]=g_security_history[0][interval+2] + v[interval+2]
            g_security_history[0][interval+3]=g_security_history[0][interval+3] + v[interval+3]
            g_security_history[0][interval+4]=g_security_history[0][interval+4] + v[interval+4]
            g_security_history[0][interval+5]=g_security_history[0][interval+5] + v[interval+5]
    
        i = i - 1
    return
def continuefrom(filename):
    excel = pd.read_excel(filename)
    _i = 0
    while _i < len(excel):
        g_security_history[_i] = excel.iloc[_i].tolist()
        _i=_i+1
    return excel['tradedate'].iloc[-1]
continueday = start
#continueday = someday(continuefrom('龙回头模拟交易选时20170101-20170111-1.xlsx'),1)
#print continueday

bt, perf =  quartz.backtest(start = continueday,end = end,benchmark = benchmark,universe = universe,capital_base = capital_base,initialize = initialize,handle_data = handle_data,refresh_rate = refresh_rate,freq = freq)

indexs = copy.copy(g_head_indexs)
i = 1
while i <= g_imaxback:
    #make the table title
    added = [x %(i) for x in g_security_return_value]
    print added
    indexs = indexs + added
    i = i + 1
data = pd.DataFrame.from_dict(data= g_security_history,orient='index')
data.to_excel('龙回头模拟交易%s-%s-%d.xlsx' %(start,end,g_targetprice),header=indexs)  

perf['cumulative_returns'].plot()
perf['benchmark_cumulative_returns'].plot()
pylab.legend(['current_strategy', 'HS300'])