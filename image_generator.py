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
	for flag in flags:
		parser.add_argument('--' + flag, action='store_true') 
	return parser.parse_args()
arg = parse()

def gauss(x,x0,d):
    return np.exp(-((x-x0)/d)**2)

im=lambda x:gauss(np.linspace(0,10,1024),5,1)*np.sin(0.1*x*np.linspace(0,1000,1024))

image = lambda y: np.vstack([im(x) for x in 2*np.sin(y+2*np.linspace(0,2,1024))+3])
#plt.imshow(image(0.8))
#plt.show()
i=0
while True:
	fd = open(arg.out_file,'w',0)
	while True:
		i += 1
		m = 255*np.float32(image(i*0.1))
		here = Image.frombuffer(mode = 'F',size=m.shape, data=m.data)
		here = here.convert('L')
		print i
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
	if not arg.d:
		break
