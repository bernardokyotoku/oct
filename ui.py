import Tkinter as tk
from Tkinter import Canvas, Frame, Button, Tk, LEFT, RIGHT, BOTTOM, TOP, Label, StringVar, Radiobutton,W,Menu

class main(Frame):
	def __init__(self,master):
		root_frame = Frame(master)
		root_frame.pack()

		menubar = Menu(master)

		menufile = Menu(menubar,tearoff=0)
		menufile.add_command(label="Open")
		menufile.add_command(label="Save")
		menubar.add_cascade(label="File",menu=menufile)

		master.config(menu=menubar)

		right_frame = Frame(root_frame,bg="white")
		right_frame.pack(side=RIGHT)

		self.button = Button(right_frame, text="quit", 
				fg="red", command=root_frame.quit)
		self.button.pack(side=TOP)

		MODES = [("3D","rectangle"),("2D","line")]
		self.mode = StringVar()
		self.mode.set("line")
		for text,mode in MODES:
			b = Radiobutton(right_frame,text=text,
					variable=self.mode,value=mode)
			b.pack(anchor=W)

		self.camera_canvas = Canvas(right_frame,bg="red")
		self.camera_canvas.bind("<ButtonPress-1>", self.pressed)
		self.camera_canvas.bind("<B1-Motion>", self.moved)
		self.camera_canvas.bind("<ButtonRelease-1>", self.released)
		self.camera_canvas.pack(side=BOTTOM)

		self.plot_canvas = Canvas(root_frame,width=100,bg="blue")
		self.plot_canvas.pack(side=LEFT)

		self.tomogram_canvas = Canvas(root_frame,bg="black")
		self.tomogram_canvas.pack(side=LEFT)

	def pressed(self,event):
		self.start_pos = (event.x,event.y)

	def moved(self,event):
		self.camera_canvas.delete(tk.ALL)
		coordinates = self.start_pos + (event.x,event.y)
		selector = {	"line":self.camera_canvas.create_line,
				"rectangle":self.camera_canvas.create_rectangle}[self.mode.get()]
		selector(*coordinates)

	def released(self,event):
		pass

	def plot(points):
		ax = self.plot_canvas
		p2 = points.roll(1)
		a = zip(points,p2)
		a.pop()
		lines = [(p[0],y1,p[1],y1+1) for p in a]
		create_line = lambda coordinate:ax.create_line(*coordinate)
		map(create_line,lines)




root = tk.Tk()
app = main(root)

root.mainloop()
