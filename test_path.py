from path import Path
from mock import Mock

def test_has_Path_object_creation():
	config = {"single":{
				"x0":0,
				"y0":0,
				"xf":1,
				"yf":1,
				"numRecords":1}}
	path = Path(config, "single")
