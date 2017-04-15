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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    return False
#rod(0.45,1)