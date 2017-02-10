from datetime import datetime
import time
import pandas as pd
import lib.mymath
reload(lib.mymath)
# 开启缓存，当前Notebook所有DataAPI数据都会缓存
DataAPI.settings.cache_enabled = True
_oneday = 24*60*60
_numcandidate=128
now = time.strftime('%Y%m%d')
def Market(before,now,inID):
    data = DataAPI.MktIdxdGet(beginDate=before,endDate=now,indexID=inID,field=u'',pandas='1')
    count = len(data['closeIndex'])
    print data['tradeDate'].iloc[-1],
    print get_week_day(data['tradeDate'].iloc[-1])
    print "成交量%.1f(%.1f)"%((data['turnoverValue'].iloc[-1]/100000000.),((data['turnoverValue'].iloc[-1] - data['turnoverValue'].iloc[-2])/100000000.))
    print "30日均线%.2f%%"%((data['closeIndex'].iloc[-1]/data['closeIndex'][count-30:count].mean()-1)*100)
    pass

def lxztordt(data,date,zt):
    _lxzt={}
    _lxzt3={}
    for (k,v) in data.items():
        _history = DataAPI.MktEqudAdjGet(secID=k,endDate=date,isOpen=1,pandas='1')
        _len = len(_history)
        if(_len<4):
            continue        
        ct = _history['closePrice'][_len-1]
        ct_1 = _history['closePrice'][_len-2]
        ct_2 = _history['closePrice'][_len-3]
        ct_3 = _history['closePrice'][_len-4]
        if(_history['secShortName'][_len-1].find('S')>=0):
            if zt:
                maxper=1.05
            else:
                maxper=0.95
        else:
            if zt:
                maxper=1.1
            else:
                maxper = 0.9
        if (zt==False and ct_1 <= lib.mymath.rod(ct_2*maxper,2))\
        or (zt and ct_1 >= lib.mymath.rod(ct_2*maxper,2) and (_history['turnoverRate'][_len-2] > 0.03 or _history['highestPrice'][_len-2]-_history['lowestPrice'][_len-2] > 0)):
            _lxzt[k] = round(_history['turnoverRate'][len(_history)-2]+ _history['turnoverRate'][len(_history)-1],2)
            if (zt==False and ct_2<=lib.mymath.rod(ct_2*maxper,2))\
            or (zt and ct_2 >= lib.mymath.rod(ct_3*maxper,2)  and (_history['turnoverRate'][_len-3] > 0.03 or _history['highestPrice'][_len-3]-_history['lowestPrice'][_len-3] > 0)):
                _lxzt3[k] = round(_lxzt[k] + _history['turnoverRate'][len(_history)-3],2)
        if(abs(ct - _history['highestPrice'].max()) < _history['highestPrice'].max()*0.1):
            if k in _lxzt:
                _lxzt[k] = 'HM%.2f' %_lxzt[k]
            if k in _lxzt3:
                _lxzt3[k] = 'HM%.2f' %_lxzt3[k]
    return _lxzt,_lxzt3

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

def dailyReview(data):
    voldata = data.sort('turnoverRate',ascending=0)
    _ztgp = 0
    _dtgpdic = {}
    _df5gp = 0
    _zsdt = 0
    _lxzt = 0
    _zgp = 0
    _zsztdic = {}
    _iter = 0
    _volval = 0
    _negMarketValue_sum = 0
    _chg = 0.
    _highvolchance = 0.
    for index,row in voldata.iterrows():
        _iter = _iter+1
        chg = row['closePrice']-row['preClosePrice']
        chgmax = lib.mymath.rod(row['preClosePrice']*1.1,2)
        chgmin = lib.mymath.rod(row['preClosePrice']*0.9,2)
        chg_5 = lib.mymath.rod(row['preClosePrice']*0.95,2)
        chg5 = lib.mymath.rod(row['preClosePrice']*1.05,2)          
        if(chg > 0):
            _zgp = _zgp+1
            if chgmax <= row['closePrice']\
            or (chg5 <= row['closePrice'] and row['secShortName'].find('S')>=0):
                _ztgp = _ztgp+1
                if row['turnoverRate'] > 0.03 or row['highestPrice']-row['lowestPrice'] > 0:
                    _zsztdic[row['secID']] = row['turnoverRate']
        elif row['closePrice'] <= chg_5:
            _df5gp = _df5gp+1
            if chgmin == row['closePrice']\
            or (chg_5 == row['closePrice'] and row['secShortName'].find('S')>=0):
                _dtgpdic[row['secID']] = row['turnoverRate']
                if row['turnoverRate'] > 0.03 or row['highestPrice']-row['lowestPrice'] > 0:
                    _zsdt = _zsdt+1
        _volval = _volval + row['turnoverValue']
        _negMarketValue_sum = _negMarketValue_sum + row['negMarketValue']
        _chg = _chg + row['closePrice']/row['preClosePrice'] - 1
        if(_iter == _numcandidate):
            _highvolret = _chg/_iter
            _highvolchance = float(_zgp)/_iter
            _highvolval = _volval
            _highvolrate = _volval/_negMarketValue_sum
    return _chg/len(voldata),float(_zgp)/len(voldata),_highvolret,_highvolchance,_highvolval,_highvolval/_volval,_ztgp,_zsdt,_df5gp,_zsztdic,_highvolrate,_volval/_negMarketValue_sum,_dtgpdic


