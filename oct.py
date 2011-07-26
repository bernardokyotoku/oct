import niScope
import ordered_symbols
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj
from validate import Validator
from nidaqmx import AnalogOutputTask
from time import sleep
from multiprocessing import Process, Queue
from function import *

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('--horz-cal',action='store_true')
	parser.add_argument('--plot',action='store_true')
	parser.add_argument('--img-plot',action='store_true')
	parser.add_argument('--store',action='store_true')
	parser.add_argument('--x',action='store_true')
	parser.add_argument('--get-p',action='store_true')
	parser.add_argument('--resample',action='store_true')
	parser.add_argument('--fft',action='store_true')
	parser.add_argument('--non-cor-fft',action='store_true')
	parser.add_argument('--line',action='store_true')
	parser.add_argument('--scan-3D',action='store_true')
	parser.add_argument('--scan-continuous',action='store_true')
	parser.add_argument('--scan',action='store_true')
	parser.add_argument('--load',action='store_true')
	return parser.parse_args()

validator = Validator({'log':log_type,'float':float})
arg = parse()
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(filename='oct.log',level=config['log'])
scope_config = config['scope']
if arg.line:
	print line([1,0],[2,3],10)

if arg.horz_cal:
	scope = prepare_scope(config['scope'])
	scope.InitiateAcquisition()
	num = scope_config['Horizontal']['numPts']
	rec = scope_config['Horizontal']['numRecords']*2
	print "Actual record length = ",scope.ActualRecordLength
	print "Actual sample rate = ",scope.ActualRecordLength
	data = np.zeros((num,rec),order='F',dtype=np.float64)
	scope.Fetch('0,1',data)
	np.savetxt('ref.dat',data,fmt='%.18e')
	x = None
			
if arg.load:
	data = np.loadtxt('ref.dat').T
	data = data[0]
	y = data

if arg.non_cor_fft:
	data = abs(np.fft.fft(data))

if arg.get_p:
	data =  y > 0
	t = np.logical_xor(data,np.roll(data,1))
	size = len(y)
	zero_x = np.arange(size)[t]
	zero_y = np.linspace(0,zero_x[-1],len(zero_x))
	data = zero_x
	p = np.polyfit(zero_x,zero_y,7)
	f = np.poly1d(p)
	data = np.vstack([zero_y,f(zero_x)]).T
	for i in p:
		config['resample_poly_coef']['p%d'%np.where(p==i)] = i
	config.write()	
	x = zero_x



if arg.scan:
	image_config = config['image']
	lineDensity = image_config['density']
	length = image_config['length']
	X = single_scan_path(-length/2,length/2,50,lineDensity)
	path = np.vstack([X,np.zeros(X.shape)]).T
	daq = prepare_daq(path,config['daq'],"positioning")
	scope = prepare_scope(scope_config)
	scope.NumRecords = path.shape[1]
	raw_data = scan(scope,daq)
	rsp_data = resample(raw_data)
	fft_data = transform(rsp_data)
	abs_data = abs(fft_data)

if arg.scan_3D:
	config3D = config["scope3D"]
	data = allocate_memory(config3D)
	scope = prepare_scope(config3D)
	numTomograms = config3D['numTomograms']
	conf = config['daq']['positioning']
	f = config['laser']['frequency']
	path = config['daq']['path'] 
	numRec = config3D['Horizontal']['numRecords']
	tf = float(numRec)/f
	import pdb;pdb.set_trace()
	r = (path['xf']-path['x0'])/tf
	N = conf['samples_per_channel']
	x0,xf,y0,yf=path['x0'],path['xf'],path['y0'],path['yf']
	return_path = make_return_path(x0,xf,y0,yf,tf,r,N,numTomograms)
	scan_path = make_scan_path(x0,xf,y0,yf,numRec,numTomograms)
	for i in range(numTomograms):
		tomogram = data[i]
		daq = prepare_daq(scan_path[i],config['daq'],"scan3D")
		scope.InitiateAcquisition()
		scope.Fetch(config3D['VerticalSample']['channelList'],tomogram)
		del daq
		daq = prepare_daq(return_path[i],config['daq'],"positioning",auto_start=True)
		daq.wait_until_done()
		del daq
	# numpy arrays and niscope arrays have weird order, code below fix it
	new_shape = [data.shape[i] for i in [0,2,1]]
	data = data.reshape(new_shape)

if arg.scan_continuous:
	path = loadpath()
	position(path[0],daq)
	daq.configure_timing_sample_clock(**daq_config['scanContinuous'])
	daq.write(path)
	park(daq)

if arg.resample:
	if len(data.shape) == 3:
		data = data[0,:,:]
	data = resample(data,config['resample_poly_coef'])
	x = None 

if arg.fft:
	data = abs(np.fft.fft(data))

if arg.plot:
	if len(data.shape) == 3:
		data = data[0,0,:]
		x = None
	if len(data.shape) == 2:
		data = data[0]
		x = None
	if x is None:
		x = np.arange(len(data))
	import matplotlib.pyplot as plt
	plt.plot(x,data)
	plt.show()

if arg.img_plot:
	if len(data.shape) == 3:
		data = data[0]
	if len(data.shape) == 2:
		data = data
	import matplotlib.pyplot as plt
	plt.imshow(data)
	plt.show()

if arg.store:
	filename = "data.dat"
	np.savetxt(filename,data)
