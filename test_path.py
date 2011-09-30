from path import Path
import numpy as np
from mock import Mock
import path

def test_has_Path_object_creation():
	config = {"single":{
				"x0":0,
				"y0":0,
				"xf":1,
				"yf":1,
				"numRecords":1,
				"acc":0.1}}
	path = Path(config, "single")
	return path

def test_if_next_path_is_2_by_x_array():
	path = test_has_Path_object_creation()
	dimension = len(path.next()[0])
	assert dimension is 2, "dimension is %s"%dimension

def test_smooth_return():
	p0 = np.array([10,4])
	pf = -p0 
	a = 0.1 
	p = path.smooth_return(p0,pf,a) 
	dimension = p[0].shape
	assert dimension == (2,), "dimension is %s"%str(dimension)
	last_p = p[-1]
	assert last_p.all() == pf.all(), "last p is %s"%str(last_p)
	max_acc = np.max(np.diff(np.diff(p,axis=0),axis=0))
	error = np.abs(max_acc - a)/a
	assert error < 1, "max_acc is %s"%np.diff(np.diff(p,axis=0),axis=0)
