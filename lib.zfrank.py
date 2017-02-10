#coding=utf-8

import pandas as pd

def findlastindexof(ticker,allgp,indexlist):
    for ind in indexlist:
        if allgp['ticker'][ind] == ticker:
            break
    return ind

def zfrankin(timeperiod,begindate,_tradedate,gc,x=0.5,howlong=90):
    """
    计算股票涨幅排名

    Parameters
    ----------
    timeperiod : 排名时间段
    begindate : 交易数据开始时间，最好取早于timeperiod的时间，给非交易日留点缓冲
    _tradedate : 统计结束时间
    gc : 要统计的股票列表
    x : 涨幅标准
    howlong : 次新股标准 
    Examples
    --------

    Returns
    -------
    list : 涨幅大于X，上市时间超过howlong的股票列表
    """
    allgp = DataAPI.MktEqudAdjGet(beginDate=begindate,endDate=_tradedate,secID=gc,isOpen='1',pandas='1')
    _highest = _turnrate = _ticker = 0
    _lowest = 99999999
    _zfdit ={}
    _ticker = allgp['ticker'].iloc[0]
    _indexlist = sorted(allgp['ticker'].index,reverse=True)
    _tickerlastindex = findlastindexof(_ticker,allgp,_indexlist)
    _tickertime = _tickerlastindex+1
    #print _ticker,_tickerlastindex,len(_indexlist)
    for _r in allgp.iterrows():
        if _ticker != _r[1]['ticker']:
            if(_turnrate > 1):
                _zfdit[_ticker]=[_ticker,_highest/_lowest-1.,_turnrate]
            _ticker = _r[1]['ticker']
            _highest=_turnrate=0
            _lowest=99999999
            _tickerlastindex = findlastindexof(_ticker,allgp,_indexlist)
            _tickertime = _tickerlastindex - _r[0]+1
        if _tickerlastindex - _r[0] > timeperiod:
            continue
        _highest = max(_highest,_r[1]['highestPrice'])
        _lowest = min(_lowest,_r[1]['lowestPrice'])
        _turnrate = _turnrate + _r[1]['turnoverRate']
    zfranklist = [ v for v in sorted(_zfdit.values(),key=lambda x:x[1],reverse=True)]
    zfranklist = [j for (i,j) in enumerate(zfranklist) if j[1] >= x and len(DataAPI.MktEqudAdjGet(endDate=_tradedate,ticker=j[0],isOpen='1',pandas='1'))>howlong]
    return zfranklist
#zfrankin(10,'20170101','20170208',['000001.XSHE','000002.XSHE'])