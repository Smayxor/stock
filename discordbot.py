import datetime
import time
import ujson as json
import math
import threading
import sys
import random
from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands
from urllib.parse import unquote as unenc
from urllib.parse import quote as enc
import datapuller as dp
import drawchart as dc
import signals as sig
import requests
import os
from typing import Union

init = json.load(open('apikey.json'))
BOT_TOKEN = init['BOT_TOKEN']
BOT_APP_ID = init['DISCORD_APP_ID']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
TENOR_API_KEY = init['TENOR_API_KEY']
UPDATE_CHANNEL = init['UPDATE_CHANNEL']    #Channel ID stored as Integer not string

WEEKDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "DAILY IV ", "EGEX ", "COMBINED ", "ATR+FIB ", "LAST DTE ", "LOG-DATA ", "CHANGE IN GEX ", "SKEWED GEX ", "HEAT MAP "]
CHART_GEX = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_DAILYIV = 3
CHART_EGEX = 4
CHART_COMBO = 5
CHART_ATR = 6
CHART_LASTDTE = 7
CHART_LOG = 8
CHART_CHANGE = 9
CHART_SKEW = 10
CHART_HEATMAP = 11

def getTenorGIF( search ):
	url ="https://g.tenor.com/v2/search?q=%s&key=%s&limit=%s" % (search, TENOR_API_KEY, "8")
	r = requests.get(url=url)
	content = json.loads(r.content)
	dctResults = []
	if r.status_code == 200:
		for ids in content['results']:
			dctResults.append( ids['media_formats']['tinygif']['url'] )
		return random.choice( dctResults )
	else: return "https://media.tenor.com/F2clNh5qPRoAAAAM/pump-stocks.gif"

gms = [enc("gm friends"), enc("good morning"), enc("wake up"), enc("time to work")]
pumps = [enc("stock pump rocket moon"), enc("stock bull"), enc("pepe money rain")]
dumps = [enc("stock dump crash"), enc("bear stock")]
titties = [enc("boobs bounce breast"), enc("women motorboat boobs"), enc("asian tits")]
asses = [enc("women ass twerk poggers"), enc("women sexy butt"), enc("latina big ass")]

def isThirdFriday(d):    return d.weekday() == 4 and 15 <= d.day <= 21

def get_expiry_date_for_month(curr_date):
    """
    http://cfe.cboe.com/products/spec_vix.aspx

    TERMINATION OF TRADING:

    Trading hours for expiring VIX futures contracts end at 7:00 a.m. Chicago
    time on the final settlement date.

    FINAL SETTLEMENT DATE:

    The Wednesday that is thirty days prior to the third Friday of the
    calendar month immediately following the month in which the contract
    expires ("Final Settlement Date"). If the third Friday of the month
    subsequent to expiration of the applicable VIX futures contract is a
    CBOE holiday, the Final Settlement Date for the contract shall be thirty
    days prior to the CBOE business day immediately preceding that Friday.
    """
    # Date of third friday of the following month
    if curr_date.month == 12:
        third_friday_next_month = datetime.date(curr_date.year + 1, 1, 15)
    else:
        third_friday_next_month = datetime.date(curr_date.year,
                                          curr_date.month + 1, 15)

    one_day = datetime.timedelta(days=1)
    thirty_days = datetime.timedelta(days=30)
    while third_friday_next_month.weekday() != 4:
        # Using += results in a timedelta object
        third_friday_next_month = third_friday_next_month + one_day

    # TODO: Incorporate check that it's a trading day, if so move the 3rd
    # Friday back by one day before subtracting
    return third_friday_next_month - thirty_days

class MyNewHelp(commands.MinimalHelpCommand):
	async def send_pages(self):
		strHelp = """}help for commands for Smayxor
/gex ticker dte strike-count charttype
/8ball followed by a question, ending in ?
/news days <- Displays upcoming events

The blue bars on left are OI.
The Red/Green bars left of the strikes are Total Gamma Exposure.
To the right of the strikes is Call Put GEX individually

}gm }tits }ass }pump }dump also exist"""
		destination = self.get_destination()
		for page in self.paginator.pages:
			await destination.send(strHelp)
bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyNewHelp(), sync_commands=True)
def getChartType( arg ):
	arg = arg.upper()
	if arg == 'V': return CHART_VOLUME
	elif arg == 'IV': return CHART_IV
	elif arg == 'DAILYIV': return CHART_DAILYIV
	elif arg == 'E': return CHART_EGEX
	elif arg == 'COMBO': return CHART_COMBO
	elif arg == 'ATR': return CHART_ATR
	elif arg == 'LD': return CHART_LASTDTE
	elif arg == 'CHANGE': return CHART_CHANGE
	elif arg == 'SKEW': return CHART_SKEW
	elif arg == 'HEATMAP': return CHART_HEATMAP
	else: return CHART_GEX

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01)

#@app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)#(i.guild_id, i.user.id))
@bot.tree.command(name="gex", description="Draws a GEX chart")
async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, count: int = 40, chart: str = "R"):
	global tickers, updateRunning, needsQueue
	perms = await checkInteractionPermissions( intr )
	if perms[1] > 0 :
		await intr.response.send_message(f'Using /gex has a 20 second cooldown - {perms[1]} seconds remaining', ephemeral=True)
		return
	"""
	minute = getStrTime()
	if 615 < minute < 630 and BOT_USER_FOR_KILL != str(intr.user) :
		randomMessage = ["Charting down for server maintenance during 15 minutes before Market Open.",
						"Bot is refreshing, go run one out, those are rookie numbers",
						"Smaybot is updating, please boost server for more info",
						"Go read Mark Douglas for a few"]
		await intr.response.send_message(random.choice(randomMessage), ephemeral=True)
		return"""
	await intr.response.defer(thinking=True, ephemeral=perms[3] == False)
	ticker = ticker.upper()
	chartType = getChartType( chart )
	if chartType == CHART_HEATMAP:
		fn = dc.drawWeeklyChart()
	else:
		fn = ""
		
		if chartType == CHART_COMBO:
			fn = grabFridayCombo(dte)
			
		elif "SPX." in ticker: # Pull the data from PC Server,  needs to check if server is even available
			try :
				tmp = ticker.split(".")
				ticker = tmp[0]
				minute = float(tmp[1])
				
				fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
				file = fileList[-1]
				gexData = dp.pullLogFile(file, discordBot=True)
				strikes = None
				dif = 99999

				for t in gexData:
					tmp = abs(float(t) - minute)
					if tmp < dif :
						dif = tmp
						strikes = gexData[t]
						dte = t
				fn = dc.drawGEXChart("SPX", 30, dte=0, strikes=strikes, expDate=dte)
			except Exception as er:
				print("GEX BOOM - ", er)
				await  intr.followup.send("Error pulling data!")
		else:
			fn = dc.drawGEXChart(ticker, count, dte, chartType=chartType)
	if fn == "error.png": await intr.followup.send("Failed to get data")
	else:
		try: await intr.followup.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await intr.followup.send("No image permissions")

@slash_command_gex.error
async def on_gex_error(intr: discord.Interaction, error: app_commands.AppCommandError):
	print( error ) #This should no longer actually be fired,  left-overs from default discord User Cooldown code
	try:
		await intr.response.send_message(f'Using /gex has a 1 minute cooldown - {int(error.retry_after)} seconds remaining', ephemeral=True)
	except: await intr.response.send_message(f'Using /gex has a 1 minute cooldown')
	
@bot.command(name="pump")
async def command_pump(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
@bot.command(name="dump")
async def command_dump(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )
@bot.command(name="tits")
async def command_tits(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(titties) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="ass")
async def command_ass(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(asses) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="gm")
async def command_gm(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(gms) if len( args) == 0 else enc(' '.join(args)) ) )
	
@bot.tree.command(name="8ball", description="Answers your question?")
async def slash_command_8ball(intr: discord.Interaction, question: str):
	perms = await checkInteractionPermissions( intr )
	future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good', 'You should ask Siri, that slut.', 'I rolled a dice to answer you, and it said the answer is C.', 'Follow your heart, I wouldn\'t trust your mind though.', 'I don\'t know and I don\'t care.', 'Did you ask ChatGPT?', 'Just google it.']
	if "?" in question:
		response = "Question: " + question + "\rAnswer: " + random.choice(future)
	else:
		response = "Please phrase that as a question"
	await intr.response.send_message(response)

