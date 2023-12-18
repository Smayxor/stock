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
import requests

init = json.load(open('apikey.json'))
BOT_TOKEN = init['BOT_TOKEN']
BOT_APP_ID = init['DISCORD_APP_ID']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
TENOR_API_KEY = init['TENOR_API_KEY']
UPDATE_CHANNEL = init['UPDATE_CHANNEL']    #Channel ID stored as Integer not string

WEEKDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "DAILY IV ", "GEX ", "JSON ", "ATR+FIB ", "LAST DTE ", "LOG-DATA ", "CHANGE IN GEX ", "SKEWED GEX ", "HEAT MAP "]
CHART_GEX = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_DAILYIV = 3
CHART_ROTATE = 4
CHART_JSON = 5
CHART_ATR = 6
CHART_LASTDTE = 7
CHART_LOG = 8
CHART_CHANGE = 9
CHART_SKEW = 10
CHART_HEATMAP = 11

#Declarations for slash commands
url = "https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands"
headers = { "Authorization": "Bot " + BOT_TOKEN}
slash_command_json = {
	"name": "gex", "type": 1, "description": "Draw a GEX/DEX chart", "options": [ 
	{ "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, 
	{ "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, 
	{ "name": "count", "description": "Strike Count", "type": 4, "required": False }, 
	{ "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [
		{ "name": "Normal", "value": "Normal"  }, 
		{ "name": "Rotated", "value": "R" }, 
		{ "name": "Volume", "value": "V" }, 
		{ "name": "JSON", "value": "JSON"  }, 
		{ "name": "HEATMAP", "value": "HEATMAP"  }
	]}   
] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "8ball", "type": 1, "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "sudo", "type": 1, "description": "Stuff you cant do on Smayxor", "options":[{ "name": "command", "description": "Super User ONLY!", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "news", "type": 1, "description": "Gets todays events", "options":[{ "name": "days", "description": "How many days", "type": 3, "required": False, "choices": [{"name": "today", "value": "TODAY"}, {"name": "week", "value": "WEEK"}, {"name": "all", "value": "ALL"}, {"name": "1", "value": "1"}, {"name": "2", "value": "2"}, {"name": "3", "value": "3"}, {"name": "4", "value": "4"}, {"name": "5", "value": "5"}] }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

#Removes slash commands
#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/COMMAND_ID", headers=headers) )
#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/1089558674533523486", headers=headers) )

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

lastNewsDay = -1
todaysNews = None
class NewsData():
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

def fetchNews():
	global lastNewsDay, todaysNews
	today = datetime.date.today()
	if lastNewsDay == today : return todaysNews
	lastNewsDay = today
	
	COLUMN = ['', ' ', '\t ', ' Actual: ', ' Forecast: ', ' Prev: ', '', '', '', '', '', '']
	url = "https://www.marketwatch.com/economy-politics/calendar"
	news = []
	try :
		data = requests.get(url=url)
		text = ""
		tables = data.text.split( "<tbody>" )
		txt = tables[1].split("</tbody>")[0] + tables[2].split("</tbody>")[0]
		txt = txt.replace('<b>', '', 1).replace('<tr>','').replace('S&amp;P', '').replace('<td style="text-align: left;">', '').replace('\r', '').replace('\n', '').split('<b>')
		for t in txt:
			t = t.replace('<td>', '').split('</tr>', 1)
			day = t[0].replace('</td>', '').replace('</b>', '').replace('. ', '.').replace('.', ' ')
			if ('FRIDAY' in day) and (15 <= int(day.split(' ')[2]) <= 21) : day = day.replace('FRIDAY', 'MOPEX - FRIDAY')
			newsD = NewsData( day )
			for r in t[1].split('</tr>'):
				event = ""
				counter = 0
				for td in r.split('</td>'):
					if counter == 0:
						if len(td) == 7 : td = td.replace(' ', '  ')
						event = td
					else:
						while (counter == 1) and (len(td) < 40): td = td + ' '	
						if len(td) > 0: event += COLUMN[counter] + td
					counter += 1
				newsD.addEvent( event )
			news.append( newsD )
	except:
		print("BOOM")
		#for x in news: print( x.toString() )
		#news.append( NewsData(today) )
	todaysNews = news
	return news





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
	elif arg == 'R': return CHART_ROTATE
	elif arg == 'JSON': return CHART_JSON
	elif arg == 'ATR': return CHART_ATR
	elif arg == 'LD': return CHART_LASTDTE
	elif arg == 'CHANGE': return CHART_CHANGE
	elif arg == 'SKEW': return CHART_SKEW
	elif arg == 'HEATMAP': return CHART_HEATMAP
	else: return CHART_GEX

@bot.tree.command(name="gex", description="Draws a GEX chart")
async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, count: int = 40, chart: str = "R"):
	global tickers, updateRunning, needsQueue
	await intr.response.defer(thinking=True)
	ticker = ticker.upper()
	chartType = getChartType( chart )
	if chartType == CHART_HEATMAP:
		fn = dc.drawHeatMap(ticker, count, dte)
	else:
		fn = dc.drawGEXChart(ticker, count, dte, getChartType(chart))
	if fn == "error.png": await intr.followup.send("Failed to get data")
	else:
		try: await intr.followup.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await intr.followup.send("No image permissions")
		
@bot.command(name="pump")
async def command_pump(ctx, *args): await ctx.send( getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
@bot.command(name="dump")
async def command_dump(ctx, *args): await ctx.send( getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )
@bot.command(name="tits")
async def command_tits(ctx, *args): await ctx.send( getTenorGIF( random.choice(titties) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="ass")
async def command_ass(ctx, *args): await ctx.send( getTenorGIF( random.choice(asses) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="gm")
async def command_gm(ctx, *args): await ctx.send( getTenorGIF( random.choice(gms) if len( args) == 0 else enc(' '.join(args)) ) )
	
@bot.tree.command(name="8ball", description="Answers your question?")
async def slash_command_8ball(intr: discord.Interaction, question: str):
	future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good', 'You should ask Siri, that slut.', 'I rolled a dice to answer you, and it said the answer is C.', 'Follow your heart, I wouldn\'t trust your mind though.', 'I don\'t know and I don\'t care.', 'Did you ask ChatGPT?', 'Just google it.']
	if "?" in question:
		response = "Question: " + question + "\rAnswer: " + random.choice(future)
	else:
		response = "Please phrase that as a question"
	await intr.response.send_message(response)

def buildNews(days):
	today = datetime.datetime.now().weekday()
	if today > 4 : today = 0
	day = 0
	if days.isnumeric() : day = today + int(days) - 1
	elif days == "TODAY" : day = today
	elif days == "WEEK" : day = -1
	elif days == "ALL" : day = -2
		
	events = fetchNews()
	txt1 = ''
	txt2 = ''
	blnFirst = True
	for j in range(len(events) - 0):
		if day != -2:
			if day == -1:
				if j > 4: continue
			elif j < today or (j > day): continue
		tmp = events[j].toString()
		if (blnFirst == True) and (len(tmp) + len(txt1) > 1999) : blnFirst = False
		if blnFirst : txt1 += tmp
		else: txt2 += tmp
	return (txt1, txt2)

@bot.tree.command(name="news")
async def slash_command_news(intr: discord.Interaction, days: str = "TODAY"):	
	await intr.response.defer(thinking=True)

	finalMessage, nextMessage = buildNews(days)
	chnl = bot.get_channel(intr.channel.id)
	try: 
		#await intr.response.send_message( finalMessage )
		await intr.followup.send( finalMessage )
	except Exception as e: 
		try: await chnl.send( finalMessage )
		except Exception as er: print("News BOOM", er)
	if len(nextMessage) != 0:
			
		try: await chnl.send( nextMessage )	
		except Exception as e: print("News 2 BOOM", e)

@bot.tree.command(name="sudo")
@commands.is_owner()
async def slash_command_sudo(intr: discord.Interaction, command: str):
	global tickers, updateRunning, auto_updater, update_timer
	user = str(intr.user)
	args = command.upper().split(' ')
	print( args )
	if BOT_USER_FOR_KILL != user:
		await intr.response.send_message(user + " you can't kill meme!")
		return
	elif args[0] == "KILL" :
		await intr.response.send_message(user + " triggered shutdown")
		await bot.close()
		await bot.logout()
		exit(0)
	elif args[0] == "UPDATE" :
		await intr.response.send_message(user + " requested code update")
		print("getting update")
		#fileName = args[1].lower()
		files = ['discordbot.py', 'datapuller.py', 'drawchart.py']
		for fileName in files:
			r = requests.get(url=f'https://raw.githubusercontent.com/Smayxor/stock/main/{fileName}')
			print("recieved file")
			with open(fileName, "wb") as outfile:
				outfile.write(r.content)
		exit(9)
		await bot.close()
		await bot.logout()
	print("Finished SUDO")

dailyTaskTime = datetime.time(hour=13, minute=0, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime)
async def dailyTask():
	global tickers
	chnl = bot.get_channel(UPDATE_CHANNEL)
	if datetime.datetime.now().weekday() > 4 : 
		await chnl.send( buildNews("WEEK")[0] )
		return
	print("Daily Task Execution")
	await chnl.send("Fethcing Morning Charts")
	await chnl.send( buildNews("TODAY")[0] )
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await intr.followup.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await intr.followup.send("No image permissions")

dailyTaskTime2 = datetime.time(hour=14, minute=31, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime2)
async def dailyTask2():
	global tickers
	if datetime.datetime.now().weekday() > 4 : return
	chnl = bot.get_channel(UPDATE_CHANNEL)
	print("Daily Task Execution 2")
	dp.findSPY2SPXRatio()
	await chnl.send("Fethcing Morning Charts")
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await intr.followup.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			chnl = bot.get_channel(1156977360881586177)
			await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await intr.followup.send("No image permissions")
	logFutureDTEs() #For Heatmap

blnFirstTime = True
@bot.event
async def on_ready():
	global blnFirstTime
	if blnFirstTime :
		#channelUpdate.start()
		dailyTask.start()
		dailyTask2.start()
		blnFirstTime = False
	"""		
	@bot.command(name="s")
	async def get_gex(ctx, *args):
		global tickers, updateRunning
		clearStoredStrikes()
		chnl = bot.get_channel(UPDATE_CHANNEL)
		await chnl.send("Fethcing Morning Charts")
		tickers.append( ("SPX", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		tickers.append( ("SPY", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
	"""	
@bot.command(name="leaveg")
@commands.is_owner()
async def leaveg(ctx, *, guild_name):
	user = str(intr.user)
	if BOT_USER_FOR_KILL != user:
		await intr.response.send_message(user + " you can't kill meme!")
		return
	guild = discord.utils.get(bot.guilds, name=guild_name) # Get the guild by name
	if guild is None:
		print("No guild with that name found.") # No guild found
		return
	await guild.leave() # Guild found
	await ctx.send(f"I left: {guild.name}!")
	
@bot.command(name="news")
async def news(ctx):
	#chnl = bot.get_channel(UPDATE_CHANNEL)
	await ctx.send( buildNews("WEEK")[0] )

@bot.command(name="list")
async def list(ctx):
	await ctx.send( str(dp.pullLogFileList()) )

@bot.command(name="pc")
async def pc(ctx, *args):
	try:
		if 'help' in args[0] :#or len(args) < 3: 
			await ctx.send( '}pc Options Price Chart.\rSimply type =pc SPY/SPX day strikec or strikep.\r=pc SPX 11-06 4450c 4425p 4500c\rYou can also type =list to get a list of available days' )
			return
		ticker = 'SPX' if args[0].upper() == 'SPX' else 'SPY'
		fileList = [x for x in dp.pullLogFileList() if ((ticker=='SPX') ^ ('SPY' in x))]
		
		if args[1].replace('-', '').isnumeric() : 
			file = [x for x in fileList if args[1] in x][0]
			args = args[2:]
		else : 
			file = fileList[-1]
			args = args[1:]

		gexData = dp.pullLogFile(file)
		chart = dc.drawPriceChart( ticker, file, gexData, args )
	
		await ctx.send( file=discord.File(open('./' + chart, 'rb'), chart) )
	except:
		await ctx.send( "Error drawing price chart" )

@bot.command(name="heatmap")
async def heatmap(ctx, *args):
	print("Fetching % based heatmap")
	try:
		fileName = dc.drawPrecentageHeatMap('SPX', 100, 1)
		await ctx.send( file=discord.File(open(f'./{fileName}', 'rb'), fileName) )
	except: pass
	
@bot.command(name="ph")
async def ph(ctx, *args):
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
	
		await ctx.send( file=discord.File(open('./' + chart, 'rb'), chart) )
	except:
		await ctx.send( "Error drawing price chart" )

def logFutureDTEs():
	exps = dp.getExpirations('SPX')
	today = str(datetime.date.today()).split(":")[0]
	fileName = f'./heatmap/SPX-{today}.json'
	if today == exps[0] : exps.pop(0)
	exps = exps[:5]
	
	date1 = datetime.datetime.strptime(today, "%Y-%m-%d")  #dp.getOptionsChain figures out date from a Xdte........
	def convertDate2DTE(strDate):
		date2 = datetime.datetime.strptime(strDate, "%Y-%m-%d")
		timedelta = str(date2 - date1).split(" ")[0]
		print( timedelta )
		return timedelta
	days = {}
	for day in exps:
		strDTE = convertDate2DTE( day )
		opts = dp.getOptionsChain("SPX", strDTE)
		days[day] = dp.getGEX( opts[1] )

	with open(fileName,'w') as f: 
		json.dump(days, f)
	dp.cleanHeatmaps()

bot.run(BOT_TOKEN) #Last line of code, until bot is closed
