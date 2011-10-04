#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import cPickle
import Image
import os
from configobj import ConfigObj
from validate import Validator
from function import transform,log_type,resample
import simplejson as json

def main(config,arg):
	source = open(arg.in_file)
	sink = open(arg.out_file,'w',0)
	adjust = open_nonblock(arg.adjust_file)
	adjust_param = config["adjust"]

	while True:
		try: data = cPickle.load(source)
		except Exception: break
		adjust_param = update_adjust(adjust_param,adjust)
		data = resample(data,config)
		data = transform(data.T).T
		data = 10*np.log(data)
		data = renormalize(data,adjust_param)
		data = np.ascontiguousarray(np.uint8(data))
		image = Image.frombuffer("L",data.shape,data=data.data)
		try: image.save(sink,format='jpeg')
		except Exception: break

	source.close()
	sink.close()
	return arg.daemon

def renormalize(data,parameters):
	data = data + parameters["brightness"]
	data = data * parameters["contrast"]
	return data

def open_nonblock(filename):
	fd = os.open(filename,os.O_RDONLY|os.O_NONBLOCK)
	return os.fdopen(fd)

def update_adjust(old_param,adjust):
	new_param = old_param 
	try: new_param = json.load(adjust) 
	except: pass
	return new_param

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
