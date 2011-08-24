import Tkinter as tk
import numpy as np
import ImageTk,Image
# create the window
root = tk.Tk()
root.title("OpenOCT")
root.geometry("640x510")

# create a frame in the window to hold widgets
app = tk.Frame(root)
app.grid()

# create a label in the frame
lbl = tk.Label(app, text = "Hi, my name is Greer!")
lbl.grid()

# kick off the windows loop
root.mainloop()

data = np.arange(200*300,dtype=np.int32)
image = Image.frombuffer('I',(200,300),data=data.data)
# load background image
def main():
	room_image = ImageTk.PhotoImage(image)
	background = room_image
	the_room = tk.Room(image = room_image,
			screen_width = 200,
			screen_height = 300,
			fps = 50)
	tk.add(the_room)

	main()
