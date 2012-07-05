from nidaqmx import DigitalOutputTask
import numpy as np 

task = DigitalOutputTask()
task.create_channel('Dev3/port0/line0')
task2 = DigitalOutputTask()
task2.create_channel('Dev3/port0/line1')
#task.configure_timing_sample_clock()
#data = np.ones(1000)
