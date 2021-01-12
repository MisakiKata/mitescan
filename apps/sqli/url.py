from django.urls import path
from apps.sqli import views

app_name = 'sqli'

urlpatten = [
    path('index/', views.index, name='sqlindex'),
    path('delsql/', views.delsql, name='delsql'),
    path('sqlsite/', views.sqlsite, name='sqlsite'),
    path('delsite/', views.delsite, name='delsqlsite'),
    path('sitedite/', views.sitedite, name='sqlsitedite'),
    path('cronevent/', views.cronevent, name='cronevent'),
    path('pro/', views.pro, name='sqlpro'),
]