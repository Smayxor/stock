#Version 1.2  Got it to save chart as a png.  Preparing for a discord bot
#Version 1.1  Improved display of data on charts to scale with max values

from tkinter import *
from datetime import date
from datetime import datetime as dt
import datetime
import time
import requests
import json
import math
#import urllib.request as req
#from ipycanvas import Canvas as ican
from PIL import Image, ImageDraw, ImageGrab, ImageFont
#import subprocess as SP
import os

#import pandas as pd
#import numpy as np
#import scipy
#from scipy.stats import norm
#import matplotlib.pyplot as plt

#************************************************************
#Get API Key from TDA Developer Account new App,  place in file named apikey.json with this for contents-> {"API_KEY": "your-key-here"}
MY_API_KEY = json.load(open('apikey.json'))['API_KEY']
#POLYGON_API_KEY = json.load(open('apikey.json'))['POLYGON']
#************************************************************

endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?apikey={api_key}"
vix_endpoint = "https://api.tdameritrade.com/v1/marketdata/%24VIX.X/quotes?apikey={api_key}"   # %24 is a $  aka $VIX.X
options_endpoint = "https://api.tdameritrade.com/v1/marketdata/chains?apikey={api_key}&symbol={stock_ticker}&contractType=ALL&strikeCount={count}&range=NTM&fromDate={fromDate}&toDate={toDate}&optionType=ALL"
fundamental_endpoint = "https://api.tdameritrade.com/v1/instruments?apikey={api_key}&symbol={stock_ticker}&projection=fundamental"

ticker_name = 'SPY'
GEX = {}
DEX = {}
VEX = {}
Volas = {}
Pain = {}
CallGEX = {}
PutGEX = {}
ExpectedMove = 0.0
dn = datetime.datetime.now()
dn = dn.replace(hour=0, minute=0, second=0, microsecond=0)

def drawRect(x, y, w, h, color, border):
    if border in 'none': border = color
    canvas.create_rectangle(x, y, w, h, fill=color, outline=border)
    draw.rectangle([x, y, w, h], fill=color, outline=border)   #for PIL Image

def drawText(x, y, txt, color):
    canvas.create_text(x, y, anchor=NW, font="Purisa", text=txt, fill=color)
    draw.text((x,y), text=txt, fill=color, anchor=NW)

def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21

def daysFromNow(days):
    delta = dt.strptime(days.split(":")[0], "%Y-%m-%d") - dn
    return delta.days + 1
 
