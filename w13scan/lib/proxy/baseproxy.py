# coding:utf-8
import _socket
import http
import os
import platform
import select
import sys
import time
import traceback
import zlib
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from ssl import wrap_socket, SSLError
from urllib.parse import urlparse, ParseResult, urlunparse

import chardet
from OpenSSL.crypto import load_certificate, FILETYPE_PEM, TYPE_RSA, PKey, X509, X509Extension, dump_privatekey, \
    dump_certificate, load_privatekey, X509Req

from w13scan.lib.core.settings import VERSION
from w13scan.lib.core.common import dataToStdout
from w13scan.lib.core.data import logger, path, conf, KB
from w13scan.lib.core.enums import HTTPMETHOD
from w13scan.lib.core.settings import notAcceptedExt
from w13scan.lib.parse.parse_request import FakeReq
from w13scan.lib.parse.parse_responnse import FakeResp
from socket import socket
import socks as socks5

__author__ = 'qiye'
__date__ = '2018/6/15 11:45'
__copyright__ = 'Copyright 2018, BaseProxy Project'
__credits__ = ['qiye safe']

__license__ = 'GPL'
__version__ = '0.1'

__email__ = 'qiye_email@qq.com'
__status__ = 'Development'

__all__ = [
    'CAAuth',
    'ProxyHandle',
    'InterceptPlug',
    'MitmProxy',
    'AsyncMitmProxy',
    'Request',
    'Response',
    'HttpTransfer'
]


class HttpTransfer(object):
    version_dict = {9: 'HTTP/0.9', 10: 'HTTP/1.0', 11: 'HTTP/1.1'}

    def __init__(self):
        self.hostname = None
        self.port = None

        # 这是请求
        self.command = None
        self.path = None
        self.request_version = None

        # 这是响应
        self.response_version = None
        self.status = None
        self.reason = None

        self._headers = None

        self._body = b''

    def parse_headers(self, headers_str):
        '''
        暂时用不到
        :param headers:
        :return:
        '''
        header_list = headers_str.rstrip("\r\n").split("\r\n")
        headers = {}
        for header in header_list:
            [key, value] = header.split(": ")
            headers[key.lower()] = value
        return headers

    def to_data(self):
        raise NotImplementedError("function to_data need override")

    def set_headers(self, headers):
        headers_tmp = {}
        for k, v in headers.items():
            if k == "Accept-Encoding" and "br" in v:
                v = v.replace("br", "")
            headers_tmp[k] = v
        self._headers = headers_tmp

    def build_headers(self):
        '''
        返回headers字符串
        :return:
        '''
        header_str = ""
        for k, v in self._headers.items():
            header_str += k + ': ' + v + '\r\n'

        return header_str

    def get_header(self, key):
        if isinstance(key, str):
            return self._headers.get(key, None)
        raise Exception("parameter should be str")

    def get_headers(self):
        '''
        获取头部信息
        :return:
        '''
        return self._headers

    def set_header(self, key, value):
        '''
        设置头部
        :param key:
        :param value:
        :return:
        '''
        if isinstance(key, str) and isinstance(value, str):
            self._headers[key] = value
            return
        raise Exception("parameter should be str")

    def get_body_data(self):
        '''
        返回是字节格式的body内容
        :return:
        '''
        return self._body

    def set_body_data(self, body):
        if isinstance(body, bytes):
            self._body = body
            self.set_header("Content-length", str(len(body)))
            return
        raise Exception("parameter should be bytes")


class Request(HttpTransfer):

    def __init__(self, req):
        HttpTransfer.__init__(self)

        self.hostname = req.hostname
        self.port = req.port
        # 这是请求
        self.command = req.command
        self.path = req.path
        self.https = False
        self.request_version = req.request_version

        self.post_hint = None  # post数据类型
        self.post_data = None

        self.urlparse = None
        self.netloc = None
        self.params = None
        self.cookies = None

        self.set_headers(req.headers)

        if self.get_header('Content-Length'):
            self.set_body_data(req.rfile.read(int(self.get_header('Content-Length'))))

    def to_data(self):
        # Build request
        req_data = '%s %s %s\r\n' % (self.command, self.path, self.request_version)
        # Add headers to the request
        req_data += '%s\r\n' % self.build_headers()
        req_data = req_data.encode("utf-8", errors='ignore')
        req_data += self.get_body_data()
        return req_data

    def set_https(self, result=False):
        self.https = result


