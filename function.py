import niScope
import ordered_symbols
import logging
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj
from validate import Validator
from nidaqmx import AnalogOutputTask
from time import sleep
from multiprocessing import Process, Queue

def log_type(value):
	try:
		return getattr(logging,value)
	except AttributeError:
		pass
	return int(value)	

def scan(scope,daq):
	scope.InitiateAcquisition()
	daq.start()
	while scope.AcquisitionStatus() != niScope.NISCOPE_VAL_ACQ_COMPLETE:
		sleep(0.1)
	scope.Fetch("",data)
	return data

def position(point,daq):
	pass

def park(daq):
	position([0,0],daq)

def prepare_daq(path,daq_config,mode,auto_start):
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.configure_timing_sample_clock(**daq_config['positioning'])
	daq.write(path,auto_start=auto_start)
	return daq

def prepare_scope(scope_config):
	scope = niScope.Scope(scope_config['dev'])
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
	resampled = np.zeros((raw_data.shape[0],1024))
	if len(raw_data.shape) == 1:
		tck = interpolate.splrep(old_x,raw_data,s=0)
		resampled = interpolate.splev(new_x,tck)
	else:
		for line in range(raw_data.shape[0]):
			tck = interpolate.splrep(old_x,raw_data[line])
			resampled[line] = interpolate.splev(new_x,tck)
	return resampled

def transform(rsp_data):
	return abs(np.fft.fft(data))

def allocate_memory(config):
	hor = config['Horizontal']
	X = hor['numPts']
	Y = hor['numRecords']
	Z = config['numTomograms']
	data = np.zeros([Z,X,Y],order='C',dtype=np.float64)
	return data

def line(begin,end,lineDensity):
	lineDensity = float(lineDensity)
	v = np.array(end) - np.array(begin)
	length = np.sqrt(sum(v**2))
	t = np.linspace(0,1,length*lineDensity)	
	t.shape += (1,)
	line = begin + v*t
	return line.T

def poly3(x1,x2,t1,t2,r1,r2):
	"""
	Returns the polynomial coeficients for a curve with the position and the
	derivative defined at two points of the curve.
	"""
	from numpy.linalg import solve
	A = np.array([
	[	3*t1**2,	2*t1, 	1,	0	],
	[	3*t2**2,	2*t2,	1,	0	],
	[	t1**3  , 	t1**2,	t1,	1	],
	[	t2**3  , 	t2**2,	t2,	1	],
	])
	B = np.array([r1, r2, x1, x2])
	return solve(A,B)

def make_scan_path(x0,xf,y0,yf,numRecords,numTomograms):
	x = np.linspace(x0,xf,numRecords)
	x.shape = (1,) + x.shape
	X = x*np.ones((numTomograms,1))
	y = np.linspace(y0,yf,numTomograms)
	y.shape = y.shape + (1,)
	Y = y*np.ones(numRecords)
	scan_path = np.dstack([X,Y])
	return scan_path

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
    	
def positioning(daq_task,config):
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
