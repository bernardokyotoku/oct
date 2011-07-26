import numpy as np
from function import *
def return_path(x0,xf,y0,yf,t0,tf,r,N,numTomograms):
	f = np.poly1d(poly3(x0,xf,t0,tf,r,r))
	path = f(np.linspace(t0,tf,N))
	path.shape += (1,)
	path_x = path*np.ones(numTomograms)
	y = np.linspace(y0,yf,numTomograms)
	a = [[y[i],y[i+1]] for i in range(numTomograms-1)]+[[y[-1]]*2]
	path_y = np.vstack(map(lambda x:np.linspace(x[0],x[1],N),a))
	path_x = path_x.T
	p = np.dstack((path_x,path_y))
	return p

print return_path(10,0,0,10,0,0.1,160,100,100)[0]
