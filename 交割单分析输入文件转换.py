import pandas as pd
excel = pd.read_excel("龙回头模拟交易20170101-20170222-EMA-2.xlsx")
_dict = excel.to_dict(orient='index')
cloumn_heads=[u'成交日期',u'证券代码',u'成交均价',u'发生金额',u'成交数量',u'证券名称',u'操作']
_newdict = {}
for k,v in _dict.items():
    _newdict[len(_newdict)-1]=[v['tradedate'],v['secID'][:6],v['tradeprice']]
for k,v in _newdict.items():
    if _newdict[k][0].isdigit():
        _newdict[k].append(100*_newdict[k][2])
        _newdict[k].append(100)
        _newdict[k].append('shorname')
        _newdict[k].append(u'证券买入')
        
excel = pd.DataFrame.from_dict(data=_newdict,orient='index') 
excel.to_excel('test.xlsx',header=cloumn_heads)