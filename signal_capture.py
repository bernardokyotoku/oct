import niScope
from niScope import COUPLING
import numpy as np
import signal as interrupt
import matplotlib.pyplot as plt

####### CONFIGURATION ##########
dev = 'Dev2'
VerticalRef = {
    'coupling': COUPLING.AC,
    'channelList': 'ext',
    'enabled': True,
    'probeAttenuation': 1.0,
    'offset': 0.0,
    'voltageRange': 10.0,
    }
Horizontal = {
    'numPts': 2420,
    'sampleRate': 40000000.0,
    'enforceRealtime': True,
    'numRecords': 1,
    'refPosition': 0.0,
    }
Trigger = {
    'slope': 1,
    'delay': 5.5e-06,
    'triggerCoupling': 1,
    'level': 0.0,
    'trigger_type': 'Edge',
    'triggerSource': 'VAL_EXTERNAL',
    'holdoff': 0.0,
    }
ChanCharacteristic = {
    'channelList': '0',
    'maxFrequency': 1000000.0,
    'impedance': 50,
    }
VerticalSample = {
    'coupling': COUPLING.AC,
    'channelList': '0',
    'enabled': True,
    'probeAttenuation': 1.0,
    'offset': 0.0,
    'voltageRange': 10.0,
    }

####### FUNCTIONS ##########

def allocate_memory():
    X = Horizontal['numPts']
    return np.zeros([X ,1],order='F',dtype=np.int32)

def initialize_scope():
    scope = niScope.Scope(dev)
    scope.ConfigureHorizontalTiming(**Horizontal)
    scope.ConfigureTrigger(**Trigger)
#    scope.ConfigureVertical(**VerticalRef)
    scope.ConfigureVertical(**VerticalSample)
    return scope

def interrupt_handler(interrupt, frame):
    print "interrupt"
    global interrupted
    interrupted = True
    
def setup_interruption():
    interrupt.signal(interrupt.SIGINT, interrupt_handler)
    global interrupted 
    interrupted = False

def init_plot(buffer):
    plt.ion()
    figure = plt.figure()
    return figure

def plot(data, graph):
    plt.clf()
    figure = graph
    plt.plot(data)
    figure.canvas.draw()

############ MAIN ###############
if __name__ == '__main__':
    buffer = allocate_memory()
    print "Initializing Scope"
    scope = initialize_scope()
    setup_interruption()
    print "Initianting acquisition"
    graph = init_plot(buffer)
    while not interrupted:
        try:
            scope.InitiateAcquisition()
            scope.Fetch('0',buffer)
        except Exception:
            print "Is the laser on, enabled and tunning?"
            interrupted = True
        print "0th value of the waveform:", buffer[0]
        plot(buffer, graph)
    raw_input()