class Response(HttpTransfer):

    def __init__(self, request, proxy_socket):

        HttpTransfer.__init__(self)

        self.request = request

        h = HTTPResponse(proxy_socket)
        h.begin()
        # HTTPResponse会将所有chunk拼接到一起，因此会直接得到所有内容，所以不能有Transfer-Encoding
        del h.msg['Transfer-Encoding']
        del h.msg['Content-Length']

        self.response_version = self.version_dict[h.version]
        self.status = h.status
        self.reason = h.reason
        self.set_headers(h.msg)
        self.decoding = None
        self.language = self.system = self.webserver = None

        try:
            data = h.read()
            encoding = self.get_header("Content-Encoding")
            encoding = encoding or self.get_header("content-encoding")
            body_data = self._decode_content_body(data, encoding)
        except http.client.IncompleteRead:
            body_data = b''
        except zlib.error:
            body_data = b''
        except _socket.timeout:
            body_data = b''
        except MemoryError:
            body_data = b''
            logger.error('MemoryError for response')
        self.set_body_data(body_data)
        self._text()  # 尝试将文本进行解码

        h.close()
        proxy_socket.close()

    def _text(self):

        body_data = self.get_body_data()
        if self.get_header('Content-Type') and ('text' or 'javascript') in self.get_header('Content-Type'):
            self.decoding = chardet.detect(body_data)['encoding']  # 探测当前的编码
            if self.decoding:
                try:
                    self._body_str = body_data.decode(self.decoding)  # 请求体
                except Exception as e:
                    self._body_str = body_data
                    self.decoding = None
            else:
                self._body_str = body_data
        else:
            self._body_str = body_data
            self.decoding = None

    def get_body_str(self, decoding=None):
        if decoding:
            try:
                return self.get_body_data().decode(decoding)
            except Exception as e:
                return ''
        if isinstance(self._body_str, bytes):
            ret = self.get_body_data().decode(errors='ignore')
            return ret
        return self._body_str

    def set_body_str(self, body_str, encoding=None):
        if isinstance(body_str, str):
            if encoding:
                self.set_body_data(body_str.encode(encoding))
            else:
                self.set_body_data(body_str.encode(self.decoding if self.decoding else 'utf-8'))
            self._body_str = body_str
            return
        raise Exception("parameter should be str")

    def _encode_content_body(self, text, encoding):

        if encoding == 'identity':
            data = text
        elif encoding in ('gzip', 'x-gzip'):

            gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
            data = gzip_compress.compress(text) + gzip_compress.flush()

        elif encoding == 'deflate':
            data = zlib.compress(text)
        else:
            data = text

        return data

    def _decode_content_body(self, data, encoding):
        if encoding is None:
            encoding = 'identity'
        if encoding == 'identity':  # 没有压缩
            text = data
        elif encoding in ('gzip', 'x-gzip'):  # gzip压缩
            try:
                text = zlib.decompress(data, 16 + zlib.MAX_WBITS)
            except zlib.error:
                text = zlib.decompress(data)
        elif encoding == 'deflate':  # zip压缩
            try:
                text = zlib.decompress(data, -zlib.MAX_WBITS)
            except zlib.error:
                text = zlib.decompress(data)
        else:
            text = data

        self.set_header('Content-Encoding', 'identity')  # 没有压缩
        return text

    def to_data(self):

        res_data = '%s %s %s\r\n' % (self.response_version, self.status, self.reason)
        res_data += '%s\r\n' % self.build_headers()
        res_data = res_data.encode(self.decoding if self.decoding else 'utf-8', errors='ignore')
        res_data += self.get_body_data()
        return res_data