allNews = None
def buildNews(days):
	global allNews
	if allNews is None :
		allNews = dp.fetchNews()
	tdy = datetime.datetime.now()
	isoday = tdy.weekday()
	
	if isoday > 4:
		isodelta = 7 - isoday
		isoday = 0
		tdy = tdy + datetime.timedelta(days=isodelta)
	
	rangeDays = 0
	if days.isnumeric() : rangeDays = int(days)
	elif days == "TODAY" : rangeDays = 0
	elif days == "WEEK" : rangeDays = max(5 - isoday, 0)
	elif days == "ALL" : rangeDays = max(5 - isoday, 0)
		
	rangeDays += 1
	dayList = [tdy + datetime.timedelta(x) for x in range(rangeDays) if (x+isoday) % 7 < 5 ]

	txt = ''
	txt2 = ''

	for d in dayList:
		#2024-08-16 06:58:09.295036
		day = str(d).split(' ')[0]
		txt += f'**{day}**\r```fix\r'
		for t in [f'{x.Time} {x.Desc}\r' for x in allNews if day in x.Day]:
			txt += t
		txt += '```'

	if len(txt) == 0 : txt = 'No news'

	return (txt, txt2)

class OldNewsData():
	def __init__(self, day):
		self.Day = day
		self.Events = []
	def addEvent(self, txt):
		if '<a href=' in txt:
			txt = txt.replace('</a>', '')
			txt = txt.split('<a href=')[0] + txt.split('">')[1]
		self.Events.append( txt )
	def toString(self):
		text = '**' + self.Day + '**```fix'
		for e in self.Events:
			if len( e ) > 0 : text += '\n' + e
		return text + '```'
		
@bot.tree.command(name="news")
async def slash_command_news(intr: discord.Interaction, days: str = "TODAY"):	
	perms = await checkInteractionPermissions( intr )
	await intr.response.defer(thinking=True)

	finalMessage, nextMessage = buildNews(days)
	
	#print( finalMessage )
	#print( nextMessage )
	
	chnl = bot.get_channel(intr.channel.id)
	try: 
		#await intr.response.send_message( finalMessage )
		await intr.followup.send( finalMessage )
	except Exception as e: 
		try: await legacySend( channel=chnl, text=finalMessage )
		except Exception as er: print("News BOOM", er)
	if len(nextMessage) != 0:
		try: await legacySend( channel=chnl, text=nextMessage )	
		except Exception as e: print("News 2 BOOM", e)

@bot.command(name="sudo")
@commands.is_owner()
async def sudo(ctx, *args): 
	global tickers, updateRunning, auto_updater, update_timer
	user = str(ctx.author.name)
	userID = ctx.author.id
	print( user, userID )
	if 758033219177283696 != userID:
		await legacySend( ctx=ctx, text=user + " you can't kill meme!")
		return
	if len(args) != 1 : 
		await legacySend( ctx=ctx, text="No command")
		return

	if args[0] == "kill" :
		await legacySend( ctx=ctx, text=user + " triggered shutdown")
		await bot.close()
		await bot.logout()
		exit(0)
	elif args[0] == "update" :
		await legacySend( ctx=ctx, text=user + " requested code update")
		print("getting update")
		files = ['discordbot.py', 'datapuller.py', 'drawchart.py', 'signals.py']
		for fileName in files:
			print(f'Fetching {fileName}')
			r = requests.get(url=f'https://raw.githubusercontent.com/Smayxor/stock/main/{fileName}')
			
			with open(f'./{fileName}', "wb") as outfile:
				outfile.write(r.content)
				print(f'{fileName} Downloaded at {os.path.realpath(outfile.name)} - {outfile.name}' )
		print('All files updated.  Restarting service')
		exit(9)
		await bot.close()
		await bot.logout()
	print("Finished SUDO")	
	
	await legacySend( ctx=ctx, text="Command Complete")

dailyTaskTime = datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime)
async def dailyTask():
	chnl = bot.get_channel(UPDATE_CHANNEL)
	if datetime.datetime.now().weekday() > 4 : 
		await legacySend( channel=chnl, text= buildNews("WEEK")[0] )
		return
	#print("Daily Task Execution")
	await legacySend( channel=chnl, text="Fetching Morning Charts")
	await legacySend( channel=chnl, text= buildNews("TODAY")[0] )
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await chnl.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await legacySend( channel=chnl, text="No image permissions")
		
	if datetime.datetime.now().weekday() == 0 : 
		fn = dc.drawWeeklyChart()
		chnl = bot.get_channel(1221522301787570256)
		await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		chnl = bot.get_channel(1258440980529418250)  #Beating Meat Gex Channel
		await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))

