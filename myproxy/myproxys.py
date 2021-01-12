from mitmproxy.proxy.config import ProxyConfig
from mitmproxy.proxy.server import ProxyServer
from mitmproxy.tools.dump import DumpMaster
from mitmproxy import http, options
import threading
import asyncio
import sys
from apps.proxy.models import ProxyAny, ProxySite
import time
from django import db
from myproxy.sqlmapapi import sqli
from w13scan import w13scan

url_filter = list(ProxySite.objects.values_list("url_filter", flat=True))
filter_ext = list(ProxySite.objects.values_list("filter_ext", flat=True))

url_filter = ','.join(url_filter).strip(',').split(',')
static_ext = ','.join(filter_ext).strip(',').split(',')


class ResponseParser(object):

    def __init__(self, f):
        super(ResponseParser, self).__init__()
        self.flow = f
        self.content_type = self.get_content_type()
        self.extension = self.get_extension()
        self.ispass = self.capture_pass()

    def parser_data(self):

        result = {}
        result['content_type'] = self.content_type
        result['url'] = self.get_url()
        result['path'] = self.get_path()
        result['extension'] = self.get_extension()
        result['host'] = self.get_host()
        result['port'] = self.get_port()
        result['scheme'] = self.get_scheme()
        result['method'] = self.get_method()
        result['status_code'] = self.get_status_code()
        result['date_start'] = self.by_time(self.flow.response.timestamp_start)
        result['date_end'] = self.by_time(self.flow.response.timestamp_end)
        result['content_length'] = self.get_content_length()
        result['static_resource'] = self.ispass
        result['header'] = self.get_header()
        result['request_header'] = self.get_request_header()

        # request resource is media file & static file, so pass
        if self.ispass:
            result['content'] = None
            result['request_content'] = None
            return result

        result['request_content'] = self.get_request_content()
        return result

    def by_time(self, data):
        tt = time.localtime(data)
        return time.strftime("%Y-%m-%d %H:%M:%S", tt)

    def get_content_type(self):

        if not self.flow.response.headers.get('Content-Type'):
            return ''
        return self.flow.response.headers.get('Content-Type').split(';')[:1][0]

    def get_content_length(self):
        if self.flow.response.headers.get('Content-Length'):
            return int(self.flow.response.headers.get('Content-Length'))
        else:
            return 0

    def capture_pass(self):

        if self.extension in static_ext:
            return True

        # can't catch the content_type
        if not self.content_type:
            return False

    def get_header(self):
        return self.parser_header(self.flow.response.headers)

    def get_request_header(self):
        return self.parser_header(self.flow.request.headers)

    def get_request_content(self):
        return str(self.flow.request.content, encoding='utf-8')

    def get_url(self):
        return self.flow.request.url

    def get_path(self):
        return '/{}'.format('/'.join(self.flow.request.path_components))

    def get_extension(self):
        if not self.flow.request.path_components:
            return ''
        else:
            end_path = self.flow.request.path_components[-1:][0]
            split_ext = end_path.split('.')
            if not split_ext or len(split_ext) == 1:
                return ''
            else:
                return split_ext[-1:][0][:32]

    def get_scheme(self):
        return self.flow.request.scheme

    def get_method(self):
        return self.flow.request.method

    def get_port(self):
        return self.flow.request.port

    def get_host(self):
        return self.flow.request.host

    def get_status_code(self):
        return self.flow.response.status_code

    @staticmethod
    def parser_header(header):
        headers = {}
        for key, value in header.items():
            headers[key] = value
        return headers

class Addon(object):
    def response(self, flow: http.HTTPFlow):
        host = flow.request.host
        if host in url_filter:
            return

        url = flow.request.url
        lastPath = url.split('?')[0].split('/')[-1]
        if lastPath.split('.')[-1] in static_ext:
            return

        try:
            parser = ResponseParser(flow)
            if parser.parser_data()['static_resource']:
                return
            try:
                ProxyAny.objects.exists()            #判断连接超时重建
            except:
                db.close_old_connections()

            ProxyAny.objects.create(url=parser.parser_data()['url'], status_code=parser.parser_data()['status_code'], start_time=parser.parser_data()['date_start'],
                                    end_time=parser.parser_data()['date_end'], method=parser.parser_data()['method'], host=parser.parser_data()['host'],
                                    content_type=parser.parser_data()['content_type'], path=parser.parser_data()['path'], scheme=parser.parser_data()['scheme'],
                                    port=parser.parser_data()['port'], request_header=parser.parser_data()['request_header'], respone_header=parser.parser_data()['header'],
                                    request_content=parser.parser_data()['request_content'] if parser.parser_data()['request_content'] else '')

            sql = sqli(url=parser.parser_data()['url'], data=parser.parser_data()['request_content'],headers=parser.parser_data()['request_header'],
                       host=parser.parser_data()['host'], port=parser.parser_data()['port'])

            if sql.run():
                print('注入执行成功')
            else:
                print('注入执行失败')

            w13scan.main(url=parser.parser_data()['url'], status_code=parser.parser_data()['status_code'],request_headers=parser.parser_data()['request_header'],
                         respone_headers=parser.parser_data()['header'],respone_body=bytes(flow.response.text, encoding='utf-8'),method=parser.parser_data()['method'],
                         request_body=parser.parser_data()['request_content'])


        except Exception as e:
            db.close_old_connections()
            print(e)



def loop_in_thread(loop, m):
    asyncio.set_event_loop(loop)
    m.run_loop(loop.run_forever)


def main():
    option = options.Options(listen_host='0.0.0.0', listen_port=18088, http2=True, mode="regular")            #代理地址
    m = DumpMaster(option, with_termlog=False, with_dumper=False)
    config = ProxyConfig(option)
    m.server = ProxyServer(config)
    m.addons.add(Addon())

    loop = asyncio.get_event_loop()
    t = threading.Thread(target=loop_in_thread, args=(loop,m) )
    try:
        t.start()
    except:
        m.shutdown()
        sys.exit(0)

