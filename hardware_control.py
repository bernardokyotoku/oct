import sys
def set_voltage_to_channel(channel,voltage):
    from nidaqmx import AnalogOutputTask
    tolerance = 1
    laserTask = AnalogOutputTask("pointer")
    laserTask.create_voltage_channel(channel,min_val=voltage - tolerance,
            max_val=voltage + tolerance)
    laserTask.write(voltage)
    laserTask.clear()

def turn_laser(state):
    voltage = 3.4 if state == "on" else 0
    set_voltage_to_channel("Dev2/ao3",voltage)
