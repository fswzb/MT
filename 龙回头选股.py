import lib.testfulllib as xg
reload(xg)
from CAL.PyCAL import font
import matplotlib.pyplot as plt
import time
now = time.strftime('%Y%m%d')
universe = DynamicUniverse('A').apply_filter(Factor.VOL10.nlarge(300))#&Factor.REVS10.nlarge(_numcandiate)) #set_universe('A') # 证券池，支持股票和基金
gc = universe.preview(now,skip_halted=True)
stocksmerged = {}
def merge(src):
    for k,v in src.iteritems():
        if not k in stocksmerged:
            stocksmerged[k]=v
print '黄金0.809'
merge(xg.findcandidate(gc,now,1,_EMA=True))
print '5日均线'
merge(xg.findcandidate(gc,now,2,_EMA=True))
print '黄金0.618'
merge(xg.findcandidate(gc,now,3,_EMA=True))
print '10日均线'
merge(xg.findcandidate(gc,now,4,_EMA=True))
print '黄金0.5'
merge(xg.findcandidate(gc,now,5,_EMA=True))
print '20日均线'
merge(xg.findcandidate(gc,now,6,_EMA=True))

for k,v in stocksmerged.iteritems():
    fig, _ax1 = plt.subplots()
    _gdfquotes = DataAPI.MktEqudAdjGet(ticker=k[:6],endDate=now,field=[u'secShortName','tradeDate','openPrice','highestPrice','lowestPrice','closePrice'],isOpen=1)
    _beginindex = max(len(_gdfquotes)-60,0)
    _targetprices = v[1:]
    print _gdfquotes[u'secShortName'].iloc[-1],v[0]
    _ax1.set_title(u'%s'%(k[:6]),fontproperties=font,fontsize='16')
    xg.plot_dragonpoint(_ax1,_gdfquotes,_beginindex,_targetprices,60) 
    plt.show()
