import json
import requests
from apps.sqli.models import SQLsite
from apps.sqli.models import SQLmaster
from random import choice


class sqli:
    def __init__(self, url, data, host, port, headers):
        self.url = url
        self.data = data
        self.headers = headers
        self.host = host
        self.port = port
        self.taskid = ''
        self.sqlstatus = 0
        # self.sqlurl = choice(hostname)    #动态修改

    def sqlurl(self):
        hostname = list(SQLsite.objects.values_list('serv', flat=True))
        sqlurl =choice(hostname)
        return sqlurl

    def header(self):
        headerstr = ''
        key = self.headers.keys()
        for k in key:
            headerstr += k + ':' + self.headers[k] +'\n'
        return headerstr

    def newtask(self):
        r = requests.get(self.sqlurl()+'/task/new')
        self.taskid = r.json()['taskid']
        return r.json()


    def startscan(self):
        if self.newtask()['success']:
            if not self.data:
                r = requests.post(self.sqlurl() + '/scan/' + self.taskid + '/start', json.dumps({'url': self.url, 'headers':self.header(),'batch':True,'flushSession':True,
                                                                                               'level':3}),headers={'Content-Type':'application/json'})
                return r.json()
            else:
                r = requests.post(self.sqlurl() + '/scan/' + self.taskid + '/start', json.dumps({'url': self.url, 'data': self.data, 'headers':self.header(),'batch':True,'flushSession':True,
                                                                                              'level':3}),headers={'Content-Type':'application/json'})
                return r.json()


    def run(self):
        if self.startscan()['success']:
            SQLmaster.objects.create(url=self.url, header=self.headers, content=self.data, taskid=self.taskid, host=self.host, port=self.port, sqlmap_url=self.sqlurl(), status=0)
            return True
        else:
            return False