dailyTaskTime2 = datetime.time(hour=13, minute=31, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime2)
async def dailyTask2():
	if datetime.datetime.now().weekday() > 4 : return
	startMonitorSPX()
	chnl = bot.get_channel(UPDATE_CHANNEL)
	#print("Daily Task Execution 2")
	dp.findSPY2SPXRatio()
	await legacySend( channel=chnl, text="Fetching Morning Charts")
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await legacySend( channel=chnl, text="Failed to get data")# await chnl.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			chnl = bot.get_channel(1156977360881586177)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await legacySend( channel=chnl, text="No image permissions")#await chnl.send("No image permissions")
	#logFutureDTEs() #For Heatmap

dailyTaskTime3 = datetime.time(hour=13, minute=11, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime3)
async def dailyTask3():
	if datetime.datetime.now().weekday() > 4 : return
	chnl = bot.get_channel(1193060258088759356)
	#print("Daily Task Execution 3")
	fn = dc.drawGEXChart("SPX", 40, 0)#, chartType=CHART_VOLUME)
	if fn == "error.png": await legacySend( channel=chnl, text="Failed to get data")

	else:
		try: 
			chnl = bot.get_channel(1193060258088759356)
			await legacySend( channel=chnl, fileName=fn)
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await legacySend( channel=chnl, fileName=fn)
			chnl = bot.get_channel(1258440980529418250)  #Beating Meat gex channel
			await legacySend( channel=chnl, fileName=fn)
		except: await legacySend( channel=chnl, text="No image permissions")


gexDataToday = None
gexDataFileName = None
lastSPXTimeStamp = None
sigs = None
strat = None
@tasks.loop(seconds=4)  # If not fast enough, will miss the "final" commits to data!!!!
async def monitorSPX():
	global gexDataToday, gexDataFileName, sigs, strat, lastSPXTimeStamp
	
	blnWasFinal = dp.blnWasFinal
	gexDataToday = dp.pullLogFile(gexDataFileName, cachedData=False)
	if not (dp.blnWasFinal == True and blnWasFinal == False) : return   #Prevent action without a commit, Should instead pop recent entries in strat so we can get a Live signal
	
	#minute = next(x for x in reversed(gexDataToday))
	if getToday()[1] < 130000:
		#lastDataTime = [[x for x in gexDataToday.keys()][-1], [x for x in gexDataToday.keys()][-2]]  #High and Low
		newTimes = [x for x in gexDataToday.keys() if float(x) > lastSPXTimeStamp]
		#print( newTimes )
		for ldt in newTimes:
			lastSPXTimeStamp = float(ldt)
			strikes = gexDataToday[ldt]
			flag = strat.addTime(float(ldt), strikes)
			if flag[0] != 0 : 
				print(f'Flag {flag} at {ldt}')# general chat = 1055967445652865130
				chnl = bot.get_channel(1055967445652865130)
				txt = flag[1]
				await legacySend( channel=chnl, text=txt)
	else:
		print('Stopping monitor')
		monitorSPX.cancel()
	
def startMonitorSPX():
	global gexDataToday, gexDataFileName, sigs, strat, lastSPXTimeStamp
	print('Starting monitor')
	fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
	gexDataFileName = fileList[-1]
	gexDataToday = dp.pullLogFile(gexDataFileName, cachedData=False)
	
	fltTimes = [float(x) for x in gexDataToday.keys()]
	#lastDataTime = fltTimes[-1]
	sortedABSTimes = sorted( fltTimes, key=lambda i: abs(i - 630) ) #We want market open to be first in list
	firstTime = sortedABSTimes[0]
	
	firstStrikes = gexDataToday[str(firstTime)]
	sigs = sig.identifyKeyLevels( firstStrikes )
	strat = sig.Signal(day=gexDataFileName, firstTime=firstTime, strikes=firstStrikes, deadprice=0.30, ema1=2, ema2=4)
	#strat.addTime( float(lastDataTime), gexDataToday[str(lastDataTime)] )
	
	for k, v in gexDataToday.items():
		strat.addTime(float(k), v)
		lastSPXTimeStamp = float(k)
	print(f'Data loaded in monitor {lastSPXTimeStamp}')
	monitorSPX.start()
	 
blnFirstTime = True
@bot.event
async def on_ready():
	global blnFirstTime
	if blnFirstTime :
		#channelUpdate.start()
		dailyTask.start()
		dailyTask2.start()
		dailyTask3.start()
		blnFirstTime = False
		minute = getToday()[1]
		if minute < 130000 : startMonitorSPX()
	
