from CAL.PyCAL import font
import matplotlib.pyplot as plt
from matplotlib import gridspec
from datetime import datetime
import time
import pandas as pd
import lib.mymath
import lib.marketsummary as msum
import lib.selstock as xg
reload(xg)
reload(msum)
reload(lib.mymath)
# 开启缓存，当前Notebook所有DataAPI数据都会缓存
DataAPI.settings.cache_enabled = False

_oneday = 24*60*60
_numcandidate=128
now = time.strftime('%Y%m%d')
def Market(before,now,inID):
    data = DataAPI.MktIdxdGet(beginDate=before,endDate=now,indexID=inID,field=u'',pandas='1')
    count = len(data['closeIndex'])
    print data['tradeDate'].iloc[-1],
    print get_week_day(data['tradeDate'].iloc[-1])
    print "成交量%.1f(%.1f)5日平均%.1f"%((data['turnoverValue'].iloc[-1]/100000000.),((data['turnoverValue'].iloc[-1] - data['turnoverValue'].iloc[-2])/100000000.),(data['turnoverValue'][-5:].mean()/100000000.))\
    , "  30日均线:%.2f%%"%((data['closeIndex'].iloc[-1]/data['closeIndex'][count-30:count].mean()-1)*100)
    pass

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

def dailyReview(data):
    voldata = data.sort('turnoverRate',ascending=0)
    _dtgpdic = {}
    _zsztdic = {}
    _ztgp =_df5gp=_zsdt =_lxzt =_zgp=_iter=_volval=_negMarketValue_sum = 0
    _chg =_highvolchance = 0.
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
    allgp = DataAPI.MktEqudAdjGet(tradeDate=_tradedate,secID=set_universe("A"),isOpen='1',pandas='1')
    return allgp

def yesterdayztret(dic,date):
    z = 0.
    r = 0.
    today = date
    ret = DataAPI.MktIdxdGet(tradeDate=today,indexID='399317.ZICN',pandas='1')
    for i in dic.keys():
        info = DataAPI.MktEqudAdjGet(tradeDate=today,secID=i,isOpen='1',pandas='1')
        if len(info) > 0:
            r = r + info['closePrice'][0]/info['preClosePrice'][0] - 1
        if len(info) > 0 and (info['closePrice'][0] > info['preClosePrice'][0]):
            z = z+1
    return r/len(dic),z/len(dic)

def dailyfp(now,t1ztdic):
    now = someday(now,0)
    before = someday(now,-70)
    Market(before,now,['399317.ZICN'])
    #T日复盘
    _tradedate=now
    allgp = MktequGet(_tradedate)
    _Tret,_Tchance,_Thighvolret,_Thchance,_Thighvolval,_Tratio,_Tzt,_Tzsdt,_Tdf5,_Tztdic,_Thturnrate,_Tturnrate,_Tdtdic = dailyReview(allgp)
    _lxzt= msum.lxztordt(_Tztdic.keys(),_tradedate)
    _lxdt= msum.lxztordt(_Tdtdic.keys(),_tradedate,False)
    print "高换手赚钱概率%.2f%%(收益%.2f%%)成交量%.1f(换手率%.2f%% 大盘换手率%.2f%%)"%(round(_Thchance,3)*100,round(_Thighvolret,3)*100,_Thighvolval/100000000.,_Thturnrate*100,_Tturnrate*100)
    print "赚钱概率%.2f%%(收益%.2f%%)"%(round(_Tchance,3)*100,round(_Tret,3)*100)
    print "真实涨跌停比 %d:%d"%(len(_Tztdic),_Tzsdt)
    _retlxzt=[]
    for k,v in _lxzt.iteritems(): 
        if k > 1:
            _retlxzt = _retlxzt+v
            print "%d连板股票 %d %s"%(k,len(v),map(lambda x:[x[0][:6],'%.2f%%'%(round(x[1],3)*100)],v))
        else:
            print "真实涨停 %d %s"%(len(v),map(lambda x:[x[0][:6],'%.2f%%'%(round(x[1],3)*100)],v))
    for k,v in _lxdt.iteritems(): 
        if k > 1:
            print "连续%d个跌停股票 %d %s"%(k,len(v),map(lambda x:[x[0][:6],'%.2f%%'%(round(x[1],3)*100)],v))
        else:
            print "跌停股票 %d %s"%(len(v),map(lambda x:[x[0][:6],'%.2f%%'%(round(x[1],3)*100)],v)) 
    print "跌幅超5股票 %d"%(_Tdf5)
    if len(t1ztdic) != 0:
        _T1ztret,_T1ztchance = yesterdayztret(t1ztdic,_date)#昨日涨停赚钱效应
        print "昨日涨停赚钱概率%.2f%%(收益%.2f%%)"%(round(_T1ztchance,3)*100,round(_T1ztret,3)*100)
    return [_e[0] for _e in _retlxzt],_Tztdic,_Tdtdic


