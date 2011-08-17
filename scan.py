




def convert_path_to_voltage(path,path_to_voltage_constants):
	X_mpV = path_to_voltage_constants['X_mpV']
	Y_mpV = path_to_voltage_constants['Y_mpV']
	T = np.array([[X_mpV,Y_mpV]])
	return path*T

def configure_daq(mode,daq_config):
	daq = AnalogOutputTask()
	daq.create_voltage_channel(**daq_config['X'])
	daq.create_voltage_channel(**daq_config['Y'])
	daq.configure_timing_sample_clock(**daq_config[mode])
	return daq

def adjust_scope_config_to_scan(mode,config):
	numRecords = config[mode]['numRecords']
	numPts = config[mode]['numPts']
	config['scope']['Horizontal']['numRecords'] = numRecords
	config['scope']['Horizontal']['numPts'] = numPts

def configure_scope(mode,config):
	def fetch(self,memory):
		ch = config['VerticalSample']['ChannelList']
		self.Fetch(ch,memory)
	niScope.Scope.fetch_sample_signal = fetch
	scope = niScope.Scope(config['dev'])
	scope.ConfigureHorizontalTiming(**config['Horizontal'])
	scope.ExportSignal(**config['ExportSignal'])
	scope.ConfigureTrigger(**config['Trigger'])
	scope.ConfigureVertical(**config['VerticalRef'])
	scope.ConfigureVertical(**config['VerticalSample'])
	return scope

def allocate_memory(mode,config):
	Xp = config['num_long_points']
	X = config[mode]['numPts']
	Y = config[mode]['numRecords']
	Z = config[mode]['numTomograms']
	data = 	[np.zeros([X ,Y],order='F',dtype=np.int32) for i in range(Z)]
	data_p= [np.zeros([Xp,Y],order='F',dtype=np.int32) for i in range(Z)]
	class Memory:
		def __init__(self,data,data_p,mode):
			self.i = 0 
			self.data = data
			self.data_p = data_p
			self.mode = mode
			self.next = {
				'single':self.next_single,
				'continuous':self.next_continuous,
				'3D':self.next_3D,
					}[self.mode]

		def next_p(self):
			return self.data_p[i]

		def next_continuous(self):
			self.i += 1	
			if self.i >= len(self.data):
				self.i = 1
			return self.data[self.i - 1]

		def next_3D(self):
			self.i += 1	
			return self.data[self.i-1]

		def next_single(self):
			return self.data,self.data_p

		def all(self):
			return self.data
	return Memory(data,data_p,mode)

def scan(config,data,mode):
	memory = allocate_memory(mode,config)
	scope = configure_scope(mode,config)
	path = Path(mode,config)

	global interrupted
	interrupted = False
	fd = open(filename,'w',0)
	while path.has_next() and not interrupted:
		tomogram = memory.next()
		signal = convert_path_to_voltage(path.next(),config['path_to_voltage'])
		daq = configure_daq(config['daq'],mode)
		#need to test if array ordering is ok
		daq.write(signal)
		scope.InitiateAcquisition()
		scope.fetch_sample_signal(tomogram)
		sys.stdout.write(tomogram.data)
		del daq
		move_daq(path.next_return(),config['daq'])
	fd.close()
