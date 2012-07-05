from nidaqmx import AnalogOutputTask
import numpy as np 

task = AnalogOutputTask()
task.create_voltage_channel('Dev3/ao0', max_val = 10)
task.configure_timing_sample_clock()
task.write(np.ones(1000)*3)
data = [i*0.001 for i in range(1000)]
for n in range(1000):
	task = AnalogOutputTask()
	task.create_voltage_channel("Dev3/ao3")
	task.configure_timing_sample_clock()
	task.write(data,auto_start=False)
#	del task
