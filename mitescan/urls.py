"""mitescan URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.views.static import serve
from django.urls import path, re_path, include

from apps.anyx.url import urlpatter2
from apps.proxy.url import extra_urlpatter
from apps.proxy.views import index, dashb, loginx, logoutx, view_page_404, view_page_403, view_page_500, editpasswd
from apps.sqli.url import urlpatten



urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^static/(?P<path>.*)$',serve,{'document_root': settings.STATIC_ROOT}),
    path('proxy/', include(extra_urlpatter)),
    path('sqli/', include(urlpatten)),
    path('anyx/', include(urlpatter2)),
    path('index/', index, name='index'),
    path('', index, name='index'),
    path('dashb/', dashb, name='dashb'),
    path('editpasswd/', editpasswd, name='editpasswd'),
    path('login/', loginx, name='loginx'),
    path('logout/', logoutx, name='logoutx'),

]

handler404 = view_page_404
handler500 = view_page_500
handler403 = view_page_403