class CAAuth(object):
    '''
    用于CA证书的生成以及代理证书的自签名

    '''

    def __init__(self, ca_file="ca.pem", cert_file='ca.crt'):
        self.ca_file_path = os.path.join(path["certs"], ca_file)
        self.cert_file_path = os.path.join(path['certs'], cert_file)
        self._gen_ca()  # 生成CA证书，需要添加到浏览器的合法证书机构中

    def _gen_ca(self, again=False):
        # Generate key
        # 如果证书存在而且不是强制生成，直接返回证书信息
        if os.path.exists(self.ca_file_path) and os.path.exists(self.cert_file_path) and not again:
            self._read_ca(self.ca_file_path)  # 读取证书信息
            return
        self.key = PKey()
        self.key.generate_key(TYPE_RSA, 2048)
        # Generate certificate
        self.cert = X509()
        self.cert.set_version(2)
        self.cert.set_serial_number(1)
        self.cert.get_subject().C = 'CN'
        self.cert.get_subject().ST = 'Beijing'
        self.cert.get_subject().O = 'w-digital-scanner'
        self.cert.get_subject().CN = 'W13Scan scanner'
        self.cert.get_subject()
        self.cert.gmtime_adj_notBefore(0)
        self.cert.gmtime_adj_notAfter(315360000)
        self.cert.set_issuer(self.cert.get_subject())
        self.cert.set_pubkey(self.key)
        self.cert.add_extensions([
            X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:0"),
            X509Extension(b"keyUsage", True, b"keyCertSign, cRLSign"),
            X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=self.cert),
        ])
        self.cert.sign(self.key, 'sha256')
        with open(self.ca_file_path, 'wb+') as f:
            f.write(dump_privatekey(FILETYPE_PEM, self.key))
            f.write(dump_certificate(FILETYPE_PEM, self.cert))

        with open(self.cert_file_path, 'wb+') as f:
            f.write(dump_certificate(FILETYPE_PEM, self.cert))

    def _read_ca(self, file):
        self.cert = load_certificate(FILETYPE_PEM, open(file, 'rb').read())
        self.key = load_privatekey(FILETYPE_PEM, open(file, 'rb').read())

    def __getitem__(self, cn):
        # 将为每个域名生成的服务器证书，放到临时目录中
        cache_dir = path['certs']
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # cn = get_fld(cn, fix_protocol=True, fail_silently=True)
        cnp = os.path.join(cache_dir, "baseproxy_{}.pem".format(cn))

        if not os.path.exists(cnp):
            self._sign_ca(cn, cnp)
        return cnp

    def _sign_ca(self, cn, cnp):
        # 使用合法的CA证书为代理程序生成服务器证书
        # create certificate
        try:

            key = PKey()
            key.generate_key(TYPE_RSA, 2048)

            # Generate CSR
            req = X509Req()
            req.get_subject().CN = cn
            req.set_pubkey(key)
            req.sign(key, 'sha256')

            # Sign CSR
            cert = X509()
            cert.set_version(2)
            cert.set_subject(req.get_subject())
            cert.set_serial_number(self.serial)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(31536000)
            cert.set_issuer(self.cert.get_subject())
            ss = ("DNS:%s" % cn).encode(encoding="utf-8")

            cert.add_extensions(
                [X509Extension(b"subjectAltName", False, ss)])

            cert.set_pubkey(req.get_pubkey())
            cert.sign(self.key, 'sha256')

            with open(cnp, 'wb+') as f:
                f.write(dump_privatekey(FILETYPE_PEM, key))
                f.write(dump_certificate(FILETYPE_PEM, cert))
        except Exception as e:
            raise Exception("generate CA fail:{}".format(str(e)))

    @property
    def serial(self):
        return int("%d" % (time.time() * 1000))


