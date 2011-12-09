import Tkinter as tk
from Tkinter import Canvas, Frame, Button, Tk, LEFT, RIGHT, BOTTOM, TOP

class main(Frame):
	def __init__(self,master):
		root_frame = Frame(master)
		root_frame.pack()

		right_frame = Frame(root_frame,bg="white")
		right_frame.pack(side=RIGHT)

		self.button = Button(right_frame, text="quit", 
				fg="red", command=root_frame.quit)
		self.button.pack(side=TOP)

		self.camera_canvas = Canvas(right_frame,bg="red")
		self.camera_canvas.pack(side=BOTTOM)

		self.plot_canvas = Canvas(root_frame,width=100,bg="blue")
		self.plot_canvas.pack(side=LEFT)

		self.tomogram_canvas = Canvas(root_frame,bg="black")
		self.tomogram_canvas.pack(side=LEFT)



root = tk.Tk()
app = main(root)

root.mainloop()
