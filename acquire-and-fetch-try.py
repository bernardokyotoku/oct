import niScope
import numpy as np
from time import sleep
import matplotlib.pyplot as plt
import timeit
X,Y,Z = 2420,1000,2
scope = niScope.Scope("Dev4")
scope.ConfigureHorizontalTiming( numPts = X,
		sampleRate = 40000000.0,
		enforceRealtime = True,
		numRecords = Y,
		refPosition = 0.0)
scope.ConfigureVertical( coupling = 1,
		channelList = "0",
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
data = np.zeros([Z,X,Y],order='C',dtype=np.int32)
i=0
#s = """\
#try:
#	scope.InitiateAcquisition()
#	scope.Fetch("0",data[0])
#	print "3"
#except Exception:
#	pass
#		"""
#t = timeit.Timer(stmt=s)
#print "pass %.2f usec/pass"%(100*t.timeit(number=100)/100) 
for tomogram in data:
	scope.InitiateAcquisition()
	scope.Fetch("0",tomogram)
	i +=1
	print i 
data = data.reshape((Z,Y,X))
#plt.plot(data[10,499,:])
#plt.show()
