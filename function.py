try:
	import niScope
except Exception:
	print "niScope missing, continuing anyway"
try:
	from nidaqmx import AnalogOutputTask
except Exception:
	print "nidaqmx missing, continuing anyway"
import logging
import numpy as np
import matplotlib.pyplot as plt
import signal
import subprocess
import sys
from configobj import ConfigObj
from validate import Validator
from time import sleep
from multiprocessing import Process, Queue
from path import *
from scipy import interpolate
from PIL import Image

interrupted = False

def signal_handler(signal, frame):
	print "interrupt"
	global interrupted
	interrupted = True
signal.signal(signal.SIGINT, signal_handler)

def log_type(value):
	try:
		return getattr(logging,value)
	except AttributeError:
		pass
	return int(value)	

def park(daq):
	position([0,0],daq)

def prepare_daq(path,daq_config,mode,auto_start=True):
	X_mpV = daq_config['X_mpV']
	Y_mpV = daq_config['Y_mpV']
	T = np.array([[X_mpV,Y_mpV]])
	signal = path*T
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.configure_timing_sample_clock(**daq_config[mode])
	#array ordering is really annoying me, need to fix this
	shape = list(signal.shape)
	shape.reverse()
	signal = signal.reshape(shape)
	daq.write(signal.T,auto_start=auto_start)
	return daq

def move_daq(signal,daq_config):
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.write(signal)
	del daq

def prepare_scope(scope_config):
	scope = niScope.Scope(scope_config['dev'])
	scope.ConfigureHorizontalTiming(**scope_config['Horizontal'])
	scope.ExportSignal(**scope_config['ExportSignal'])
	scope.ConfigureTrigger(**scope_config['Trigger'])
	scope.ConfigureVertical(**scope_config['VerticalRef'])
	scope.ConfigureVertical(**scope_config['VerticalSample'])
	return scope

def resample(raw_data,config,rsp_data=None,axis=0):
	if rsp_data == None:
		n = 1024
		rsp_data = np.zeros((n,raw_data.shape[-1]))
	else:
		n = rsp_data.shape[axis]
	p = [config['resample_poly_coef']['p%d'%i] for i in range(8)]
	f = np.poly1d(p)
	old_x = f(np.arange(raw_data.shape[axis]))
	new_x = np.linspace(0,raw_data.shape[axis],n)
	if len(raw_data.shape) == 1:
		tck = interpolate.splrep(old_x,raw_data,s=0)
		rsp_data = interpolate.splev(new_x,tck)
	else:
		for line in range(raw_data.shape[-1]):
			tck = interpolate.splrep(old_x,raw_data[:,line])
			rsp_data[:,line] = interpolate.splev(new_x,tck)
	return rsp_data

def transform(rsp_data):
	return abs(np.fft.fft(rsp_data))


def horz_cal(config,data):
	scope_config = config['scope']
	scope = prepare_scope(config['scope'])
	scope.InitiateAcquisition()
	num = scope_config['Horizontal']['numPts']
	rec = scope_config['Horizontal']['numRecords']*2
	data = np.zeros((num,rec),order='F',dtype=np.float64)
	scope.Fetch('0,1',data)
	np.savetxt('ref.dat',data,fmt='%.18e')
	return data

def load(config,data):
	data = np.loadtxt('ref.dat').T
	return data[0]

def non_cor_fft(config,data):
	return abs(np.fft.fft(data))

def get_p(config,data):
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
	return data

def convert_path_to_voltage(path,path_to_voltage_constants):
	X_mpV = path_to_voltage_constants['X_mpV']
	Y_mpV = path_to_voltage_constants['Y_mpV']
	T = np.array([[X_mpV,Y_mpV]])
	return path*T

def configure_daq(mode,daq_config):
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.configure_timing_sample_clock(**daq_config[mode])
	return daq

def adjust_scope_config_to_scan(mode,config):
	numRecords = config[mode]['numRecords']
	numPts = config[mode]['numPts']
	config['scope']['Horizontal']['numRecords'] = numRecords
	config['scope']['Horizontal']['numPts'] = numPts

def configure_scope(mode,config):
	def fetch(self,memory):
		ch = config['VerticalSample']['channelList']
		self.Fetch(ch,memory)
	niScope.Scope.fetch_sample_signal = fetch
	scope = niScope.Scope(config['dev'])
	scope.ConfigureHorizontalTiming(**config['Horizontal'])
	scope.ExportSignal(**config['ExportSignal'])
	scope.ConfigureTrigger(**config['Trigger'])
	scope.ConfigureVertical(**config['VerticalRef'])
	scope.ConfigureVertical(**config['VerticalSample'])
	return scope

