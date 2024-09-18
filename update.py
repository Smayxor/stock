import datetime
import time
import ujson as json
import sys
import requests

print("getting update")
files = ['datapuller.py', 'data-logger.py', 'drawchart.py', 'gexgui.py', 'signals.py']
for fileName in files:
	r = requests.get(url=f'https://raw.githubusercontent.com/Smayxor/stock/main/{fileName}')
	print("recieved file")
	with open(f'./{fileName}', "wb") as outfile:
		outfile.write(r.content)