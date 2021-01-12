import inspect
import os
import sys
import threading
from w13scan.lib.controller.controller import start
from w13scan.lib.parse.parse_request import FakeReq
from w13scan.lib.parse.parse_responnse import FakeResp

from w13scan.lib.core.data import KB
from w13scan.lib.core.option import init


def modulePath():
    """
    This will get us the program's directory, even if we are frozen
    using py2exe
    """

    try:
        _ = sys.executable if hasattr(sys, "frozen") else __file__
    except NameError:
        _ = inspect.getsourcefile(modulePath)

    return os.path.dirname(os.path.realpath(_))


def main(url, request_headers,method,request_body,status_code,respone_body,respone_headers):

    root = modulePath()
    init(root)

    KB["continue"] = True
    # 启动漏洞扫描器
    scanner = threading.Thread(target=start)
    scanner.setDaemon(True)
    scanner.start()

    req = FakeReq(url, request_headers, method, request_body)
    resp = FakeResp(status_code, respone_body, respone_headers)
    KB['task_queue'].put(('loader', req, resp))
