import talib
import lib.lhtbuypoint as lts
reload(lts)
ma5f=5./4
ma10f=10./9
ma20f=20./19
def findcandidate(guci,_previousdate,_EMA=False,howlong=60,_enableprint=True):
    """
    计算龙回头股票均线和黄金分割位置
    Args:
        guci  (list): 候选股票列表
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
now = '20170428'
g_candidates = findcandidate(['000856.XSHE' ],now,False,60,True)
for k,v in g_candidates.iteritems():
    lts.plot_candidate(k[:6],v[1:],now)

