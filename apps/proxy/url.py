from django.urls import path
from apps.proxy import views


app_name = 'proxy'


extra_urlpatter = [
    path('order/', views.proxything, name='thing'),
    path('user/', views.user, name='user'),
    path('proxysite/', views.proxysite, name='proxysite'),
    path('sitedit/', views.sitedit, name='sitedit'),
    path('delsite/', views.delsite, name='delsite'),
    path('delproxy/', views.delproxy, name='delproxy'),
    path('pro/', views.proxypro, name='pro'),

]