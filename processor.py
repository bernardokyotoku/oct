import numpy as np
import logging
import sys
import cPickle
import Image
from configobj import ConfigObj
from validate import Validator
from function import transform,log_type,resample

flags = [ ] 

validator = Validator({'log':log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('-i',dest='in_file', default=config['in_file'])
	parser.add_argument('-o',dest='out_file', default=config['out_file'])
	for flag in flags:
		parser.add_argument('--' + flag,action='store_true') 
	return parser.parse_args()

arg = parse()
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

for i in flags:
	if getattr(arg,i.replace('-','_')):
		fun = getattr(function,i)
		data = fun(config,data)	

in_file = arg.in_file if arg.in_file else config['in_file']
out_file = arg.out_file if arg.out_file else config['out_file']

while True:
	in_fd = open(in_file)
	out_fd = open(out_file,'w',0)
	while True:
		try:
			data = cPickle.load(in_fd)
		except Exception:
			break
		data = resample(data,config)
		data = transform(data.T).T
		data = 1000*(data[0:512]/115057684827.0)
		data = np.ascontiguousarray(np.uint8(data))
		image = Image.frombuffer("L",data.shape,data=data.data)
		try:
			image.save(out_fd,format='jpeg')
		except Exception:
			break
	in_fd.close()
	out_fd.close()