def MktequGet(_tradedate):
    while True:
        allgp = DataAPI.MktEqudAdjGet(tradeDate=_tradedate,secID=set_universe("A"),isOpen='1',pandas='1')
        if(len(allgp) == 0):
            _tradedate = yesterday(_tradedate)
        else:
            break        
    return _tradedate,allgp

def yesterdayztret(dic,date):
    z = 0.
    r = 0.
    today = someday(date,1)
    while True:
        ret = DataAPI.MktIdxdGet(tradeDate=today,indexID='399317.ZICN',pandas='1')
        if len(ret) == 0:
            today = someday(today,1)
        else:
            break
    for i in dic.keys():
        info = DataAPI.MktEqudAdjGet(tradeDate=today,secID=i,isOpen='1',pandas='1')
        if len(info) > 0:
            r = r + info['closePrice'][0]/info['preClosePrice'][0] - 1
        if len(info) > 0 and (info['closePrice'][0] > info['preClosePrice'][0]):
            z = z+1
    return r/len(dic),z/len(dic)

def dailyfp(now):
    now = someday(now,0)
    before = someday(now,-70)
    Market(before,now,['399317.ZICN'])
    #T日复盘
    _tradedate=now
    _tradedate,allgp = MktequGet(_tradedate)
    _nextdate = _tradedate
    _Tret,_Tchance,_Thighvolret,_Thchance,_Thighvolval,_Tratio,_Tzt,_Tzsdt,_Tdf5,_Tztdic,_Thturnrate,_Tturnrate,_Tdtdic = dailyReview(allgp)
    _lxzt,_lxzt3 = lxztordt(_Tztdic,_tradedate,True)
    _lxdt,_lxdt3 = lxztordt(_Tdtdic,_tradedate,False)
    #T-1日复盘
    _tradedate = yesterday(_tradedate)
    _tradedate,allgp = MktequGet(_tradedate)
    _T1ret,_T1chance,_T1highvolret,_T1hchance,_T1highvolval,_T1ratio,_T1zt,_T1zsdt,_T1df5,_T1ztdic,_T1hturnrate,_T1turnrate,_T1dtdic = dailyReview(allgp)
    print "高换手赚钱概率%.2f%%(收益%.2f%%)成交量%.1f(换手率%.2f%% 大盘换手率%.2f%%)"%(round(_Thchance,3)*100,round(_Thighvolret,3)*100,_Thighvolval/100000000.,_Thturnrate*100,_Tturnrate*100)
    print "赚钱概率%.2f%%(收益%.2f%%)"%(round(_Tchance,3)*100,round(_Tret,3)*100)
    print "真实涨跌停比 %d(%d):%d(%d)"%(len(_Tztdic),len(_Tztdic)-len(_T1ztdic),_Tzsdt,_Tzsdt-_T1zsdt)
    print "涨跌停比 %d(%d):%d(%d)"%(_Tzt,_Tzt-_T1zt,len(_Tdtdic),len(_Tdtdic)-len(_T1dtdic))
    print "跌幅超5股票 %d(%d)"%(_Tdf5,_Tdf5-_T1df5)
    if len(_lxdt) > 0:
        print "连续跌停 %d %s"%(len(_lxdt),_lxdt)
    if len(_lxdt3) > 0:
        print "连续3跌停 %d %s"%(len(_lxdt3),_lxdt3)
    _T1ztret,_T1ztchance = yesterdayztret(_T1ztdic,_tradedate)#昨日涨停赚钱效应
    print "昨日涨停赚钱概率%.2f%%(收益%.2f%%)"%(round(_T1ztchance,3)*100,round(_T1ztret,3)*100)
    if len(_lxzt) > 0:
        print "2连板股票 %d %s"%(len(_lxzt),_lxzt)
    if len(_lxzt3) > 0:
        print "3连板股票 %d %s"%(len(_lxzt3),_lxzt3)
    return _nextdate
#main()
i = 20
#now = '20101231'
while True:
    if(is_weekend(now) == True):
        now = yesterday(now)
        continue
    now = dailyfp(now)
    now = yesterday(now)
    i = i -1
    if(i==0):
        break
