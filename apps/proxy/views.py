import datetime
from django.shortcuts import render, HttpResponse, redirect
from apps.proxy.models import ProxyAny, ProxySite
from django.contrib.auth.admin import User
from django.http.response import HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
import json
from apps.sqli.models import SQLmaster
from apps.anyx.models import AnyX
from django.db import connection
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from myproxy import myproxys
# Create your views here.

myproxys.main()

@login_required
def index(request):
    # index

    return render(request, 'index.html')

@login_required
def proxything(request):
    # proxy thing
    date_to = datetime.datetime.now()
    date_from = date_to - datetime.timedelta(days=3)                # 显示3天的流量数据

    if 'host' not in request.GET and 'port' not in request.GET:
        proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to))
        return render(request, 'order-list.html', {'proxy':proxy})
    elif request.GET.get('host') == '' and request.GET.get('port') == '':
        proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to))
        return render(request, 'order-list.html', {'proxy':proxy})
    else:
        host = request.GET.get('host')
        port = request.GET.get('port')
        if isinstance(host, str) and host != '':
            if port != '' and isinstance(int(port), int):
                proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to)).filter(host=host).filter(port=port)
            else:
                proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to)).filter(host=host)
        elif isinstance(int(port), int) and port != '':
            proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to)).filter(port=port)
        else:
            proxy = ProxyAny.objects.filter(create_time__range=(date_from, date_to))
        return render(request, 'order-list.html', {'proxy':proxy})

@csrf_exempt
@login_required
def delproxy(request):
    #del proxy

    if request.method == 'POST':
        id = request.body
        try:
            ids = str(id, encoding='utf-8').split(',')
            ProxyAny.objects.filter(id__in=ids).delete()
        except:
            return HttpResponseServerError('server error')
        return HttpResponse(status=200)
    else:
        return redirect('/index')

@login_required
def dashb(request):
    # dashb
    #main1
    cur_date = datetime.datetime.now()
    date_from = datetime.datetime(cur_date.year, cur_date.month, cur_date.day, 0, 0, 0)
    nowdata = ProxyAny.objects.filter(create_time__gte=date_from, create_time__lte=cur_date).count()
    yester_day = cur_date - datetime.timedelta(days=1)
    onedata = ProxyAny.objects.filter(create_time__gte=yester_day, create_time__lte=cur_date).count()
    two_day = cur_date - datetime.timedelta(days=2)
    twodata = ProxyAny.objects.filter(create_time__gte=two_day, create_time__lte=yester_day).count()
    three_day = cur_date - datetime.timedelta(days=3)
    threedata = ProxyAny.objects.filter(create_time__gte=three_day, create_time__lte=two_day).count()
    four_day = cur_date - datetime.timedelta(days=4)
    fourdata = ProxyAny.objects.filter(create_time__gte=four_day, create_time__lte=three_day).count()
    five_day = cur_date - datetime.timedelta(days=5)
    fivedata = ProxyAny.objects.filter(create_time__gte=five_day, create_time__lte=four_day).count()
    six_day = cur_date - datetime.timedelta(days=6)
    sixdata = ProxyAny.objects.filter(create_time__gte=six_day, create_time__lte=five_day).count()

    #main2,4
    sqlall = SQLmaster.objects.filter(sqlstatus=1).count()
    xss = AnyX.objects.filter(type='xss').count()
    cmd_injection = AnyX.objects.filter(type='cmd_injection').count()
    code_injection = AnyX.objects.filter(type='code_injection').count()
    dirscan = AnyX.objects.filter(type='dirscan').count()
    path_traversal = AnyX.objects.filter(type='path_traversal').count()
    xxe = AnyX.objects.filter(type='xxe').count()
    brute_force = AnyX.objects.filter(type='brute_force').count()
    jsonp = AnyX.objects.filter(type='jsonp').count()
    redirect = AnyX.objects.filter(type='redirect').count()
    ssrf = AnyX.objects.filter(type='ssrf').count()
    crlf = AnyX.objects.filter(type='crlf').count()
    sensitive = AnyX.objects.filter(type='sensitive').count()
    smuggling = AnyX.objects.filter(type='smuggling').count()
    baseline = AnyX.objects.filter(type='baseline').count()

    #main3
    size = "select \"miteproxy\", concat(truncate(sum(data_length)/1024/1024/1024,2),' GB') as data_size,concat(truncate(sum(index_length)/1024/1024/1024,2),'GB') as index_size from information_schema.tables"
    cursor = connection.cursor()
    cursor.execute(size)
    raw = cursor.fetchone()[1]
    raw = int(float(raw.split(' ')[0])/100)
    return render(request, 'welcome1.html', locals())

