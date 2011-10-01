#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import cPickle
import Image
from configobj import ConfigObj
from validate import Validator
from function import transform,log_type,resample


def main(config,arg):
	in_fd = open(arg.in_file)
	out_fd = open(arg.out_file,'w',0)
	while True:
		try:
			data = cPickle.load(in_fd)
		except Exception:
			break
		parameters = {"brightness":-100,"contrast":1}
		data = resample(data,config)
		data = transform(data.T).T
		data = 10*np.log(data)
		data = renormalize(data,parameters)
		data = np.ascontiguousarray(np.uint8(data))
		image = Image.frombuffer("L",data.shape,data=data.data)
		try:
			image.save(out_fd,format='jpeg')
		except Exception:
			break
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
	parser.add_argument('-i',dest='in_file', default=config['in_file'])
	parser.add_argument('-o',dest='out_file', default=config['out_file'])
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true',default=False) 
	return parser.parse_args()

config = parse_config()
arg = parse_arguments()
logging.basicConfig(filename='oct.log',level=config['log'])

while __name__ == "__main__":
	repeat = main(config,arg)
	if not repeat:
		break
	 
	