# Black-Scholes European-Options Gamma
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    if T == 0 or vol == 0:
        return 0

    dp = (np.log(S/K) + (r - q + 0.5*vol**2)*T) / (vol*np.sqrt(T))
    dm = dp - vol*np.sqrt(T) 

    if optType == '1':
        gamma = np.exp(-q*T) * norm.pdf(dp) / (S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 
    else: # Gamma is same for calls and puts. This is just to cross-check
        gamma = K * np.exp(-r*T) * norm.pdf(dm) / (S * S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 

def addStrike(strike, volume, oi, delta, gamma, vega, price, volatility, call, itm, bid, days):
    global ExpectedMove, GEX, DEX, VEX, Volas, Pain
    try:
        if not strike in GEX:   #Prevents NaN values
            GEX[strike] = 0
            CallGEX[strike] = 0
            PutGEX[strike] = 0
            DEX[strike] = 0
            VEX[strike] = 0
            Volas[strike] = 0
            Pain[strike] = 0
        if (oi == 0): return   #Delta and Gamma show up as -999.0

        GEX[strike] += (gamma * oi * call)
        DEX[strike] += (delta * oi)
        VEX[strike] = vega
        Volas[strike] = volatility

        if (call == 1):
            CallGEX[strike] += (gamma * oi)
#            if strike == 420: print(delta, gamma)
        else:
            PutGEX[strike] += (gamma * oi)
#            if strike == 420: print(delta, gamma)
        if (itm): Pain[strike] += oi
        
        em = 0
        if (strike - int(price)) == 0 : em = volatility * math.sqrt(days / 365)
        if em > ExpectedMove: ExpectedMove = em   #Each date should land on this strike, keep the biggest one
    except TypeError:
        a = 1

def stock_price():
    global ExpectedMove, GEX, DEX, VEX, Volas, Pain, img, draw
    GEX.clear()
    CallGEX.clear()
    PutGEX.clear()
    DEX.clear()
    VEX.clear()
    Volas.clear()
    Pain.clear()
    ExpectedMove = 0.0

#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
    today = date.today()
    if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours
    dateRange = today + datetime.timedelta(days=int(e2.get()))
    ticker_name = e1.get().upper()

    full_url = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', fromDate=today, toDate=dateRange)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    price = content['underlyingPrice']

#Force method to return results if DateRange is too small for stock to have options.  increment days until it works     
    if (content['status'] in 'FAILED') and (int(e2.get()) < 30):
        days = int(e2.get()) + 1
        e2.delete(0, END)
        e2.insert(0, str(days))
        stock_price()
        return

    """  #Declaration For using pandas/numpy code.
    dataColumns ={'ExpirationDate':'','Calls':'1','LastSale':'0','Net':'0','Bid':'0','Ask':'0','Vol':'0','IV':'0','Delta':'0','Gamma':'0','OpenInt':'0','StrikePrice':'0'}
    df = pd.DataFrame(columns=dataColumns) """
#Load the data from JSON
    for days in content['callExpDateMap']: 
        for strikes in content['callExpDateMap'][days]:
            def addData(opts): addStrike(strike=opts["strikePrice"], volume=opts["totalVolume"], oi=opts["openInterest"], delta=opts['delta'], gamma=opts["gamma"], vega=opts['vega'], volatility=opts['volatility'], price=price, call=(1 if (opts['putCall'] in "CALL") else -1), itm=opts['inTheMoney'], bid=opts['bid'], days=daysFromNow(days))
            for options in content['callExpDateMap'][days][strikes]: addData(options)
            for options in content['putExpDateMap'][days][strikes]: addData(options)

#************* Paste pandas/numpy code here ****************

#Get max GEX/DEX for math to draw chart
    maxPain = 0
    maxGEX = 0
    maxDEX = 0
    maxCPGEX = 0
    for strikes in GEX:
        if abs(GEX[strikes]) > maxGEX: maxGEX = abs(GEX[strikes])
        if abs(CallGEX[strikes]) > maxCPGEX: maxCPGEX = abs(CallGEX[strikes])
        if abs(PutGEX[strikes]) > maxCPGEX: maxCPGEX = abs(PutGEX[strikes])
        if abs(DEX[strikes]) > maxDEX: maxDEX = abs(DEX[strikes])
        if abs(Pain[strikes]) > maxPain: maxPain = abs(Pain[strikes])
    
#Draw the chart
    canvas.delete('all')
    drawRect(0,0,800,500, color="#000", border="#000")
    
    x = -10
    for strikes in sorted(GEX):
        x += 15
        drawText(x, 235, txt=('\n'.join(str(strikes).replace('.0', ''))), color="#0F0")
        if (Pain[strikes] != 0): drawRect(x, 30, x + 9, 30 + ((abs(Pain[strikes]) / maxPain) * 50), color="#00f", border='')
        if (GEX[strikes] != 0): drawRect(x, 235 - ((abs(GEX[strikes]) / maxGEX) * 150), x + 9, 235, color=("#0f0" if (GEX[strikes] > -1) else "#f00"), border='')
        if (DEX[strikes] != 0): drawRect(x + 2, 235 - ((abs(DEX[strikes]) / maxDEX) * 150), x + 6, 235, color=("#077" if (DEX[strikes] > -1) else "#f77"), border='')
        if (CallGEX[strikes] != 0): drawRect(x, 400 - ((CallGEX[strikes] / maxCPGEX) * 50), x + 9, 400, color="#0f0", border='')
        if (PutGEX[strikes] != 0): drawRect(x, 400 + ((PutGEX[strikes] / maxCPGEX) * 50), x + 9, 400, color="#f00", border='')

#experimental search for Zero Gamma
    total_gamma = 0
    for strikes in GEX:
        total_gamma += GEX[strikes]
    total_gamma = total_gamma / price
    print('TotalGamma', total_gamma)
#    print(Pain)

#Get company fundamentals
    page = requests.get(url=fundamental_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name))
    content = json.loads(page.content)[ticker_name]["fundamental"]
    fundamentals = {'Beta': content["beta"], 'DivYield': content["dividendYield"], 'DivDate': content["dividendDate"], 'DivAmount': content["dividendAmount"], 'peRatio': content["peRatio"], 'pegRatio': content["pegRatio"], 'QuickRatio': content["quickRatio"], 'DebtToCapital': content["totalDebtToCapital"], 'SharesOutstanding': content["sharesOutstanding"], 'MarketCapFloat': content["marketCapFloat"], 'MarketCap': content["marketCap"], 'ShortInt': content["shortIntToFloat"], 'ShortDaysToCover': content["shortIntDayToCover"]}
    drawRect(x+20, 0, x + 24, 350, color='#777', border='#333')
    x += 27
    y = 0
    for keys in fundamentals:
        drawText(x, y, txt=keys + ": " + str(fundamentals[keys]), color="#00f")
        y += 25

# For every 16 points of VIX expect 1% move on SPY
    drawText(0, 0, txt=str(ticker_name + ": $" + str(round(price, 2)) + " VIX " + str(json.loads(requests.get(url=vix_endpoint.format(api_key=MY_API_KEY)).content)['$VIX.X']['lastPrice']) + " Expected Move " + str(round(ExpectedMove, 2)) + "% $" + str(round(price * (ExpectedMove / 100), 2))), color="#0FF")

    
#    print(json.loads(requests.get(url=endpoint.format(stock_ticker="%24DXY", api_key=MY_API_KEY)).content))
#    print( req.urlopen('https://www.cboe.com/delayed_quotes/spx/quote_table').read().decode('utf8') )   # Strictly prohibited

    img.save("stock-chart.png")
    
#Under construction.  plans to add 10min chart
def stock_chart():
#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
    today = date.today()
    if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)
    dateRange = today + datetime.timedelta(days=int(e2.get()))
    ticker_name = e1.get().upper()

    full_url = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', fromDate=today, toDate=dateRange)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    price = content['underlyingPrice']
        
