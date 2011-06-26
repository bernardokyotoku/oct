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
		'coupling' : 		int,#scope_symbol
		'delay' : 		float,
		'enabled' : 		bool,
		'enforceRealtime' : 	bool,
		'holdoff' : 		float,
		'Horizontal' : 		section,
		'level' : 		float,
		'log':			int,#log_type,
		'maxFrequency' : 	int,
		'numPts' : 		int,
		'numRecords' : 		int,
		'offset' : 		float,
		'probeAttenuation' : 	float,
		'refPosition' : 	float,
		'sampleRate' : 		float,
		'scope':		section,
		'slope' : 		int,#int,#scope_symbol
		'triggerCoupling' : 	int,#scope_symbol
		'Trigger' : 		section,
		'triggerSource' : 	str,#int,#scope_symbol
		'trigger_type' : 	str,
		'VerticalRef':		section,
		'VerticalSample' : 	section,
		'voltageRange' : 	int,
		'resample_poly_coef':	section,
		'p0' : 			float,
		'p1' : 			float,
		'p2' : 			float,
		'p3' : 			float,
		'p4' : 			float,
		'p5' : 			float,
		'p6' : 			float,
		'p7' : 			float,
	}
	return section(config)

def parse():
	import argparse
	parser = argparse.ArgumentParser()
	parser.description = "OCT client."
	parser.add_argument('--horz-cal',action='store_true')
	parser.add_argument('--plot',action='store_true')
	parser.add_argument('--x',action='store_true')
	parser.add_argument('--get-p',action='store_true')
	parser.add_argument('--non-cor-fft',action='store_true')
	return parser.parse_args()

arg = parse()
raw_config = ConfigObj('settings.cfg')
config = typing(raw_config)
log.basicConfig(filename='oct.log',level=config['log'])
scope_config = config['scope']
if arg.horz_cal:
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
	scope.InitiateAcquisition()
	num = scope_config['Horizontal']['numPts']
	rec = scope_config['Horizontal']['numRecords']*2
	print "Actual record length = ",scope.ActualRecordLength
	data = np.zeros((num,rec),order='F',dtype=np.float64)
	scope.Fetch('0,1',data)
	np.savetxt('ref.dat',data,fmt='%.18e')
			
data = np.loadtxt('ref.dat').T
data = data[0]
y = data
if arg.non_cor_fft:
	data = abs(np.fft.fft(data))
if arg.get_p:
	data = data > 0
	t = np.logical_xor(data,np.roll(data,1))
	zero_x = np.arange(len(t))[t]
	zero_y = np.arange(len(zero_x))
	data = zero_x
	p = np.polyfit(zero_y,zero_x,7)
	raw_config['resample_poly_coef'] = {}
	for i in p:
		raw_config['resample_poly_coef']['p%d'%np.where(p==i)] = i
	raw_config.write()
	f = np.poly1d(p)
	data = np.vstack([zero_x,f(zero_y)]).T
	from scipy import interpolate
	new_x = f(np.linspace(0,len(zero_x)-1,len(y)))
	x2000 = np.arange(len(y))
	tck = interpolate.splrep(x2000,y,s=0)
	new_y = interpolate.splev(new_x,tck,der=0)
	x = f(np.linspace(1,len(zero_x),len(y)))
	x = None 
	data = new_y
	x = new_x
	data = abs(np.fft.fft(data))
if arg.plot:
	if x is None:
		x = np.arange(len(data))
	import matplotlib.pyplot as plt
	plt.plot(x,data)
	plt.show()
