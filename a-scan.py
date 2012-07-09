import processor
import signal_capture as sc
import signal as interrupt
import matplotlib.pyplot as plt
import numpy as np

config = processor.parse_config()

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
    figure = graph
    plt.clf()
    rsp_data = processor.resample(data, config)
    ascan = processor.transform(rsp_data.T).T
    plt.subplot(211)
    plt.plot(rsp_data)
    plt.ylim([s*1E9 for s in [-1,1]])
    plt.subplot(212)
    db = True
    if db:
        plt.plot(np.log10(ascan))
        plt.ylim([7,11])
    else:
        plt.plot(np.log(ascan))
        plt.ylim([0,1E09])
    figure.canvas.draw()

if __name__ == '__main__':
    buffer = sc.allocate_memory()
    print "Initializing Scope"
    scope = sc.initialize_scope()
    setup_interruption()
    print "Initianting acquisition"
    graph = init_plot(buffer)
    print "Press ctrl-C and enter to stop"
    while not interrupted:
        try:
            scope.InitiateAcquisition()
            scope.Fetch('0',buffer)
        except Exception:
            print "Is the laser on, enabled and tunning?"
            interrupted = True
#        print "0th value of the waveform:", buffer[0]
        plot(buffer, graph)
    raw_input()
