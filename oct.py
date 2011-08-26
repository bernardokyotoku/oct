import numpy as np
import function
import logging
from configobj import ConfigObj
from validate import Validator

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
	parser.add_argument('-o',dest='filename',default='data.dat')
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true') 
	return parser.parse_args()

arg = parse()
validator = Validator({'log':function.log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

data = []
if arg.filename:
	config['filename']=arg.filename if arg.filename else 'data.dat'
	
for i in flags:
	function_name = i.replace('-','_')
	if getattr(arg,funame):
		fun = getattr(function,function_name)
		data = fun(config,data)	