@bot.command(name="s")
async def get_gex(ctx, *args):
	chnl = bot.get_channel(UPDATE_CHANNEL)
	await legacySend( channel=chnl, text="Testing stuff")
	#*********************************************************************************************************************

orders=[]
@bot.command(name="trade")
@commands.is_owner()
async def trade(ctx, arg1, arg2=None, arg3=None):
	global gexDataToday, gexDataFileName, sigs, strat, lastSPXTimeStamp, orders
	
	if gexDataToday is None: startMonitorSPX() #Used for testing AH
	
	if arg1 == 'balance':
		balance = dp.getAccountBalance()['cash']['cash_available']
		await legacySend( ctx=ctx, text=f'{balance}')
	elif arg1 ==  'orders':
		orders = getOrders()
		txtOut = 'Orders - \r'
		for o in orders:
			txtOut += f'{o}\r'
		await legacySend( ctx=ctx, text=txtOut)
		
		positions = getPositions()
		txtOut = 'Positions - \r'
		for o in positions:
			txtOut += f'{o}\r'
		await legacySend( ctx=ctx, text=txtOut)
	elif arg1 == 'buy' :
		if not arg2 is None :
			if len(arg2) != 5 :
				await legacySend( ctx=ctx, text=f'Specify Strike + c/p - Found {arg2[-1]}')
				return
			isCall = arg2[-1] == 'c'
			isPut = arg2[-1] == 'p'
			if not (isCall or isPut) :
				await legacySend( ctx=ctx, text=f'Specify c or p - Found {arg2[-1]}')
				return
			strike = arg2[:-1]
			conData = strat.findContractWithPrice( float(strike), arg2[-1])
			symbol = conData[0]
			price = arg3
			if arg3 is None : #figure out a price!!@!! *******************************************************************
				lowPrice = conData[1]
				lastPrice = conData[2]
				price = lowPrice
				await legacySend( ctx=ctx, text=f'No price specified, lowPrice {lowPrice} - last price {lastPrice}')
			
			await legacySend( ctx=ctx, text=f'Buying - {symbol} {strike} {'c' if isCall else 'p'} @ ${price}')
			
			myCon = dp.placeOptionOrder(symbol, price, ticker = 'SPX', side='buy_to_open', quantity='1', type='limit', duration='day', tag='gui', preview="false")
			txtOut = f'{myCon}'
			orders.append( myCon['order'] )
			await legacySend( ctx=ctx, text=txtOut )
			
		else :
			await legacySend( ctx=ctx, text=f'Example - }}trade buy 5750c 0.30')
	elif arg1 == 'cancel' :
		openOrders = getOrders()
		for o in openOrders:
			outPut = dp.cancelOrder( o['id'] )
			print(outPut)
			await legacySend( ctx=ctx, text=f'Canceled - {outPut}')
	elif arg1 == 'close' :
		price = 0
		side = 'sell_to_close'
		order_type = 'market'
		if not arg2 is None :
			price = arg2
			order_type = 'limit'
	
		positions = getPositions()
		for p in positions :
			myCon = dp.placeOptionOrder(p['symbol'], price, ticker = 'SPX', side=side, quantity='1', type=order_type, duration='day', tag='gui', preview="false")
			await legacySend( ctx=ctx, text=f'Closing - {myCon}')
		

def getOrders():
	openOrders = dp.getOrders()
	orders=[]
	for o in openOrders['order'] :
		if 'id' == o : #The payload will make it a List when multiple entries are found, otherwise it wont be
			if 'open' in openOrders['order']['status'] : orders.append(openOrders['order'])
			break
		if 'open' in o['status'] :
			orders.append(o)
	return orders

def getPositions(): # Positions - {'position': {'cost_basis': 40.0, 'date_acquired': '2024-10-07T17:39:26.519Z', 'id': 10103069, 'quantity': 1.0, 'symbol': 'SPXW241007C05750000'}}
	myPositions = dp.getPositions()
	positions = []
	try :
		#if myPositions in 'null' : return positions
		for o in myPositions['position'] :
			print(o)
			if 'cost_basis' == o : #The payload will make it a List when multiple entries are found, otherwise it wont be
				positions.append(myPositions['position'])
				break
			positions.append(o)	
	except :
		pass
	return positions

