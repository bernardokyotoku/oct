import numpy as np
import logging
import sys
import cPickle
from configobj import ConfigObj
from validate import Validator
from function import resample, transform, renormalize

flags = [
	'calibrate-spectrum',
	'x',
	'get-p',
	'resample-d',
	'fft',
	'non-cor-fft',
	'line',
	'scan-3D',
	'scan-continuous',
	'scan-single',
	'load',
	'store',
	'plot',
	'img-plot',
	]

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('-i',dest='input_filename')
	parser.add_argument('-o',dest='output_filename')
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true') 
	return parser.parse_args()

arg = parse()
validator = Validator({'log':function.log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

for i in flags:
	if getattr(arg,i.replace('-','_')):
		fun = getattr(function,i)
		data = fun(config,data)	

fifo = open(arg.input_filename)
out = open(arg.output_filename,'w',0)

while not finished:
	data = cPickle.load(fifo)
	data = resample(data)
	data = transform(data)
	data = abs(data)
	data = renormalize(data)
	out.write(data)
fifo.close()
out.close()