@login_required
def user(request):
    # user
    username = request.GET.get('username')
    if username:
        user = User.objects.filter(username=username)
    else:
        user = User.objects.all()
    return render(request, 'admin-list.html', {'user':user})

@login_required
def proxysite(request):
    # site

    site = ProxySite.objects.all()
    return render(request, 'admin-cate.html',{'site':site})

@csrf_exempt
@login_required
def sitedit(request):
    # edit
    if request.method == 'GET':
        url_filter = ProxySite.objects.values('url_filter')[0]['url_filter']
        filter_ext = ProxySite.objects.values('filter_ext')[0]['filter_ext']
        return render(request, 'admin-edit.html', locals())
    elif request.method == 'POST':
        url = json.loads(request.body)['url'] if json.loads(request.body)['url'] else ''
        ext = json.loads(request.body)['ext'] if json.loads(request.body)['ext'] else ''
        try:
            ProxySite.objects.create(url_filter=url, filter_ext=ext)
            return HttpResponse(status=200)
        except:
            return HttpResponseServerError('server error')


@csrf_exempt
@login_required
def delsite(request):
    # del
    if request.method == "POST":
        id = request.body
        try:
            ProxySite.objects.get(pk=json.loads(id)).delete()
            return HttpResponse(status=200)
        except:
            return HttpResponseServerError('server error')
    else:
        redirect('/index')

@login_required
def proxypro(request):
    # pro

    if request.GET.get('id'):
        id = request.GET.get('id')
        proxy = ProxyAny.objects.get(id=id)
        return render(request, 'admin-add.html', {'proxy':proxy})
    else:
        return redirect('/index')

@csrf_exempt
def loginx(request):
    # login

    if request.POST.get('username') and request.POST.get('password'):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('/index')
        else:
            return render(request, 'login.html')
    else:
        if request.user.is_authenticated:
            return redirect('/index')
        return render(request, 'login.html')

@login_required
def logoutx(request):
    #logout

    logout(request)
    return redirect('/login')

@csrf_exempt
@login_required
def editpasswd(request):
    #edit passwd

    err_msg = ''
    if request.method == 'GET' and request.GET.get('oldpass'):
        old_password = request.GET.get('oldpass')
        new_password = request.GET.get('newpass')
        repeat_password = request.GET.get('repass')

        if request.user.check_password(old_password):
            if not new_password:
                err_msg = '新密码不能为空'
            elif new_password != repeat_password:
                err_msg = '两次密码不一致'
            else:
                request.user.set_password(new_password)
                request.user.save()
                err_msg = '密码修改成功'
                return render(request, 'member-password.html', {'err_msg': err_msg})
        else:
            err_msg = '原密码输入错误'
        return render(request, 'member-password.html', {'err_msg': err_msg})
    else:
        return render(request, 'member-password.html')


def view_page_404(request,*args, **kwargs):
    # 404

    return render(request, '404.html')

def view_page_403(request,*args, **kwargs):
    # 403

    return render(request, '403.html')

def view_page_500(request,*args, **kwargs):
    # 500

    return render(request, '500.html')