"""
Buying - SPXW241007C05750000 5750 c @ $0.35
{'order': {'id': 70125825, 'status': 'ok', 'partner_id': '30ea5c89-e029-4da3-a179-5867a8006e07'}}

Open Orders - {'order': {'id': 70125825, 'type': 'limit', 'symbol': 'SPX', 'side': 'buy_to_open', 'quantity': 1.0, 'status': 'open', 'duration': 'day', 'price': 0.35, 'avg_fill_price': 0.0, 'exec_quantity': 0.0, 'last_fill_price': 0.0, 'last_fill_quantity': 0.0, 'remaining_quantity': 1.0, 'create_date': '2024-10-07T13:50:47.298Z', 'transaction_date': '2024-10-07T13:50:47.363Z', 'class': 'option', 'option_symbol': 'SPXW241007C05750000', 'tag': 'gui'}}
"""


@bot.command(name="listg")
@commands.is_owner()
async def listg(ctx, *args):  #Needs customized so the arguements remove you from a server etc......meh
	user = str(ctx.author)
	if BOT_USER_FOR_KILL != user:
		await legacySend( ctx=ctx, text=user + " you can't kill meme!")
		return
		
	blnExit = args[0] == 'leave'
		
	txt = ""
	for guild in bot.guilds:
		if blnExit :
			blnFound = False
			for i in range(1, len(args) ):
				if args[i] in  guild.name : blnFound = True
			txt += '********** Staying in - ' if blnFound else 'Leaving - '
			if blnFound == False :
				await guild.leave() # Guild found
		txt += guild.name + '\r'
	await legacySend( ctx=ctx, text=f"{txt}")

"""
@commands.listener()
async def on_guild_join(guild):
	#cli = self.client
	ctx = bot.get_context
	await ctx.create_text_channel("📯announcements-and-suggestions")
	await ctx.create_text_channel("💼log")               
	general = find(lambda x: x.name == '📯announcements-and-suggestions',  guild.text_channels)
	if general and general.permissions_for(guild.me).send_messages:
		await ctx.send(f"Hello {guild.name}! I am {self.client.user.display_name}. Thank you for inviting me.\n\nTo see what commands I have available type `r?help`.\nIf you want to see my available AutoResponse Triggers type `gethelp`.")
"""
	
@bot.command(name="news")
async def news(ctx):
	#chnl = bot.get_channel(UPDATE_CHANNEL)
	#await ctx.send( buildNews("WEEK")[0] )
	await legacySend( ctx=ctx, text=buildNews("WEEK")[0] )

#    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
#    @commands.hybrid_command(name="adventure", aliases=["a"])
#    @commands.bot_has_permissions(add_reactions=True)

@bot.command(name="test")
async def test(ctx):
	if BOT_USER_FOR_KILL != str(ctx.author): return   #Honestly NEEDS to use   ctx.author.id
	channel = ctx.channel
	#channel = bot.get_channel(1259405215820550255)  #Testing channel
	permissions = channel.permissions_for(ctx.guild.me)
	textable = permissions.send_messages == True
	imageable = permissions.attach_files == True
	await legacySend( ctx, channel=channel, fileName=f'stock-chart.png')
	await legacySend( ctx, channel=channel, text=f'Text {textable} and Images {imageable}')

async def legacySend(ctx=None, channel=None, text=None, fileName=None, ephemeral=False):  #When not using /commands Check channel permissions before sending ALWAYS
	if channel == None : channel = ctx.channel

	if "private" in channel.type :  #"text" in channel.type = in a Channel.     May also use if channel.guild is None
		permissions = ctx.permissions
	else :
		permissions = channel.permissions_for(channel.guild.me) 
	if text != None and permissions.send_messages == True : await channel.send( text )
	if fileName != None and permissions.attach_files == True :
		await channel.send(file=discord.File(open('./' + fileName, 'rb'), fileName))

@bot.command(name="list")
async def list(ctx):
	await legacySend( ctx=ctx, text=str(dp.pullLogFileList()) )

@bot.command(name="pc")
async def pc(ctx, arg1, arg2="spx"):
	global gexDataToday, gexDataFileName
	
	try:
		if 'help' in arg1 :#or len(args) < 3: 
			await ctx.send( '}pc Options Price Chart.\rSimply type =pc SPY/SPX day strikec or strikep.\r=pc SPX 11-06 4450c 4425p 4500c\rYou can also type =list to get a list of available days' )
			return
		
		chart = dc.drawPriceChart( "SPX", gexDataFileName, gexDataToday, [arg1, arg2] )
		await legacySend( ctx=ctx, fileName = chart )
	except:
		await legacySend( ctx=ctx, text="Error drawing price chart" )
		#await ctx.send( "Error drawing price chart" )

