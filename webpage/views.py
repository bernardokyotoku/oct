from django.http import HttpResponse

def test(request):
	return HttpResponse("hello world")
