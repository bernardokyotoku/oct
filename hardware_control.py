def set_voltage_to_channel(channel,voltage):
	from nidaqmx import AnalogOutputTask
	tolerance = 1
	laserTask = AnalogOutputTask()
	laserTask.create_voltage_channel(channel,min_val=voltage - tolerance,
			max_val=voltage + tolerance)
	laserTask.write(voltage)
	laserTask.clear()

def turn_laser(state):
	voltage = 5 if state == "on" else 0
	set_voltage_to_channel("Dev3/ao2",voltage)

def turn_pointer(state):
	voltage = 4 if state == "on" else 0
	set_voltage_to_channel("Dev3/ao3",voltage)
