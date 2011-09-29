from nidaqmx import AnalogOutputTask

task = AnalogOutputTask()
task.create_voltage_channel("Dev1/ao2",min_voltage=0,max_voltage=6)
