import Tkinter as tk
import numpy as np
import ImageTk,Image
data = np.arange(200*300)

class OCTApp:
	def __init__(self,parent):
		self.parent = parent
#		self.frame = tk.Frame(parent)
#		self.frame.pack()

#		self.button1 = tk.Button(self.frame)
#		self.button1["text"]= "Hello, World!"
#		self.button1.pack()

		self.canvas = tk.Canvas(self.parent,width=300,height=200)
		self.canvas.pack()

		data = np.int32(np.random.randn(200,300))
		image = Image.frombuffer(mode='I',size=(300,200),data=data.data)

		self.im = ImageTk.PhotoImage(image)
		self.canvas.create_image(0,0,image=self.im,state=tk.NORMAL)
		tk.Misc.lift(self.canvas,aboveThis=None)
		self.canvas.update()

root = tk.Tk()
root.title("OpenOCT")
root.geometry("640x510")
app = OCTApp(root)
tk.mainloop()
