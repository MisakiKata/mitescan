from django.db import models
from django.contrib.auth.admin import User
from django.utils import timezone
# Create your models here.


class SQLmaster(models.Model):

    AVAORT = (
        (0, '运行中'),
        (1, '已完成')
    )

    AVAORT2 = (
        (0, '不存在注入'),
        (1, '存在注入！')
    )

    url = models.CharField('请求地址', max_length=500)
    header = models.TextField('请求头')
    content = models.CharField('请求参数', max_length=500, blank=True, null=True)
    host = models.CharField('主机地址', max_length=100, blank=True)
    port = models.IntegerField('端口', blank=True)
    taskid = models.CharField('任务ID', max_length=32)
    status = models.IntegerField('扫描状态', choices=AVAORT, default=0)
    sqlstatus = models.IntegerField('扫描结果', choices=AVAORT2, default=0)
    dbms = models.CharField('数据库类型', max_length=20, blank=True)
    payload = models.CharField('注入payload', max_length=200, blank=True)
    title = models.CharField('注入类型', max_length=100, blank=True)
    parament = models.CharField('漏洞参数', max_length=100, blank=True)
    sqlmap_url = models.URLField('使用的SQLMAP地址', default='http://127.0.0.1:8775')
    creat_time = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '注入详情'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.taskid



class SQLsite(models.Model):

    serv = models.URLField('sqlmap服务器地址', help_text='格式为：http://IP:PORT', unique=True)

    class Meta:
        verbose_name = 'SQLMAP地址'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.serv

