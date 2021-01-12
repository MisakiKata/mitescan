# -*- coding: utf-8 -*-
# @Time    : 2021/1/6 15:52
# @Author  : misakikata
# @File    : url.py
# Software : PyCharm
from django.urls import path
from apps.anyx import views

app_name = 'anyx'


urlpatter2 = [
    path('index/', views.index, name='anyxindex'),
    path('anyxpro/', views.anyxpro, name='anyxpro'),
    path('delanyx/', views.delanyx, name='delanyx'),
    path('delanyxpro/', views.delanyxpro, name='delanyxpro'),
]