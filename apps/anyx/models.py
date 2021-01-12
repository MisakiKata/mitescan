from django.db import models
from django.utils import timezone
# Create your models here.


class AnyX(models.Model):
    #any

    url = models.URLField('漏洞链接')
    headers = models.TextField('请求头')
    host = models.CharField('主机名', max_length=50, default='127.0.0.1')
    port = models.IntegerField('端口',default=80)
    type = models.CharField('漏洞类型', max_length=20, blank=True)
    msg = models.CharField('漏洞描述', max_length=2000, blank=True)
    param = models.CharField('漏洞参数', max_length=100, blank=True, null=True)
    value = models.CharField('漏洞payload', max_length=200, blank=True)
    method = models.CharField('请求方法', max_length=10)
    path = models.CharField('插件目录', max_length=50, blank=True)
    result = models.CharField('漏洞结果', max_length=50, blank=True)
    creatime = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '漏洞详情'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.url

