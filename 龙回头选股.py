import lib.selstock as xg
reload(xg)
from CAL.PyCAL import font
import matplotlib.pyplot as plt
from matplotlib import gridspec
import time
now = time.strftime('%Y%m%d')
universe = DynamicUniverse('A').apply_filter(Factor.VOL10.nlarge(300))#&Factor.REVS10.nlarge(_numcandiate)) #set_universe('A') # 证券池，支持股票和基金
now='20170217'
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
    fig = plt.figure(figsize=(8,6))
    gs = gridspec.GridSpec(2,1,height_ratios=[4,1])
    _ax1 = plt.subplot(gs[0])
    gs.update(left=0.05, right=0.48, hspace=0.0)
    ax1 = plt.subplot(gs[1])
    _gdfquotes = DataAPI.MktEqudAdjGet(ticker=k[:6],endDate=now,field=[u'secShortName','tradeDate','openPrice','highestPrice','lowestPrice','closePrice','turnoverVol'],isOpen=1)
    _beginindex = max(len(_gdfquotes)-60,0)
    _targetprices = v[1:]
    print _gdfquotes[u'secShortName'].iloc[-1],v[0]
    _ax1.set_title(u'%s'%(k[:6]),fontproperties=font,fontsize='16')
    fig.sca(_ax1)
    xg.plot_dragonpoint(_ax1,_gdfquotes,_beginindex,_targetprices,60) 
    #成交量
    fig.sca(ax1)
    xg.plot_volume_overlay(ax1,_gdfquotes,_beginindex)
    ax1.yaxis.set_visible(False)
    plt.show()

