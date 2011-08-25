import numpy as np
import logging
import sys
import cPickle
import Image
from configobj import ConfigObj
from validate import Validator
from function import transform,log_type,resample

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
validator = Validator({'log':log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])

for i in flags:
	if getattr(arg,i.replace('-','_')):
		fun = getattr(function,i)
		data = fun(config,data)	

in_fd = open(arg.input_filename)
out_fd = open(arg.output_filename,'w',0)
import matplotlib.pyplot as plt
i=0
#raw_input()
for i in range(100):
	print i
	#info = cPickle.load(in_fd)
	try:
		data = cPickle.load(in_fd)
	except Exception:
		break
	#data = np.ndarray(**info)
	data = resample(data,config)

	print 'x',data.shape
	data = transform(data.T).T
	data = 1000*(data[0:512]/115057684827.0)
	#plt.imshow(data)
	#plt.show()
	data3 = np.ascontiguousarray(np.uint8(data))
	print 'y',data3.shape
	#plt.imshow(data3)
	#plt.show()
	image = Image.frombuffer("L",data.shape,data=data3.data)
	#data = renormalize(data)
	try:
		image.save(out_fd,format='jpeg')
	except Exception:
		break
in_fd.close()
out_fd.close()
