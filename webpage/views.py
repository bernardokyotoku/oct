from django.http import HttpResponse
from django.utils import simplejson
import traceback,sys

def scan(request):
	scan_settings = request.GET
	mode = scan_settings['mode']
	return HttpResponse("mode ="+mode)

def config(request):
	print "here"
	try:
		from processor import parse_config
	except Exception,e:
		print e
		traceback.print_exc(file=sys.stdout)
	configu = parse_config()
	return JSONResponse(configu.dict())

def JSONResponse(data):
	return HttpResponse(simplejson.dumps(data), content_type = 'application/javascript; charset=utf8')

