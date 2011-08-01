import numpy as np
import function
import logging
from configobj import ConfigObj
from validate import Validator

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	flags = [
		'horz-cal',
		'plot',
		'img-plot',
		'store',
		'x',
		'get-p',
		'resample',
		'fft',
		'non-cor-fft',
		'line',
		'scan-3D',
		'scan-continuous',
		'scan',
		'load',
		]
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true') 
	return parser.parse_args()

arg = parse()
args = filter(lambda element: not element.startswith('_'),dir(arg))
validator = Validator({'log':function.log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

data = []
for i in args:
	if getattr(arg,i):
		print i
		fun = getattr(function,i)
		data = fun(config,data)	