@bot.tree.command(name="pc")
@commands.is_owner()
async def slash_command_pc(intr: discord.Interaction, strike1: str = "all", strike2: str = "spx"):
	perms = await checkInteractionPermissions( intr )
	await intr.response.defer(thinking=True, ephemeral=perms[3]==False)
	try: 
		ticker = 'SPX'
		fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
		file = fileList[-1]
		gexData = dp.pullLogFile(file, discordBot=True)
		chart = dc.drawPriceChart( ticker, file, gexData, [strike1, strike2] )
		await intr.followup.send(file=discord.File(open('./' + chart, 'rb'), chart))
	except: await intr.followup.send("No image permissions")

@bot.command(name="heatmap")
async def heatmap(ctx, *args):
	print("Fetching % based heatmap")
	try:
		fileName = dc.drawPrecentageHeatMap('SPX', 100, 1)
		await legacySend( ctx=ctx, fileName=fileName )
	except: pass
	
@bot.command(name="ph")
async def ph(ctx, *args):  #Grabs Morning GEX Chart for Xdte 
	try:
		ticker = 'SPX'
		index = int( args[0] )
		fileList = [x for x in dp.pullLogFileList() if ((ticker=='SPX') ^ ('SPY' in x))]
		file = fileList[ index ]

		gexData = dp.pullLogFile(file)
		day = file.replace('-datalog.json', '')
		minute = next(iter(gexData))
		price = gexData[minute]['price']
		strikes = gexData[minute]['data']
		chart = dc.drawGEXChart('SPX', 40, 0, chartType = 0, strikes = strikes, expDate = day, price = price)
	
		await legacySend( ctx=ctx, fileName=chart )
	except:
		await legacySend( ctx=ctx, text="Error drawing price chart" )

def getDateOfFriday():
	today = datetime.date.today()
	return str(today + datetime.timedelta( (4-today.weekday()) % 7 ))
	
def grabFridayCombo(dte):
	exps = dp.getExpirations('SPX')
	today = str(datetime.date.today()).split(":")[0]
	#if today == exps[0] : exps.pop(0)
	fridayIndex = exps.index(getDateOfFriday())
	exps = exps[:fridayIndex + 1]
	if 0 < dte < 5 : exps = exps[:dte+1]
	
	days = []
	startDate = None
	lastDate = ""
	for day in exps:
		opts = dp.getOptionsChain("SPX", 0, date=day )
		lastDate = opts[0]
		if startDate == None : startDate = opts[0]
		days.append( dp.getGEX( opts[1] ) )
		
	combinedData = days[0]
	for d in range( 1, len(days) ):
		nd = days[d]
		for strike in nd :
			oStrike = next((x for x in combinedData if x[dp.GEX_STRIKE] == strike[dp.GEX_STRIKE]), None)
			if oStrike == None :	
				combinedData.append( strike )
				continue
			oStrike[dp.GEX_TOTAL_GEX] += strike[dp.GEX_TOTAL_GEX]
			oStrike[dp.GEX_TOTAL_OI] += strike[dp.GEX_TOTAL_OI]
			oStrike[dp.GEX_CALL_GEX] += strike[dp.GEX_CALL_GEX]
			oStrike[dp.GEX_PUT_GEX] += strike[dp.GEX_PUT_GEX]
			oStrike[dp.GEX_CALL_OI] += strike[dp.GEX_CALL_OI]
			oStrike[dp.GEX_PUT_OI] += strike[dp.GEX_PUT_OI]
			oStrike[dp.GEX_CALL_VOLUME] += strike[dp.GEX_CALL_VOLUME]
			oStrike[dp.GEX_PUT_VOLUME] += strike[dp.GEX_PUT_VOLUME]
			#oStrike[dp.GEX_] += strike[dp.GEX_]
			#oStrike[dp.GEX_] += strike[dp.GEX_]
	#drawGEXChart(ticker, count, dte, chartType = 0, strikes = None, expDate = 0, price = 0, RAM=False):
	price = dp.getPrice("SPX", combinedData )
	fn = dc.drawGEXChart("SPX", 40, 0, 5, combinedData, expDate=f'{lastDate}-C', price=price)
	return fn

def getToday():
	dateAndtime = str(datetime.datetime.now()).split(" ")
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 10000) + (float(tmp[1]) * 100) + float(tmp[2])
	return (dateAndtime[0], minute)