def allocate_memory(mode,config):
	Xp = config[mode]['numLongPts']
	X = config[mode]['numPts']
	Y = config[mode]['numRecords']
	Z = config[mode]['numTomograms']
	data = 	[np.zeros([X ,Y],order='F',dtype=np.int32) for i in range(Z)]
	data_p= [np.zeros([Xp,Y],order='F',dtype=np.int32) for i in range(Z)]
	class Memory:
		def __init__(self,data,data_p,mode):
			self.i = 0 
			self.data = data
			self.data_p = data_p
			self.mode = mode
			self.next = {
				'single':self.next_single,
				'continuous':self.next_continuous,
				'3D':self.next_3D,
					}[self.mode]

		def next_p(self):
			return self.data_p[i]

		def next_continuous(self):
			self.i += 1	
			if self.i >= len(self.data):
				self.i = 1
			return self.data[self.i - 1]

		def next_3D(self):
			self.i += 1	
			return self.data[self.i-1]

		def next_single(self):
			return self.data,self.data_p

		def all(self):
			return self.data
	return Memory(data,data_p,mode)

def scan_continuous(config,data):
	scan(config,data,'continuous')

def scan_3D(config,data):
	scan(config,data,'3D')

def scan(config,data,mode):
	adjust_scope_config_to_scan(mode,config)
	memory = allocate_memory(mode,config)
	import serial
	ser = serial.Serial('/dev/ttyUSB0',baudrate=115200);ser.write('oct=1\rscan=1\r');ser.close()
	scope = configure_scope(mode,config['scope'])
	path = Path(mode,config)

	global interrupted
	interrupted = False
	filename = 'fifo'
	fd = open(filename,'w',0)
	while path.has_next() and not interrupted:
		tomogram = memory.next()
		signal = convert_path_to_voltage(path.next(),config['path_to_voltage'])
		daq = configure_daq(mode,config['daq'])
		#need to test if array ordering is ok
		daq.write(signal)
		scope.InitiateAcquisition()
		scope.fetch_sample_signal(tomogram)
		fd.write(tomogram.data)
		del daq
		signal = convert_path_to_voltage(path.next_return(),config['path_to_voltage'])
		move_daq(signal,config['daq'])
	move_daq([0,0],config['daq'])
	ser = serial.Serial('/dev/ttyUSB0',baudrate=115200);ser.write('oct=0\rscan=0\r');ser.close()
	fd.close()

def scan_3Dold(config,data):
	config_scope = config["scope3D"]
	arg = config['scan_region'].dict()
	x0,y0,xf,yf = arg['x0'],arg['y0'],arg['xf'],arg['yf']
	memory = allocate_memory(config_scope,'3D')
	scope = prepare_scope(config_scope)
	numTomograms = config_scope['numTomograms']
	numRecords = config_scope['Horizontal']['numRecords']
	path = Path((x0,y0),(xf,yf),[numTomograms,numRecords])
	global interrupted
	interrupted = False
	while path.has_next() and not interrupted:
		tomogram = memory.next()
		daq = prepare_daq(path.next(),config['daq'],"scan3D")
		scope.InitiateAcquisition()
		scope.Fetch(config_scope['VerticalSample']['channelList'],tomogram)
		del daq
		move_daq(path.next_return(),config['daq'])
	return memory.all()

def scan_continuousold(config,data):
	config_scope = config['scope_continuous']
	arg = config['scan_region'].dict()
	x0,y0,xf,yf = arg['x0'],arg['y0'],arg['xf'],arg['yf']
	numRecords = config_scope['Horizontal']['numRecords']
	path = Path((x0,y0),(xf,yf),numRecords)
	scope = prepare_scope(config_scope)
	memory = allocate_memory(config_scope,'continuous')
	global interrupted
	interrupted = False
	plt.ion()
	plt.figure()
	plt.show()
	while path.has_next() and not interrupted:
		daq = prepare_daq(path.next(),config['daq'],'scanContinuous')
		scope.InitiateAcquisition()
		data = memory.next()
		scope.Fetch('0',data)
		del daq
		move_daq(path.next_return(),config['daq'])
		processed_data = memory.next_p()
		resample(data,config,processed_data)
		processed_data = transform(processed_data.T).T
		img = processed_data 
		plt.imshow(img[512:])
		plt.draw()
	return memory.all()

def resample_d(config,data):
	if type(data) == list:
		data = data[0]
	return resample(data,config['resample_poly_coef'])

def fft(config,data):
	data = abs(np.fft.fft(data))

def plot(config,data):
	if len(data.shape) == 3:
		data = data[0,0,:]
	if len(data.shape) == 2:
		if data.shape[1] == 2:
			plt.plot(data[0],data[1])
			plt.show()
			return
	plt.plot(data)
	plt.show()

def zimg_plot(config,data):
	if type(data)== list:
		data = data[0]
	if len(data.shape) == 2:
		data = data
	import matplotlib.pyplot as plt
	plt.imshow(data)
	plt.show()

def store(config,data):
	filename = "data.dat"
	np.savetxt(filename,data)
