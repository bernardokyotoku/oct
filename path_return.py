
f = 16000.
T = 1000/f
T
10/T
vt=10/T
r = 10/T
sampleRate = n/dt
dt=0.1
n=100
sampleRate = n/dt
numTomograms=100
yf,y0=10,0
def return_path(x0,xf,y0,yf,t0,tf,r,N,numTomograms):
	f = poly1d(poly3(x0,xf,t0,tf,r,r))
	path = f(linspace(t0,tf,N))
	path.shape += (1,)
	path_x = path*ones(numTomograms)
	a = [[y[i],y[i+1]] for i in range(numTomograms-1)]+[[y[-1]]*2]
	path_y = vstack(map(lambda x:linspace(x[0],x[1],n),a))
	path_x = path_x.T
	p = dstack((path_x,path_y))
	return p
