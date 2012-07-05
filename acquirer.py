import logging
import numpy as np
import matplotlib.pyplot as plt
import signal as interrupt
import subprocess
import sys
import cPickle
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

def log_type(value):
    try:
        return getattr(logging,value)
    except AttributeError:
        pass
    return int(value)    

def park(daq):
    position([0,0],daq)

def move_daq(signal,daq_config):
    try:
        from nidaqmx import AnalogOutputTask
    except Exception:
        print "nidaqmx missing, continuing anyway"
    daq = AnalogOutputTask()
    daq.create_voltage_channel(**daq_config['X'])
    daq.create_voltage_channel(**daq_config['Y'])
    daq.write(signal)
    del daq

def resample(raw_data, config, rsp_data=None,axis=0):
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

def transform(config, rsp_data):
    return abs(np.fft.fft(rsp_data.T).T)


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
    try:
        from nidaqmx import AnalogOutputTask
    except Exception:
        print "nidaqmx missing, continuing anyway"
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
    try:
        import niScope
    except Exception:
        print "niScope missing, continuing anyway"
    def fetch(self,memory):
        ch = config['VerticalSample']['channelList']
        print "fetching channel:", ch
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
    data =     [np.zeros([X ,Y],order='F',dtype=np.int32) for i in range(Z)]
    data_p=    [np.zeros([Xp,Y],order='F',dtype=np.int32) for i in range(Z)]
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
            return self.data[0]#,self.data_p

        def all(self):
            return self.data
    return Memory(data,data_p,mode)

def scan_continuous(config,data):
    scan(config,data,'continuous')

def scan_3D(config,data):
    scan(config,data,'3D')

def scan_single(config, data):
    return scan(config, data, 'single')

def scan(config,data,mode):
    adjust_scope_config_to_scan(mode,config)
    memory = allocate_memory(mode,config)
#    import serial
#    ser = serial.Serial('/dev/ttyUSB0',baudrate=115200);ser.write('oct=1\rscan=1\r');ser.close()
    scope = configure_scope(mode,config['scope'])
    path = Path(config,mode)

    global interrupted
    interrupted = False
    print config['filename']
    with open(config['filename'],'w',0) as fd:
        interrupt.signal(interrupt.SIGINT, signal_handler)
        while path.has_next() and not interrupted:
            tomogram = memory.next()
            signal = convert_path_to_voltage(path.next(),config['path_to_voltage'])
            daq = configure_daq(mode,config['daq'])
            #need to test if array ordering is ok
            daq.write(signal)
            scope.InitiateAcquisition()
            scope.fetch_sample_signal(tomogram)
            try:
                cPickle.dump(tomogram, fd, cPickle.HIGHEST_PROTOCOL)
            except Exception:
                del daq
                signal = convert_path_to_voltage(path.next_return(),config['path_to_voltage'])
                break
            del daq
            signal = convert_path_to_voltage(path.next_return(),config['path_to_voltage'])
            move_daq(signal,config['daq'])
        move_daq([0,0],config['daq'])
#        ser = serial.Serial('/dev/ttyUSB0',baudrate=115200);ser.write('oct=0\rscan=0\r');ser.close()
        return tomogram


def resample_d(config,data):
    if type(data) == list:
        data = data[0]
    return resample(data, config)

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

def img_plot(config,data):
    print "ploting"
    if type(data)== list:
        data = data[0]
    if len(data.shape) == 2:
        data = data
    import matplotlib.pyplot as plt
    length = data.shape[0]/2-1
    plt.imshow(data[20:length])
    plt.show()

def store(config,data):
    filename = "data.dat"
    np.savetxt(filename,data)
