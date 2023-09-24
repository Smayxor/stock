from tkinter import *
import time
import threading

angle = 0.0
loop = False
COLORS = ["#F00", "#0F0", "#00F", "#F0F", "#0FF", "#FF0", "#FFF"]
colorIndex = 0

def clickButton():
	global loop, angle, colors, colorIndex
	loop = not loop
	if loop : x.start()

def tick():
	global loop, angle, colors, colorIndex, canvas, win
	while loop:
		angle = (angle + 5.0) % 360
		colorIndex = (colorIndex + 1) % 7
		x1, y1 = -50.0, -50.0
		x2, y2 = 0.0, -100.0
		"""
		xAngle = 0.0
		yAngle = 0.0
		if angle < 91.0 :
			xAngle = angle
			yAngle = angle - 90.0
		elif angle < 181.0 :
			xAngle = 90.0 - (angle - 90.0)
			yAngle = angle - 90.0
		elif angle < 271.0 :
			xAngle = 90.0 - (angle - 90.0)
			yAngle = 270.0 - angle
		else :
			xAngle = angle - 360.0
			yAngle = 270.0 - angle
		xAngle = xAngle / 90.0   #make angles a % of movement along each axis
		yAngle = yAngle / 90.0
		"""  #The Above if statements have been shrunk to the equation below
		#flippy = ((angle // 180) * -2) + 1
		#xAngle = (abs((((angle // 90) % 2) * 90) - (angle % 90)) * flippy) / 90
		xAngle = -(abs(180 - ((angle + 90) % 360)) - 90) / 90
		yAngle = -(abs(180 - angle) - 90) / 90

		def drawDot(x, y):
			newX = 150 + (x*xAngle) - (y*yAngle)
			newy = 150 + (x*yAngle) + (y*xAngle)
			canvas.create_line(newX,newy,newX + 1,newy + 1, fill=COLORS[colorIndex], width=3)
		#canvas.delete("all")
		drawDot(x1, y1)
		drawDot(x2, y2)
		win.update()

win = Tk()
win.geometry("400x400")
Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')

canvas = Canvas(win, width=400, height=400)
canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
canvas.configure(bg="#000000")

x = threading.Thread(target=tick)

mainloop()
