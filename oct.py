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
	parser.add_argument('-o',dest='filename')
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true') 
	return parser.parse_args()

arg = parse()
validator = Validator({'log':function.log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
a = config.validate(validator)
print a
if not a:
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

data = []
if arg.filename:
	config['filename']=arg.filename if arg.filename else 'data.dat'
	
for i in flags:
	funame = i.replace('-','_')
	print funame

	if getattr(arg,funame):
		fun = getattr(function,funame)
		data = fun(config,data)	


