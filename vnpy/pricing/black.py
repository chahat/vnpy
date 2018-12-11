# encoding: UTF-8

'''
Black76 option pricing model, mainly used for pricing European options with futures as futures

Variable description
f: subject matter futures price
k: exercise price
r: risk free rate
t: remaining expiration time (year)
v: implied volatility
Cp: ​​option type, +1/-1 corresponds to call/put
Price: option price

For the purpose of developing demonstrations, the Greek value calculation in this document is based on a simple numerical difference method.
The computational efficiency is general, and a higher speed algorithm is recommended in the real disk.

The Greek value calculation results in this document do not use the traditional model price values, but instead
A more practical percentage change in real trading, as defined below
Delta: price change when f changes by 1%
Gamma: change of delta when f changes by 1%
Theta: price change when t changes 1 day (240 days per year on domestic trading day)
Vega: When v goes up and down 1 point, the price changes (such as from 16% to 17%)
'''

from __future__ import division

from scipy import stats
from math import (log, pow, sqrt, exp)

cdf = stats.norm.cdf


# 计算希腊值和隐含波动率时用的参数
STEP_CHANGE = 0.001
STEP_UP = 1 + STEP_CHANGE
STEP_DOWN = 1 - STEP_CHANGE
STEP_DIFF = STEP_CHANGE * 2

DX_TARGET = 0.00001


#----------------------------------------------------------------------
def calculatePrice(f, k, r, t, v, cp):
    """计算期权价格"""
    # 如果波动率为0，则直接返回期权空间价值
    if v <= 0:
        return max(0, cp * (f - k))

    d1 = (log(f / k) + (0.5 * pow(v, 2)) * t) / (v * sqrt(t))
    d2 = d1 - v * sqrt(t)
    price = cp * (f * cdf(cp * d1) - k * cdf(cp * d2)) * exp(-r * t)
    return price

#----------------------------------------------------------------------
def calculateDelta(f, k, r, t, v, cp):
    """计算Delta值"""
    price1 = calculatePrice(f*STEP_UP, k, r, t, v, cp)
    price2 = calculatePrice(f*STEP_DOWN, k, r, t, v, cp)
    delta = (price1 - price2) / (f * STEP_DIFF) * (f * 0.01)
    return delta

#----------------------------------------------------------------------
def calculateGamma(f, k, r, t, v, cp):
    """计算Gamma值"""
    delta1 = calculateDelta(f*STEP_UP, k, r, t, v, cp)
    delta2 = calculateDelta(f*STEP_DOWN, k, r, t, v, cp)
    gamma = (delta1 - delta2) / (f * STEP_DIFF) * pow(f, 2) * 0.0001
    return gamma

#----------------------------------------------------------------------
def calculateTheta(f, k, r, t, v, cp):
    """计算Theta值"""
    price1 = calculatePrice(f, k, r, t*STEP_UP, v, cp)
    price2 = calculatePrice(f, k, r, t*STEP_DOWN, v, cp)
    theta = -(price1 - price2) / (t * STEP_DIFF * 240)
    return theta

#----------------------------------------------------------------------
def calculateVega(f, k, r, t, v, cp):
    """计算Vega值"""
    vega = calculateOriginalVega(f, k, r, t, v, cp) / 100
    return vega

#----------------------------------------------------------------------
def calculateOriginalVega(f, k, r, t, v, cp):
    """计算原始vega值"""    
    price1 = calculatePrice(f, k, r, t, v*STEP_UP, cp)
    price2 = calculatePrice(f, k, r, t, v*STEP_DOWN, cp)
    vega = (price1 - price2) / (v * STEP_DIFF)
    return vega

#----------------------------------------------------------------------
def calculateGreeks(f, k, r, t, v, cp):
    """计算期权的价格和希腊值"""
    price = calculatePrice(f, k, r, t, v, cp)
    delta = calculateDelta(f, k, r, t, v, cp)
    gamma = calculateGamma(f, k, r, t, v, cp)
    theta = calculateTheta(f, k, r, t, v, cp)
    vega = calculateVega(f, k, r, t, v, cp)
    return price, delta, gamma, theta, vega

#----------------------------------------------------------------------
def calculateImpv(price, f, k, r, t, cp):
    """计算隐含波动率"""
    # 检查期权价格必须为正数
    if price <= 0:
        return 0
    
    # 检查期权价格是否满足最小价值（即到期行权价值）
    meet = False
    
    if cp == 1 and (price > (f - k) * exp(-r * t)):
        meet = True
    elif cp == -1 and (price > k - f):
        meet = True
    
    # 若不满足最小价值，则直接返回0
    if not meet:
        return 0
    
    # 采用Newton Raphson方法计算隐含波动率
    v = 0.3     # 初始波动率猜测
    
    for i in range(50):
        # 计算当前猜测波动率对应的期权价格和vega值
        p = calculatePrice(f, k, r, t, v, cp)
        
        vega = calculateOriginalVega(f, k, r, t, v, cp)
        
        # 如果vega过小接近0，则直接返回
        if not vega:
            break
        
        # 计算误差
        dx = (price - p) / vega
        
        # 检查误差是否满足要求，若满足则跳出循环
        if abs(dx) < DX_TARGET:
            break
        
        # 计算新一轮猜测的波动率
        v += dx
        
    # 检查波动率计算结果非负
    if v <= 0:
        return 0
    
    # 保留4位小数
    v = round(v, 4)
    
    return v
    