#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import cPickle
import Image
from configobj import ConfigObj
from validate import Validator
from acquirer import transform,log_type,resample

def plot(image):
	plt.imshow(image)
	plt.show()


def main(config,arg):
	in_fd = open(arg.in_file)
	out_fd = open(arg.out_file,'w',0)
	#while True:
	try:
		data = cPickle.load(in_fd)
	except Exception:
		return#break
	parameters = {"brightness":-00,"contrast":8}
#	data = resample(data.T,config)
	data = transform(data)
	#data = 10*np.log(data)
	data = renormalize(data,parameters)
	data = np.ascontiguousarray(np.uint16(data))
	print "max=", np.max(data)
	print "min=", np.min(data)
	print "shape=", data.T.shape
	#plot(data)
	#image = Image.frombuffer(mode="L", size=data.shape, data=data.data, "L", 0, 1)
	image = Image.frombuffer("L", data.T.shape, data.data, "raw","L", 0, 1)
	try:
		image.save(out_fd,format='jpeg')
	except Exception:
		return#break

	in_fd.close()
	out_fd.close()
	return arg.daemon

def renormalize(data,parameters):
	data = data + parameters["brightness"]
	data = data * parameters["contrast"]
	return data

def parse_config():
	validator = Validator({'log':log_type,'float':float})
	config = ConfigObj('config.ini',configspec='configspec.ini')
	if not config.validate(validator):
		raise Exception('config.ini does not validate with configspec.ini.')
	return config

def parse_arguments():
	import argparse
	flags = ["daemon"]
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('-i',dest='in_file', default="raw_data")#config['in_file'])
	parser.add_argument('-o',dest='out_file', default="df.jpg" )#config['out_file'])
	for flag in flags: 
		parser.add_argument('--' + flag,action='store_true',default=False) 
		return parser.parse_args()

if __name__ == "__main__":
	config = parse_config()
	arg = parse_arguments()
	logging.basicConfig(filename='oct.log',level=config['log'])
	repeat = main(config,arg)
	 
	
