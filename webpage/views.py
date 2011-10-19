from django.http import HttpResponse
#import function

def scan(request):
	scan_settings = request.GET
	mode = scan_settings['mode']
	return HttpResponse("mode ="+mode)
