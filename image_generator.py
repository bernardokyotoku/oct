import numpy as np
import matplotlib.pyplot as plt
from cPickle import dump, HIGHEST_PROTOCOL
from time import sleep
import Image

flags=['d']
def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "Raw data simulator."
	parser.add_argument('-o',dest='out_file', default='raw_data')
	parser.add_argument('-count',dest='count', default=1000000000)
	parser.add_argument('-height',dest='height', default=480)
	parser.add_argument('-width',dest='width', default=640)

	for flag in flags:
		parser.add_argument('-' + flag, action='store_true') 
	return parser.parse_args()
arg = parse()

def gauss(x,x0,d):
    return np.exp(-((x-x0)/d)**2)

line = lambda x:gauss(np.linspace(0,10,arg.width),5,1)*np.sin(0.1*x*np.linspace(0,1000,arg.width))

image = lambda y: np.vstack([line(x) for x in 2*np.sin(y + 2*np.linspace(0,2,arg.height)) + 3])
i=0
while True:
	fd = open(arg.out_file,'w',0)
	while True:
		i += 1
		print i
		m = 255*np.float32(image(i*0.1))
		here = Image.frombuffer(mode = 'F',size=m.T.shape, data=m.data)
		here = here.convert('L')
		plt.figure()
		plt.imshow(here)
		plt.show()
		try:
			here.save(fd,'jpeg')
		except Exception, e:
			print e
			break
		#dump(image(t),fd)
		sleep(0.1)
		if not arg.d or (i >= int(arg.count)):
			break
	fd.close()
	if  arg.d:
		break
