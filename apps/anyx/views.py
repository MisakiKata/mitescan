from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden
# Create your views here.
from django.contrib.auth.decorators import login_required
from apps.anyx.models import AnyX
from django.views.decorators.csrf import csrf_exempt

@login_required
def index(request):
    #anyx

    if 'host' not in request.GET and 'port' not in request.GET:
        anyx = AnyX.objects.all()
        return render(request, 'order-anyx.html', {'anyx':anyx})
    elif request.GET.get('host') == '' and request.GET.get('port') == '':
        anyx = AnyX.objects.all()
        return render(request, 'order-anyx.html', {'anyx':anyx})
    else:
        host = request.GET.get('host')
        port = request.GET.get('port')
        if isinstance(host, str) and host != '':
            if port != '' and isinstance(int(port), int) :
                anyx = AnyX.objects.filter(host=host).filter(port=port)
            else:
                anyx = AnyX.objects.filter(host=host)
        elif isinstance(int(port), int) and port != '':
            anyx = AnyX.objects.filter(port=port)
        else:
            anyx = AnyX.objects.all()
        return render(request, 'order-anyx.html', {'anyx':anyx})

@login_required
def anyxpro(request):
    # anyx pro

    if request.GET.get('id'):
        id =  request.GET.get('id')
        anyx = AnyX.objects.get(id=id)
        return render(request, 'admin-add-anyx.html', {'anyx':anyx})
    else:
        return HttpResponseForbidden('server Forbidden')

@csrf_exempt
@login_required
def delanyx(request):
    #del

    if request.body:
        id = request.body
        try:
            AnyX.objects.get(id=id).delete()
            return HttpResponse(status=200)
        except:
            return HttpResponseServerError('server error')
    else:
        return HttpResponseForbidden('server Forbidden')


@csrf_exempt
@login_required
def delanyxpro(request):
    #del proxy

    if request.method == 'POST':
        id = request.body
        try:
            ids = str(id, encoding='utf-8').split(',')
            AnyX.objects.filter(id__in=ids).delete()
        except:
            return HttpResponseServerError('server error')
        return HttpResponse(status=200)
    else:
        return redirect('/index')