win = Tk()
win.geometry("800x500")

Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, ticker_name)

e2 = Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '0')

Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
Button(win, text="Fetch", command=stock_price, width=5).grid(row=0, column=2, sticky='E')
Button(win, text="Loop", command=stock_chart, width=5).grid(row=0, column=3, sticky='N')

canvas = Canvas(win,  width= 2400, height= 2000)
canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
canvas.configure(bg="#000000")

img = Image.new("RGB", (800, 500), "#000")
draw = ImageDraw.Draw(img)

stock_price()
mainloop()

os.remove("stock-chart.png", dir_fd=None)

"""  #Block comment for all the pandas/numpy code.   Might require Put-Call specific fields for later compatability
#**********Starting in code section to parse JSON
            for options in content['callExpDateMap'][days][strikes]:
                dataRow = [days.split(":")[0], '1', '0', '0', options['bid'], options['ask'], options['totalVolume'], options['volatility'], options['delta'], options['gamma'], options['openInterest'], strikes]
                df.loc[len(df.index)] = dataRow
            for options in content['putExpDateMap'][days][strikes]:
                dataRow = [days.split(":")[0], '-1', '0', '0', options['bid'], options['ask'], options['totalVolume'], options['volatility'], options['delta'], options['gamma'], options['openInterest'], strikes]
                df.loc[len(df.index)] = dataRow


    df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], format='%Y-%m-%d')
    df['ExpirationDate'] = df['ExpirationDate'] + datetime.timedelta(hours=16)
    df['StrikePrice'] = df['StrikePrice'].astype(float)
    df['IV'] = df['IV'].astype(float)
    df['Gamma'] = df['Gamma'].astype(float)
    df['OpenInt'] = df['OpenInt'].astype(float)
    df['Calls'] = df['Calls'].astype(float)



    fromStrike = 0.8 * price
    toStrike = 1.2 * price

# ---=== CALCULATE SPOT GAMMA ===---
# Gamma Exposure = Unit Gamma * Open Interest * Contract Size * Spot Price 
# To further convert into 'per 1% move' quantity, multiply by 1% of spotPrice
    df['GEX'] = df['Gamma'] * df['OpenInt'] * 100 * price * price * 0.01 * df['Calls']


    df['TotalGamma'] = df.GEX / 10**9
    dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
    strikes = dfAgg.index.values

    # Chart 1: Absolute Gamma Exposure
#    plt.grid()
#    plt.bar(strikes, dfAgg['TotalGamma'].to_numpy(), width=6, linewidth=0.1, edgecolor='k', label="Gamma Exposure")
#    plt.xlim([fromStrike, toStrike])
#    chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum())) + " Bn per 1% SPX Move"
#    plt.title(chartTitle, fontweight="bold", fontsize=20)
#    plt.xlabel('Strike', fontweight="bold")
#    plt.ylabel('Spot Gamma Exposure ($ billions/1% move)', fontweight="bold")
#    plt.axvline(x=price, color='r', lw=1, label="SPX Spot: " + str("{:,.0f}".format(price)))
#    plt.legend()
#    plt.show()

# ---=== CALCULATE GAMMA PROFILE ===---
    levels = np.linspace(fromStrike, toStrike, 60)

    # For 0DTE options, I'm setting DTE = 1 day, otherwise they get excluded
    df['daysTillExp'] = [1/262 if (np.busday_count(today, x.date())) == 0 \
                               else np.busday_count(today, x.date())/262 for x in df.ExpirationDate]

    nextExpiry = df['ExpirationDate'].min()

    df['IsThirdFriday'] = [isThirdFriday(x) for x in df.ExpirationDate]
    thirdFridays = df.loc[df['IsThirdFriday'] == True]
    nextMonthlyExp = thirdFridays['ExpirationDate'].min()

    totalGamma = []
    totalGammaExNext = []
    totalGammaExFri = []
# For each spot level, calc gamma exposure at that point
    for level in levels:
        df['GammaEx'] = df.apply(lambda row : calcGammaEx(level, row['StrikePrice'], row['IV'], 
                                                              row['daysTillExp'], 0, 0, "Calls", row['OpenInt']), axis = 1)
        totalGamma.append(df['GammaEx'].sum() * df['Calls'])
        exNxt = df.loc[df['ExpirationDate'] != nextExpiry]
        totalGammaExNext.append(exNxt['GammaEx'].sum() * exNxt['Calls'].sum())

        exFri = df.loc[df['ExpirationDate'] != nextMonthlyExp]
        totalGammaExFri.append(exFri['GammaEx'].sum() * exFri['Calls'].sum())


    totalGamma = np.array(totalGamma) / 10**9
    totalGammaExNext = np.array(totalGammaExNext) / 10**9
    totalGammaExFri = np.array(totalGammaExFri) / 10**9

    # Find Gamma Flip Point
    zeroCrossIdx = np.where(np.diff(np.sign(totalGamma)))[0]

    negGamma = totalGamma[zeroCrossIdx]
    posGamma = totalGamma[zeroCrossIdx+1]    #current section causing bug, index out of bounds
    negStrike = levels[zeroCrossIdx]
    posStrike = levels[zeroCrossIdx+1]

    # Writing and sharing this code is only possible with your support! 
    # If you find it useful, consider supporting us at perfiliev.com/support :)
    zeroGamma = posStrike - ((posStrike - negStrike) * posGamma/(posGamma-negGamma))
    zeroGamma = zeroGamma[0]

    print(df)
    print(zeroGamma)
"""



"""

https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory?apikey={apikey}&periodType=day&period=10&frequencyType=minute&frequency=30&needExtendedHoursData=true"
{
  "candles": [
    {
      "open": 136.39,
      "high": 136.47,
      "low": 135.45,
      "close": 135.47,
      "volume": 276577,
      "datetime": 1667822400000
    }
  ],
  "symbol": "AAPL",
  "empty": false
}

https://api.tdameritrade.com/v1/marketdata/%24SPX.X/movers?apikey={apikey}&direction=down&change=percent
[broken]

https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes?apikey={apikey}
https://api.tdameritrade.com/v1/instruments?apikey={apikey}&symbol={ticker}&projection=fundamental

"""