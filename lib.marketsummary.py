#lib.marketsummary
import lib.mymath as mymath
import numpy as np
reload(mymath)
def AdjP(_Divhis,_Divdate,p):
    accumAdj = False
    for b in _Divhis['exDivDate']:
        if b == _Divdate:
            accumAdj = True
            break
    if accumAdj == False:
        return p
    _divs = _Divhis.set_index('exDivDate')
    
    if np.isnan(_divs['perCashDiv'].loc[_Divdate]) == False:
        p = p - _divs['perCashDiv'].loc[_Divdate]
    _div = 1.
    if np.isnan(_divs['perShareDivRatio'].loc[_Divdate]) == False:
        _div = _div + _divs['perShareDivRatio'].loc[_Divdate]
    if np.isnan(_divs['perShareTransRatio'].loc[_Divdate]) == False:
        _div = _div + _divs['perShareTransRatio'].loc[_Divdate]
    ap = p/_div
    return ap

def lxztordt(gc,tradedate,zt=True,turnrate=0.03):
    """
    给定股票代码列表，计算连板数
    Args:
        gc (list): 需要计算连板的股票代码列表
        tradedate (string):计算时间
        turnrate (float):一字板确认真实涨停换手率标准
        zt (bool):计算涨停还是跌停
    Returns:
        dict (dictionary):key是连板数量，value是[[ticker,turnoverrate],[ticker,turnoverrate]....]

    Examples:
        >> lxztordt(['000425','600307','002307','000877'],'20170210')
        >> lxztordt(['000425.XSHE','600307.XSHG','002307','000877'],'20170210')
    """
    _his =[]
    _conbandict={}
    for s in gc:
        _continuebang = 0
        _continueturn = 0
        if s.find('.')>=0:
            _his = DataAPI.MktEqudGet(endDate=tradedate,secID=s,field=['tradeDate','secShortName','lowestPrice','closePrice','turnoverRate'],isOpen=1,pandas='1')
        else:
            _his = DataAPI.MktEqudGet(endDate=tradedate,ticker=s,field=['tradeDate','secShortName','lowestPrice','closePrice','turnoverRate'],isOpen=1,pandas='1')
        Divhis = DataAPI.EquDivGet(secID=s,eventProcessCD='6',field=['exDivDate','perShareDivRatio','perShareTransRatio','perCashDiv'],pandas="1")
        indexreverse = range(-1,-len(_his),-1)
        for ind in indexreverse:
            if(_his['secShortName'].iloc[ind].find('S')>=0):
                if zt:
                    maxinc=1.05
                else:
                    maxinc=0.95
            else:
                if zt:
                    maxinc=1.1
                else:
                    maxinc = 0.9
            if ind > indexreverse[-1]:
                _preclose = AdjP(Divhis,_his['tradeDate'].iloc[ind],_his['closePrice'].iloc[ind-1])
                if _his['closePrice'].iloc[ind] == mymath.rod(_preclose*maxinc,2):
                    _continuebang = _continuebang+1
                    _continueturn = _continueturn+_his['turnoverRate'].iloc[ind]
                    #如果是统计涨停，则需要检查是不是真实涨停,如果不是就不统计连板数
                    if zt and _his['lowestPrice'].iloc[ind] == _his['closePrice'].iloc[ind] and _his['turnoverRate'].iloc[ind] < turnrate:
                        _continuebang = _continuebang - 1
                        break
                else:
                    break#next security           
        if _continuebang == 0:
            continue
        #store to the dict
        if _continuebang in _conbandict:
            _conbandict[_continuebang].append([s,_continueturn])
        else:
            _conbandict[_continuebang] = [[s,_continueturn]]
    return _conbandict
#print lxztordt(['000425','600307','002307','000877'],'20170210')

def zfrankin(timeperiod,begindate,_tradedate,gc,x=0.5,turnrate=0.5,howlong=90):
    """
    计算股票涨幅排名

    Parameters
    ----------
    timeperiod (int): 统计排名区间
    begindate (string): 交易数据开始时间，最好取早于timeperiod的时间，给非交易日留点缓冲
    _tradedate (string): 统计结束时间
    gc (list): 要统计的股票列表
    x (float): 涨幅标准
    turnrate (float):区间还手率标准
    howlong (int): 次新股标准 
    Examples
    --------
        >> zfrankin(10,'20170101','20170208',['000877.XSHE','000001.XSHE'],x=0.5)
    Returns
    -------
    list : 涨幅大于X，交易日超过howlong的股票列表,[股票代码，区间最大涨幅，收盘与最高价回落，区间换手率]['000877',0.87,0.05,1.1]
    """
    allgp = DataAPI.MktEqudAdjGet(beginDate=begindate,endDate=_tradedate,secID=gc,isOpen='1',pandas='1')
    _highest = _turnrate = _ticker = 0
    _lowest = 99999999
    _zfdit ={}
    _tickertime = timeperiod
    _indexlist = sorted(allgp['ticker'].index,reverse=True)
    _ticker = allgp['ticker'].iloc[-1]
    _closePrice = allgp['closePrice'].iloc[-1]
    for _r in _indexlist:
        if _ticker != allgp.loc[_r]['ticker']:
            if(_turnrate > turnrate):
                _zfdit[_ticker]=[_ticker,_highest/_lowest-1.,_closePrice/_highest-1.,_turnrate]
            _ticker = allgp.loc[_r]['ticker']
            _highest=_turnrate=0
            _lowest=99999999
            _closePrice = allgp.loc[_r]['closePrice']
            _tickertime = timeperiod
        if _tickertime <= 0:
            continue
        if allgp.loc[_r]['highestPrice'] > _highest:
            _highest = allgp.loc[_r]['highestPrice']
            _lowest = allgp.loc[_r]['lowestPrice']# reset the lowest price 
            _turnrate = 0# reset the turnover rate
        _lowest = min(_lowest,allgp.loc[_r]['lowestPrice'])
        _turnrate = _turnrate + allgp.loc[_r]['turnoverRate']
        _tickertime = _tickertime - 1
    #handle the last security in gc
    if(_turnrate > turnrate):
        _zfdit[_ticker]=[_ticker,_highest/_lowest-1.,_closePrice/_highest-1.,_turnrate]
    
    zfranklist = [ v for v in sorted(_zfdit.values(),key=lambda x:x[1],reverse=True)]
    zfranklist = [j for (i,j) in enumerate(zfranklist) if j[1] >= x and len(DataAPI.MktEqudAdjGet(endDate=_tradedate,ticker=j[0],isOpen='1',pandas='1'))>howlong]
    return zfranklist
#zfrankin(20,'20170101','20170218',['000877.XSHE','000885.XSHE'],x=0.1)

