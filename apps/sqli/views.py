import requests
from django.shortcuts import render, redirect
from django.http.response import HttpResponseServerError, HttpResponse
from apps.sqli.models import SQLmaster, SQLsite
from django.views.decorators.csrf import csrf_exempt
import json
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.contrib.auth.decorators import login_required
from django import db
# Create your views here.

@login_required
def index(request):
    # index
    if 'host' not in request.GET and 'port' not in request.GET:
        sql = SQLmaster.objects.all()
        return render(request, 'order-sql.html', {'sql':sql})
    elif request.GET.get('host') == '' and request.GET.get('port') == '':
        sql = SQLmaster.objects.all()
        return render(request, 'order-sql.html', {'sql':sql})
    else:
        host = request.GET.get('host')
        port = request.GET.get('port')
        if isinstance(host, str) and host != '':
            if port != '' and isinstance(int(port), int):
                sql = SQLmaster.objects.filter(host=host).filter(port=port)
            else:
                sql = SQLmaster.objects.filter(host=host)
        elif isinstance(int(port), int) and port != '':
            sql = SQLmaster.objects.filter(port=port)
        else:
            sql = SQLmaster.objects.all()
        return render(request, 'order-sql.html', {'sql':sql})


@csrf_exempt
@login_required
def delsql(request):
    # del sql

    if request.method == 'POST':
        try:
            id = str(request.body, encoding='utf-8').split(',')
            for i in id:
                sqlurl = SQLmaster.objects.get(id=i).sqlmap_url
                taskid = SQLmaster.objects.get(id=i).taskid
                requests.get(sqlurl + '/task/' + taskid + '/delete')
            SQLmaster.objects.filter(id__in=id).delete()
            return HttpResponse(status=200)
        except Exception as e:
            print(e)
            return HttpResponseServerError('server error')
    else:
        return redirect('/index')

@login_required
def sqlsite(request):
    # sql site

    site = SQLsite.objects.all()
    return render(request, 'admin-sql.html', {'site':site})

@csrf_exempt
@login_required
def delsite(request):
    #del site

    if request.method == 'POST':
        try:
            id = str(request.body, encoding='utf-8')
            SQLsite.objects.get(id=id).delete()
            return HttpResponse(status=200)
        except:
            return HttpResponseServerError('server error')
    else:
        return redirect('/index')


@csrf_exempt
@login_required
def sitedite(request):
    #edit site

    if request.method == 'GET':
        if SQLsite.objects.all().count() != 0:
            url = SQLsite.objects.values('serv')[0]['serv']
            return render(request, 'admin-edit-sql.html', locals())
        else:
            return render(request, 'admin-edit-sql.html')
    elif request.method == 'POST':
        url = json.loads(request.body)['url'] if json.loads(request.body)['url'] else ''
        try:
            SQLsite.objects.create(serv=url)
            return HttpResponse(status=200)
        except:
            return HttpResponseServerError('server error')

@login_required
def cronevent(request):
    if request.GET.get('comshow'):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.start()
        register_events(scheduler)
        if request.GET.get('comshow') == 'yes':
            scheduler.add_job(scanstatus, 'interval', minutes=1, id='status')               #定时任务时间
            return HttpResponse(status=200)
        elif request.GET.get('comshow') == 'no':
            scheduler.remove_job('status')
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)
    else:
        return redirect('/index')

def scanstatus():
    try:
        SQLmaster.objects.exists()
    except:
        db.close_old_connections()

    statu = SQLmaster.objects.filter(status=0)

    for s in statu:
        try:
            url = s.sqlmap_url
            r = requests.get(url+'/scan/'+s.taskid+'/status')

            if r.json()['status'] == 'running':
                continue

            r = requests.get(url+'/scan/'+s.taskid+'/data')
            if len(r.json()['data']):
                for ty in r.json().get('data'):
                    if ty.get('type') == 1:

                        key = ty['value'][0].get('data')
                        dbms = ty['value'][0].get('dbms')
                        parameter = ty['value'][0].get('parameter')
                        title = ty['value'][0].get('data')[list(key.keys())[0]]['title']
                        payload = ty['value'][0].get('data')[list(key.keys())[0]]['payload']

                        SQLmaster.objects.filter(taskid=s.taskid).update(dbms=dbms, parament=parameter, title=title, payload=payload, sqlstatus=1, status=1)
            else:
                s.status = 1
                s.save()

        except Exception as e:
            db.close_old_connections()
            print(e)

@login_required
def pro(request):
    #sql pro

    if request.GET.get('id'):
        id = request.GET.get('id')
        sql = SQLmaster.objects.get(id=id)

        return render(request, 'admin-add-sql.html', {'sql':sql})
    else:
        redirect('/index')
