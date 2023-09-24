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
		x2, y2 = 0.0, -75.0

		flippy = ((angle // 180) * -2) + 1  #		flippy = -1 if angle // 180 else 1
		xAngle = (abs((((angle // 90) % 2) * 90) - (angle % 90)) * flippy) / 90
		yAngle = (((angle - 90) - ((angle // 180) * 180)) * flippy) / 90
		def drawDot(x, y):
			newX = 150 + (x*xAngle) - (y*yAngle)
			newy = 150 + (x*yAngle) + (y*xAngle)
			canvas.create_line(newX,newy,newX + 1,newy + 1, fill=COLORS[colorIndex], width=3)
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
