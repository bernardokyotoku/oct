from niScope import Scope
import ordered_symbols
import logging as log
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj
from validate import Validator
from nidaqmx import AnalogOutputTask
from time import sleep
from multiprocessing import Process, Queue

def log_type(value):
	try:
		return getattr(log,value)
	except AttributeError:
		pass
	return int(value)	

validator = Validator({'log':log_type,'float':float})

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('--horz-cal',action='store_true')
	parser.add_argument('--plot',action='store_true')
	parser.add_argument('--x',action='store_true')
	parser.add_argument('--get-p',action='store_true')
	parser.add_argument('--resample',action='store_true')
	parser.add_argument('--fft',action='store_true')
	parser.add_argument('--non-cor-fft',action='store_true')
	parser.add_argument('--line',action='store_true')
	parser.add_argument('--scan-3D',action='store_true')
	parser.add_argument('--scan-continuous',action='store_true')
	parser.add_argument('--scan',action='store_true')
	return parser.parse_args()

def scan(scope,daq):
	scope.InitiateAcquisition()
	daq.start()
	while scope.complete():
		sleep(0.1)
	scope.Fetch(data)
	return data

def position(point,daq):
	pass

def park(daq):
	position([0,0],daq)

def prepare_daq(path,daq_config):
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.configure_timing_sample_clock(**daq_config['positioning'])
	daq.write(path,auto_start=False)
	return daq

def prepare_scope(scope_config):
	scope = Scope(scope_config['dev'])
	log.debug('Scope initialized ok')
	scope.ConfigureHorizontalTiming(**scope_config['Horizontal'])
	log.debug('Scope horizontal configured')
	scope.ExportSignal(**scope_config['ExportSignal'])
	scope.ConfigureTrigger(**scope_config['Trigger'])
	log.debug('Scope trigger configured')
	scope.ConfigureVertical(**scope_config['VerticalRef'])
	log.debug('Scope ref configured')
	scope.ConfigureVertical(**scope_config['VerticalSample'])
	log.debug('Scope sample configured')
	return scope

def resample(raw_data,config):
	from scipy import interpolate
	import matplotlib.pyplot as plt
	p = [config['p%d'%i] for i in range(8)]
	f = np.poly1d(p)
	old_x = f(np.arange(raw_data.shape[-1]))
	new_x = np.linspace(0,raw_data.shape[-1],1024)
	resampled = np.zeros(raw_data.shape)
	if len(raw_data.shape) == 1:
		tck = interpolate.splrep(old_x,raw_data,s=0)
		resampled = interpolate.splev(new_x,tck)
	else:
		for line in raw_data:
			tck = interpolate.splrep(old_x,line)
			resampled[raw_data.index(line)] = interpolate.splev(new_x,tck)
	return resampled

def transform(rsp_data):
	return abs(np.fft.fft(data))

def allocate_memory(config):
	hor = config['Horizontal']
	X = hor['numPts']
	Y = hor['numRecords']
	Z = config['numTomograms']
	return np.zeros([Z,X,Y],order='F',dtype=np.float64)

def line(begin,end,lineDensity):
	lineDensity = float(lineDensity)
	v = np.array(end) - np.array(begin)
	length = np.sqrt(sum(v**2))
	t = np.linspace(0,1,length*lineDensity)	
	t.shape += (1,)
	line = begin + v*t
	return line.T

def poly3(x1,x2,t1,t2,r1,r2):
	from numpy.linalg import solve
	A = np.array([
	[	3*t1**2,	2*t1, 	1,	0	],
	[	3*t2**2,	2*t2,	1,	0	],
	[	t1**3  , 	t1**2,	t1,	1	],
	[	t2**3  , 	t2**2,	t2,	1	],
	])
	B = np.array([r1, r2, x1, x2])
	return solve(A,B)

def third_order_line(x1,x2,t1,t2,r1,r2):
    	f = np.poly1d(poly3(x1,x2,t1,t2,r1,r2))
	return f(np.arange(t1,t2))

def single_scan_path(X0,Xf,t,lineDensity):
	pitch = 1/float(lineDensity)
	num = (Xf-X0)*lineDensity
	start = third_order_line(0,X0,0,t,0,pitch)
	scan = np.linspace(X0,Xf,num)
	park = third_order_line(Xf,0,0,t,pitch,0)
	return np.hstack([start,scan[0:-1],park])
    	
def positioning(daq_task,config)
	config['daq']['positioning']
	task.configure_timing_sample_clock(source='OnboardClock', rate=1, active_edge='rising', sample_mode='finite', samples_per_channel=1000)
	
def make_setpositionpath():
	pass

def make_resetpositionpath():
	pass

def make_acquisitionwindowpath():
	pass

def make_parkpath():
	pass

	

arg = parse()
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
	raise Exception('config.ini does not validate with configspec.ini.')
log.basicConfig(filename='oct.log',level=config['log'])
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

if arg.resample:
	data = resample(data,config['resample_poly_coef'])
	x = None 
if arg.fft:
	data = abs(np.fft.fft(data))

if arg.scan:
	path = loadpath()
	daq = prepare_daq(path,config['daq'])
	scope = prepare_scope(scope)
	raw_data = scan(scope,daq)
	rsp_data = resample(raw_data)
	fft_data = transform(rsp_data)
	abs_data = abs(fft_data)

if arg.scan_3D:
	path = loadpath()
	position(path[0],daq)
	data = alloc_mem(config['scope3D'])
	daq.write(path)
	prepare_scope(scope,config['scope3D'])
	queue = Queue()
	p = Process(target=fetcher, args=(scope,queue))
	scope.InitiateAcquisition()
	p.start()
	
	park(daq)

def fetcher(scope,queue):
	scope.Fetch(data)
	queue.put(data)

if arg.scan_continuous:
	path = loadpath()
	position(path[0],daq)
	daq.configure_timing_sample_clock(**daq_config['scanContinuous'])
	daq.write(path)
	park(daq)

if arg.plot:
	if x is None:
		x = np.arange(len(data))
	import matplotlib.pyplot as plt
	plt.plot(x,data)
	plt.show()

