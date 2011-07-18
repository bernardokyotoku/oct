import niScope
import numpy as np
X,Y,Z = 2420,500,500
scope = niScope.Scope("Dev4")
scope.ConfigureHorizontalTiming( numPts = X,
		sampleRate = 40000000.0,
		enforceRealtime = True,
		numRecords = Y,
		refPosition = 0.0)
scope.ConfigureVertical( coupling = 1,
		channelList = 1,
		enabled = True,
		probeAttenuation = 1.0,
		offset = 0.0,
		voltageRange = 10.0,)
scope.ConfigureTrigger("Edge",
		slope = 1,
		delay = 5.5e-06,
		triggerCoupling = 1,
		level = 0.0,
		triggerSource = 'VAL_EXTERNAL',
		holdoff = 0.0,)
scope.ExportSignal( signal = 4 ,
		outputTerminal = 'VAL_RTSI_0',
		signalIdentifier = "End of record",)
scope.FetchNumberRecords = Y
data = np.zeros([Z,X,Y],order='F',dtype.float64)
for tomogram in data:
	scope.InitiateAcquisition()
	scope.Fetch(data)
	print "done"

