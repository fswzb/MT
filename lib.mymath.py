# round函数四舍五入
def rod(x,n):
    #first omit n+1
    xn1=int(x*10**(n+1))
    #then add 1 at the end to avoid the float precise
    xn1=xn1+0.1
    return round(xn1/10**(n+1),n)
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    return False
#print round(299.455,2)
#print rod(299.455,2)
#print round(39.955,2)
#print rod(39.955,2)