from collections import deque
gc2rank = deque(maxlen=300)
#now='20160229'
_his = DataAPI.MktIdxdGet(endDate=now,field=[u'secShortName','tradeDate','openIndex','highestIndex','lowestIndex','closeIndex','turnoverVol'],indexID='399317.ZICN')
_startIndex = 1#最近10个交易日
_T1ztdic={}
_T1dtdic={}
for _date in _his['tradeDate'][-_startIndex:].values:
    _date = _date.replace('-','')
    _lxztlist,_T1ztdic,_T1dtdic = dailyfp(_date,_T1ztdic)
    for _e in _lxztlist:
        gc2rank.append(_e)
    if len(gc2rank)>0:
        _temp = msum.zfrankin(20,someday(_date,-30*7/5),_date,list(gc2rank),x=0.4,turnrate=0.3)
        print "市场强势股涨幅排名: %s"%(map(lambda x:[x[0],'%.2f%%'%(round(x[1],3)*100),'%.2f%%'%(round(x[2],3)*100)],_temp))

#export excel
templist = _T1ztdic.keys()+_T1dtdic.keys()
df = DataAPI.MktEqudAdjGet(beginDate=_his['tradeDate'].iloc[-1],endDate=_his['tradeDate'].iloc[-1],secID=templist,field=['tradeDate','ticker','secID','secShortName','highestPrice'])
df[u'涨跌停次数']=range(0,len(df))
for i in df.index:
    if _T1ztdic.has_key(df['secID'][i]):
        dic = msum.lxztordt([df['secID'][i]],_his['tradeDate'].iloc[-1])
        if len(dic) == 1:
            df[u'涨跌停次数'][i]= dic.keys()[0]
        else:
            df[u'涨跌停次数'][i]= 1
    elif _T1dtdic.has_key(df['secID'][i]):
        dic = msum.lxztordt([df['secID'][i]],_his['tradeDate'].iloc[-1],False)
        if len(dic) == 1:
            df[u'涨跌停次数'][i]= -dic.keys()[0]
        else:
            df[u'涨跌停次数'][i]= -1

firstzt=range(0,len(df))
lastzt=range(0,len(df))
kbnumber=range(0,len(df))
kb=range(0,len(df))
for i in df.index:
    dfminutes = DataAPI.MktBarRTIntraDayGet(securityID=df['secID'][i],startTime=u"",endTime=u"15:00",unit=u"",pandas="1")
    firstzt[i] = ''
    lastzt[i] = ''
    kbnumber[i] = 0
    kb[i] = False
    for p in dfminutes.iterrows():
        if p[1]['closePrice'] != dfminutes['closePrice'].iloc[-1]:
            kb[i] = False
        elif kb[i] == False:
            kb[i] = True
            kbnumber[i] = kbnumber[i] + 1
            lastzt[i] = p[1]['barTime']
            if len(firstzt[i]) == 0:
                firstzt[i] = lastzt[i]
                kbnumber[i] = 0

cols = []
for i in range(0,len(df)):
    cols.append('%s封板开板%i次%s封死'%(firstzt[i],kbnumber[i],lastzt[i]))

df[u'涨跌停时间']=cols
del df['highestPrice']
del df['secID']
dfsort = df.sort_values([u'涨跌停次数', u'涨跌停时间'], ascending=[False, True])
dfsort.to_excel('dailyreview.xlsx')

#plot da pang K线图
fig = plt.figure(figsize=(12,9))
fig.set_size_inches(24,18)
gs = gridspec.GridSpec(2,1,height_ratios=[4,1])
_ax1 = plt.subplot(gs[0])
gs.update(left=0.05, right=0.48, hspace=0.0)
ax1 = plt.subplot(gs[1])
_his.columns =[u'secShortName','tradeDate','openPrice','highestPrice','lowestPrice','closePrice','turnoverVol']
_beginindex = max(len(_his)-120,0)
#_ax1.set_title('%s'%(_his['secShortName'].iloc[-1]),fontproperties=font,fontsize='16')
fig.sca(_ax1)
xg.plot_security_k(_ax1,_his,_beginindex,60) 
#成交量
fig.sca(ax1)
xg.plot_volume_overlay(ax1,_his,_beginindex)
ax1.yaxis.set_visible(False)
plt.show()

