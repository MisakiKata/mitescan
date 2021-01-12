from django.contrib import admin
from apps.sqli.models import SQLmaster, SQLsite
# Register your models here.


@admin.register(SQLmaster)
class SQLmasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'taskid', 'status', 'sqlstatus', 'parament', 'payload')
    list_filter = ('status', 'sqlstatus')
    search_fields = ('id', 'url', 'taskid')
    list_display_links = ('id', 'url')


@admin.register(SQLsite)
class SQLsiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'serv')
    search_fields = ('id', 'serv')
    list_display_links = ('id', 'serv')