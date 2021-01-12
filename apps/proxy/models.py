from django.db import models
from django.utils import timezone

# Create your models here.

class ProxyAny(models.Model):
    # request thing

    url = models.CharField('请求地址', max_length=500)
    status_code = models.IntegerField('状态码')
    start_time = models.CharField('请求开始时间', max_length=30)
    end_time = models.CharField('请求结束时间', max_length=30)
    method = models.CharField('请求方法', max_length=10)
    host = models.CharField('请求主机', max_length=50)
    content_type = models.CharField('文件类型', max_length=30)
    path = models.CharField('请求路径', max_length=500)
    scheme = models.CharField('请求协议', max_length=10)
    port = models.IntegerField('请求端口', blank=True)
    request_header = models.TextField('请求头')
    respone_header = models.TextField('响应头')
    request_content = models.CharField('请求参数', max_length=500, blank=True, null=True)
    create_time = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '请求值'
        verbose_name_plural = '请求值'

    def __str__(self):
        return self.host




class ProxySite(models.Model):
    # proxy site thing
    url_filter = models.TextField('过滤的域名', blank=True)
    filter_ext = models.TextField('过滤的文件类型', blank=True)
    create_time = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '过滤设置'
        verbose_name_plural = verbose_name
