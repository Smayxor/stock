from threading import Timer
import tkinter as tk
from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont, Image,ImageTk
import pyautogui as pyautogui
#import win32gui
import pyscreeze
#import cv2
#import numpy as np

img = None
blnTarget = False

class RepeatTimer(Timer):
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		
	def run(self):#, daemon=True):
		#self.interval = 60
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)
			
vally = 0
def timerThread():
	global img, blnTarget, vally
	if img == None : return
	#button7location = pyautogui.locateOnScreen("ClickTarget.png", confidence=0.9)
	#print( button7location )
	screenshot = ImageGrab.grab()
	try:
		locations = pyscreeze.locateAll(img, screenshot)
		xPrev, yPrev = pyautogui.position()
		for pos in locations :
			x , y = pos[0] , pos[1]
			if blnTarget : return
			blnTarget = True
			
			pyautogui.click(x, y)
	
		pyautogui.moveTo( xPrev, yPrev )
	except Exception as error :
		#print( error )
		blnTarget = False
		
	#vally += 1
	win.title( f'{blnTarget}')
	
def on_closing():
	global blnRun, timer
	blnRun = False
	#timer.cancel()
	win.destroy()
	
	
def clickButton():
	global tk_image, img, canvas
	screenshot = ImageGrab.grab()
	x, y = pyautogui.position()
	#print(x, y)
	img = screenshot.crop((x-10, y-10, x+10, y+10))
	#img = Image.new("RGB", (50, 50), "#000")
	#draw = ImageDraw.Draw(img)
	#img.paste(screenshot, (-x, -y))
	
	#tk_image = ImageTk.PhotoImage(img)
	#canvas.configure(image=tk_image)
	#canvas.image = tk_image	
	img.save("ClickTarget.png")
	

win = tk.Tk()
#win.geometry(str(2200) + "x" + str(IMG_H + 45))
width, height = 100, 100
win.geometry('%dx%d+%d+%d' % (width, height, 150, 100))
win.protocol("WM_DELETE_WINDOW", on_closing)

canvas = tk.Label()
canvas.place(x=0, y=40)
#canvas.configure(width=150, height=605, bg='black')

btnFetch = tk.Button(win, text="Grab", command=clickButton, width=8)
btnFetch.place(x=0, y=0)

timer = RepeatTimer(5, timerThread, daemon=True)
timer.start()
timerThread()


tk.mainloop()



# Capture the entire screen
#screenshot = ImageGrab.grab()

# Save the screenshot to a file
#screenshot.save("screenshot.png")

# Close the screenshot
#screenshot.close()



#pyautogui includes an optional confidence argument that you can dial down to make the match more loose. You need to have opencv installed to use it.
#button7location = pyautogui.locateOnScreen('calc7key.png', confidence=0.6)


#import cv2
#import numpy as np
#image = cv2.imread("Large.png")
#template = cv2.imread("small.png")
#result = cv2.matchTemplate(image,template,cv2.TM_CCOEFF_NORMED)
#print np.unravel_index(result.argmax(),result.shape)


#big = PIL.Image.open("big.bmp");
#small = PIL.Image.open("small.bmp");
#locations = pyscreeze.locateAll(small, big);


#windowPosition = win32gui.GetWindowRect( win32gui.FindWindow(None, "Swords & Souls Neverseen"))


"""
import PIL
import win32gui
import pyautogui as pyautogui
import pyscreeze

Bullseye = PIL.Image.open("bullseye.bmp")
windowPosition = win32gui.GetWindowRect(
        win32gui.FindWindow(None, "Swords & Souls Neverseen"))
while True:
    image = PIL.ImageGrab.grab(windowPosition)
    locations = pyscreeze.locateAll(bullseye, image)
    for location in locations:
        x = location[0] + windowPosition[0]
        y = location[1] + windowPosition[1]
        pyautogui.click(x, y)
"""

"""
#! python3
import pyautogui, sys
print('Press Ctrl-C to quit.')
try:
    while True:
        x, y = pyautogui.position()
        positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        print(positionStr, end='')
        print('\b' * len(positionStr), end='', flush=True)
except KeyboardInterrupt:
    print('\n')
"""