from django.contrib import admin
from apps.anyx.models import AnyX
# Register your models here.

@admin.register(AnyX)
class AnyXAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'result', 'msg', 'param', 'path','value','creatime')
    list_display_links = ('id', 'url')
    ordering = ('pk',)
    search_fields = ['id', 'param']


admin.site.site_header = '管理后台'
admin.site.site_title = '管理后台'
