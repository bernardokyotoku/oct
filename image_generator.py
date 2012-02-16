#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import cPickle
from time import sleep
import Image

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "Raw data simulator."
	parser.add_argument('-o',dest='out_file', default='raw_data')
	parser.add_argument('--count',dest='count', default=1000000000)
	parser.add_argument('--height',dest='height', default=240)
	parser.add_argument('--width',dest='width', default=320)
	parser.add_argument('-',dest='stdout', action='store_true')
	parser.add_argument('-d', action='store_true') 
	parser.add_argument('-n', action='store_true') 
	return parser.parse_args()
arg = parse()

def matrix(phase):
	def gauss(x,x0,d):
		return np.exp(-((x-x0)/d)**2)
	def line(x):
		carrier = np.sin(0.1*x*np.linspace(0,1000,arg.width))
		envelope = gauss(np.linspace(0,10,arg.width),5,1)
		return envelope*carrier
	frequencies = 2*np.sin(phase + 2*np.linspace(0,2,arg.height)) + 3
	return np.vstack([line(f) for f in frequencies])

print arg.out_file

def amplify(image,factor):
	return np.float32(image)*factor

def getType(filename):
	return filename.split('.')[1].upper()

#filetype = getType(arg.out_file)
def main():
	i = 0
	fd = open(arg.out_file,'w',0)
	pickler = cPickle.Pickler(fd,cPickle.HIGHEST_PROTOCOL)
	while True:
		i += 1
		moving_factor = 0.1
		print "Creating image", i, "."
		#m = amplify(matrix(i*moving_factor),factor=2*16-1)
		m = matrix(i*moving_factor)
		#m = np.uint16(m)
		#mode = "L"
		#size = m.T.shape
		#data = m.data
		#image = Image.frombuffer(mode,size, data,"raw",mode,0,1)
		#plt.figure()
		#plt.imshow(m)
		#plt.show()
		try:
			pickler.dump(m)
		#	image.save(fd,filetype)
		except Exception, e:
			print "Error", e.message
			break
		#dump(image(t),fd)
		sleep(1)
		if (i >= int(arg.count)):
			print "exit"
			return True
	fd.close()
	if not arg.d:
		return True

if __name__ == "__main__":
	exit = False
	while not exit or arg.n:
		main()
