from django.contrib import admin
from apps.proxy.models import ProxyAny
from apps.proxy.models import ProxySite

# Register your models here.

@admin.register(ProxyAny)
class ProxyAnyAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'status_code', 'content_type', 'request_content', 'create_time')
    list_display_links = ('id', 'url')
    ordering = ('pk',)
    search_fields = ['host', 'status_code']


@admin.register(ProxySite)
class ProxySiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'url_filter', 'filter_ext', 'create_time')
    list_display_links = ('id',)
    ordering = ('pk',)


admin.site.site_header = '管理后台'
admin.site.site_title = '管理后台'


