#coding=utf-8

#coding=utf-8

import pandas as pd
import numpy as np
import talib
import lib.mymath
reload(lib.mymath)

ma5f=5./4
ma10f=10./9
ma20f=20./19
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

def ztcs(data):
    data = data.tolist()
    if len(data) < 2:
        return 0
    i = 0
    zt = 0
    previouszt = 0
    while True:
        if(data[i+1] == lib.mymath.rod(data[i]*1.1,2) and data[i+1] >= previouszt):
            zt = zt + 1
            previouszt = data[i+1]
        i = i + 1
        if i > len(data)-2:
            break
    return zt
#target 1，3，5对应黄金分割0.809，0.618，0.5选股。2，4，6对应5日10日20日均线选股
def findcandidate(guci,_previousdate,target,incr=0.5,duration=7,_EMA=False):
    """
    给定股票代码转化为股票内部编码
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
        if(count< 90):#to caculdate the MA20 of 30 days need at lease 50 days transaction and also we don't cound new stock
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
            MA30=MA20=MA10=MA5=_ma5=_ma10=_ma20=0.
            _closep5 = _closePrice.iloc[15]
            _closep10 = _closePrice.iloc[10]
            _closep20 = _closePrice.iloc[0]
            _closep30 = _shis['closePrice'].iloc[-30]
            if _EMA:
                MA30 = talib.EMA(_shis['closePrice'].values,timeperiod=30)[-1]
                MA20 = talib.EMA(_shis['closePrice'].values,timeperiod=20)[-1]
                MA10 = talib.EMA(_shis['closePrice'].values,timeperiod=10)[-1]
                MA5 = talib.EMA(_shis['closePrice'].values,timeperiod=5)[-1]
                _ma5 = MA5
                _ma10 = MA10
                _ma20 = MA20
            else:
                MA20 = _closePrice.mean()
                MA10 = _closePrice[-10:20].mean()
                MA5 = _closePrice[-5:20].mean()
                _ma5 = (MA5 - _closep5/5)*ma5f
                _ma10 = (MA10 - _closep10/10)*ma10f
                _ma20 = (MA20 - _closep20/20)*ma20f
                MA30 = _shis['closePrice'][count-30:count].mean()
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
#findcandidate(['002651.XSHE','002300.XSHE'],'20170208',4)