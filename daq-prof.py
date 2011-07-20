from nidaqmx import AnalogOutputTask

data = [i*0.001 for i in range(1000)]
for n in range(1000):
	task = AnalogOutputTask()
	task.create_voltage_channel("Dev3/ao3")
	task.configure_timing_sample_clock()
	task.write(data,auto_start=False)
	del task