class ProxyHandle(BaseHTTPRequestHandler):

    def __init__(self, request, client_addr, server):
        self.is_connected = False
        self._target = None
        self._proxy_sock = None
        BaseHTTPRequestHandler.__init__(self, request, client_addr, server)

    def do_CONNECT(self):
        '''
        处理https连接请求
        :return:
        '''

        self.is_connected = True  # 用来标识是否之前经历过CONNECT
        if self._is_replay():
            self.connect_relay()
        else:
            self.connect_intercept()

    def _is_replay(self):
        '''
        决定是否放行
        :return:
        '''
        ret = False
        target = self._target or self.path

        if "?" in target:
            target = target[:target.index("?")]
        for ext in notAcceptedExt:
            if target.endswith(ext):
                ret = True
                break

        return ret

    def proxy_connect(self):
        if not conf["proxy_config_bool"]:
            self._proxy_sock = socket()
        else:
            self._proxy_sock = socks5.socksocket()
            proxy = conf["proxy"]
            if "socks5" in proxy.keys():
                hostname, port = proxy["socks5"].split(":", 1)
                self._proxy_sock.set_proxy(socks5.SOCKS5, hostname, int(port))
            elif "socks4" in proxy.keys():
                hostname, port = proxy["socks4"].split(":", 1)
                self._proxy_sock.set_proxy(socks5.SOCKS4, hostname, int(port))
            elif "http" in proxy.keys():
                hostname, port = proxy["http"].split(":", 1)
                self._proxy_sock.set_proxy(socks5.HTTP, hostname, int(port))
            elif "https" in proxy.keys():
                hostname, port = proxy["https"].split(":", 1)
                self._proxy_sock.set_proxy(socks5.HTTP, hostname, int(port))
        self._proxy_sock.settimeout(10)
        self._proxy_sock.connect((self.hostname, int(self.port)))

    def do_GET(self):
        '''
        处理GET请求
        :return:
        '''
        if self.path == 'http://baseproxy.ca/' or self.path == 'http://w13scan.ca/':
            self._send_ca()
            return
        request = None
        try:
            if not self.is_connected:
                # 如果不是https，需要连接http服务器
                try:
                    self._proxy_to_dst()
                except Exception as e:
                    try:
                        self.send_error(500, '{} connect fail because of "{}"'.format(self.hostname, str(e)))
                    except BrokenPipeError:
                        pass
                    finally:
                        return
            else:
                self._target = self.ssl_host + self.path
            # 这里就是代理发送请求，并接收响应信息
            request = Request(self)
            if request:
                if self.is_connected:
                    request.set_https(True)
                self._proxy_sock.sendall(request.to_data())
                # 将响应信息返回给客户端
                errMsg = ''
                try:
                    response = Response(request, self._proxy_sock)
                except ConnectionResetError:
                    response = None
                    errMsg = 'because ConnectionResetError'
                except _socket.timeout:
                    response = None
                    errMsg = 'because socket timeout'
                except http.client.BadStatusLine as e:
                    response = None
                    errMsg = 'because BadStatusLine {}'.format(str(e))

                if response:
                    try:
                        self.request.sendall(response.to_data())
                    except BrokenPipeError:
                        pass
                    except OSError:
                        pass
                else:
                    self.send_error(404, 'response is None {}'.format(errMsg))
                if not self._is_replay() and response:
                    netloc = "http"
                    if request.https:
                        netloc = "https"
                    if (netloc == "https" and int(request.port) == 443) or (
                            netloc == "http" and int(request.port) == 80):
                        url = "{0}://{1}{2}".format(netloc, request.hostname, request.path)
                    else:
                        url = "{0}://{1}:{2}{3}".format(netloc, request.hostname, request.port,
                                                        request.path)
                    method = request.command.lower()
                    if method == "get":
                        method = HTTPMETHOD.GET
                    elif method == "post":
                        method = HTTPMETHOD.POST
                    elif method == "put":
                        method = HTTPMETHOD.PUT

                    print(1)     #  入口点
                    print(url, request._headers, method, request.get_body_data().decode('utf-8'))

                    req = FakeReq(url, request._headers, method, request.get_body_data().decode('utf-8'))
                    resp = FakeResp(int(response.status), response.get_body_data(), response._headers)
                    KB['task_queue'].put(('loader', req, resp))

            else:
                self.send_error(404, 'request is None')
        except ConnectionResetError:
            pass
        except ConnectionAbortedError:
            pass
        except (BrokenPipeError, IOError):
            pass
        except Exception:
            errMsg = "W13scan baseproxy get request traceback:\n"
            errMsg += "Running version: {}\n".format(VERSION)
            errMsg += "Python version: {}\n".format(sys.version.split()[0])
            errMsg += "Operating system: {}".format(platform.platform())
            if request:
                errMsg += '\n\nrequest raw:\n'
                errMsg += request.to_data().decode()
            excMsg = traceback.format_exc()
            dataToStdout(errMsg)
            dataToStdout(excMsg)

    do_HEAD = do_GET
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET

    def _proxy_to_ssldst(self):
        '''
        代理连接https目标服务器
        :return:
        '''
        ##确定一下目标的服务器的地址与端口

        # 如果之前经历过connect
        # CONNECT www.baidu.com:443 HTTP 1.1
        self.hostname, self.port = self.path.split(':')
        self.proxy_connect()
        # 进行SSL包裹
        self._proxy_sock = wrap_socket(self._proxy_sock)

    def _proxy_to_dst(self):
        # 代理连接http目标服务器
        # http请求的self.path 类似http://www.baidu.com:80/index.html
        u = urlparse(self.path)
        if u.scheme != 'http':
            raise Exception('Unknown scheme %s' % repr(u.scheme))
        self.hostname = u.hostname
        self.port = u.port or 80
        # 将path重新封装，比如http://www.baidu.com:80/index.html会变成 /index.html
        self._target = self.path
        self.path = urlunparse(
            ParseResult(scheme='', netloc='', params=u.params, path=u.path or '/', query=u.query, fragment=u.fragment))
        self.proxy_connect()

    def connect_intercept(self):
        '''
        需要解析https报文,包装socket
        :return:
        '''
        try:
            # 首先建立和目标服务器的链接
            self._proxy_to_ssldst()
            # 建立成功后,proxy需要给client回复建立成功
            self.send_response(200, "Connection established")
            self.end_headers()

            # 这个时候需要将客户端的socket包装成sslsocket,这个时候的self.path类似www.baidu.com:443，根据域名使用相应的证书
            try:
                self.request = wrap_socket(self.request, server_side=True,
                                           certfile=self.server.ca[self.path.split(':')[0]])
            except SSLError:
                return

            self.setup()
            self.ssl_host = 'https://%s' % self.path
            self.handle_one_request()
        except Exception as e:
            try:
                self.send_error(500, str(e))
            except:
                return
            return

    def connect_relay(self):
        '''
        对于https报文直接转发
        '''

        self.hostname, self.port = self.path.split(':')
        try:
            self.proxy_connect()
        except Exception as e:
            self.send_error(500)
            return

        self.send_response(200, 'Connection Established')
        self.end_headers()

        inputs = [self.request, self._proxy_sock]

        while True:
            readable, writeable, errs = select.select(inputs, [], inputs, 10)
            if errs:
                break
            for r in readable:
                try:
                    data = r.recv(8092)
                    if data:
                        if r is self.request:
                            self._proxy_sock.sendall(data)
                        elif r is self._proxy_sock:
                            self.request.sendall(data)
                    else:
                        break
                except ConnectionResetError:
                    break
                except TimeoutError:
                    break
        self.request.close()
        self._proxy_sock.close()

    def _send_ca(self):
        # 发送CA证书给用户进行安装并信任
        cert_path = self.server.ca.cert_file_path
        with open(cert_path, 'rb') as f:
            data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', 'application/x-x509-ca-cert')
        self.send_header('Content-Length', len(data))
        self.send_header('Connection', 'close')
        self.send_header('Content-disposition', 'attachment;filename=download.crt')
        self.end_headers()
        self.wfile.write(data)

    def mitm_request(self, req, resp):
        for p in self.server.req_plugs:
            req = p(self.server).deal_request(req, resp)
        return req

    def log_message(self, format, *args):
        pass


class MitmProxy(HTTPServer):

    def __init__(self, server_addr=('', 8788), request_handler_class=ProxyHandle, bind_and_activate=True, https=True):
        HTTPServer.__init__(self, server_addr, request_handler_class, bind_and_activate)
        logger.info('HTTPServer is running at address(\'%s\',\'%d\')......' % (server_addr[0], server_addr[1]))
        self.req_plugs = []
        self.ca = CAAuth(ca_file="ca.pem", cert_file='ca.crt')
        self.https = https

    def register(self, intercept_plug):
        self.req_plugs.append(intercept_plug)


class ProxyMinIn(ThreadingMixIn):
    daemon_threads = True


class AsyncMitmProxy(ProxyMinIn, MitmProxy):
    pass


class InterceptPlug(object):

    def __init__(self, server):
        self.server = server