TodaysUsers = {}
TodaysUsers['today'] = getToday()[0]
def confirmUser(userID):
	global TodaysUsers
	tday = getToday()
	if not tday[0] in TodaysUsers['today'] : #The cooldown Time doesnt include date, so.......reset it on new day
		#TodaysUsers = {}
		TodaysUsers['today'] = tday[0]
		for user in TodaysUsers :
			if user == "today" : continue
			TodaysUsers[user] = tday[1] - 10  #Reset cooldowns on new day or else!!!
	if userID in TodaysUsers :
		userCooldown = tday[1]-TodaysUsers[userID]
		if userCooldown > 10 :
			TodaysUsers[userID] = tday[1]
			return 0
		else :
			return 10 - userCooldown
	else :
		TodaysUsers[userID] = tday[1]
		return 0

#@app_commands.checks.has_permissions(moderate_members=True)
async def checkInteractionPermissions(intr: discord.Interaction):
	userID = intr.user.id
	coolDown = confirmUser(f'{intr.user.global_name}#{userID}')
	#intr in a Channel = 'app_permissions', 'application_id', 'channel', 'channel_id', 'client', 'command', 'command_failed', 'context', 'created_at', 'data', 'delete_original_response', 'edit_original_response', 'entitlement_sku_ids', 'entitlements', 'expires_at', 'extras', 'followup', 'guild', 'guild_id', 'guild_locale', 'id', 'is_expired', 'is_guild_integration', 'is_user_integration', 'locale', 'message', 'namespace', 'original_response', 'permissions', 'response', 'token', 'translate', 'type', 'user', 'version'
	
	if intr.guild_id is None : return (userID, coolDown, True, True)  #We are in a DM and can do anything we want
	permissions = intr.permissions
	textable = permissions.send_messages == True
	imageable = permissions.attach_files == True
	return ( userID, coolDown, textable, imageable )

@bot.command(name="listusers")
@commands.is_owner()
async def legacyListUsers(ctx, *args):
	global TodaysUsers
	txt = ""
	for name in TodaysUsers:
		txt += name + "\r"
	await legacySend( ctx=ctx, text=txt, ephemeral=True ) # ctx.send(txt, ephemeral=True) #
	
@bot.command(name="wipecooldowns")
@commands.is_owner()
async def legacyWipeCoolDowns(ctx, *args):
	global TodaysUsers
	tday = getToday()
	for name in TodaysUsers:
		if name == "today" : continue
		TodaysUsers[name] = tday[1] - 20
		#print( name, " - ", TodaysUsers[name] )
	await legacyListUsers(ctx, args)
	
	
@bot.tree.context_menu(name='Invite')
async def context_menu_Invite(intr: discord.Interaction, user: Union[discord.Member, discord.User] ):
	#user = await client.fetch_user(user_id)
	#if user:
	#await user.send("You have been invited to https://discord.gg/3YNKxx2ReP \n You can also use Smayxor anywhere with https://discord.com/oauth2/authorize?client_id=1046929513117925426")
	await intr.response.send_message(f'{user.name} you can use Smayxor here https://discord.com/oauth2/authorize?client_id=1046929513117925426')

@bot.tree.context_menu(name='FindTicker')
async def context_menu_FindTicker(intr: discord.Interaction, msg: discord.Message):

	await intr.response.send_message("Feature coming soon!", ephemeral=True)	
	
	
#@bot.event
#async def on_message(message):  #Triggered during interactions
#	await bot.process_commands(message)  #Forward message to allow Command Processing!!!!	

bot.run(BOT_TOKEN) #Last line of code, until bot is closed


"""
Polygon — Provides stock tickers, price quotes, trades, and aggregates. Covers equities, forex, cryptocurrencies, and other assets.
IEX Cloud offers real-time and historical stock prices, fundamentals, earnings, dividends, and advanced stats.
Intrinio — Features international stock data plus fundamentals, insider trading, SEC filings, earnings, and more.
Alpha Vantage — Provides free and paid stock APIs with real-time data, fundamentals, and technical indicators.
Tiingo — Supplies historical data, end-of-day prices, fundamentals, news sentiment, and analyst estimates.
Finnhub — Offers real-time and historical stock data globally along with fundamentals, earnings, and economic data.
Tradier — Provides market data APIs plus brokerage APIs for trading. Covers stocks, options, futures, and cryptocurrencies.
Quandl — Large database of financial, alternative, and other time-series data including equities."""