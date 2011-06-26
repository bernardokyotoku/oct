from niScope import Scope
import ordered_symbols
import logging as log
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj

def typing(config):
	def section(config):
		for el in config:
			config[el] = cast[el](config[el])
		return config

	scope_symbol = lambda x:getattr(ordered_symbols,x)
	log_type = lambda x:getattr(log,x)
	cast = {
		'ChanCharacteristic' : 	section,
		'channelList' : 	str,
		'coupling' : 		scope_symbol,
		'delay' : 		int,
		'enabled' : 		bool,
		'enforceRealtime' : 	bool,
		'holdoff' : 		int,
		'Horizontal' : 		section,
		'level' : 		int,
		'log':			log_type,
		'maxFrequency' : 	int,
		'numPts' : 		int,
		'numRecords' : 		int,
		'offset' : 		int,
		'probeAttenuation' : 	int,
		'refPosition' : 	float,
		'sampleRate' : 		int,
		'scope':		section,
		'slope' : 		scope_symbol,
		'triggerCoupling' : 	scope_symbol,
		'Trigger' : 		section,
		'triggerSource' : 	scope_symbol,
		'trigger_type' : 	str,
		'VerticalRef':		section,
		'VerticalSample' : 	section,
		'voltageRange' : 	int,
	}
	return section(config)

config = typing(ConfigObj('settings.cfg'))
log.basicConfig(filename='oct.log',level=config['log'])
scope_config = config['scope']
scope = Scope()
log.debug('Scope initialized ok')
scope.ConfigureHorizontalTiming(**scope_config['Horizontal'])
log.debug('Scope horizontal configured')
scope.ConfigureTrigger(**scope_config['Trigger'])
log.debug('Scope trigger configured')
scope.ConfigureVertical(**scope_config['VerticalRef'])
log.debug('Scope ref configured')
scope.ConfigureVertical(**scope_config['VerticalSample'])
log.debug('Scope sample configured')
#scope.InitiateAcquisition()
#data = np.zeros((2000,2),order='F',dtype=np.float64)
#scope.Fetch('0,1',data)
#plt.plot(data.T[0])
#plt.show()
