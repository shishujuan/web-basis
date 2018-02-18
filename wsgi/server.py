#!/usr/bin/env python

import sys
import socket
import select
import errno
from handlers import WSGIRequestHandler

DEFAULT_ERROR_MESSAGE = """\
<head>
<title>Error response</title>
</head>
<body>
<h1>Error response</h1>
<p>Error code %(code)d.
<p>Message: %(message)s.
<p>Error code explanation: %(code)s = %(explain)s.
</body>
"""

DEFAULT_ERROR_CONTENT_TYPE = "text/html"


def _eintr_retry(func, *args):
    while True:
        try:
            return func(*args)
        except (OSError, select.error) as e:
            if e.args[0] != errno.EINTR:
                raise

class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    application = None
    __shutdown_request = False

    def __init__(self, server_address, RequestHandlerClass):
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.socket = socket.socket(self.address_family, self.socket_type)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.server_address)
            host, port = self.socket.getsockname()[:2]
            self.server_name = socket.getfqdn(host)
            self.server_port = port
            self.server_address = self.socket.getsockname()
            self.setup_environ()
            self.socket.listen(self.request_queue_size)
        except:
            self.socket.close()
            raise

    def fileno(self):
        return self.socket.fileno()

    def serve_forever(self, poll_interval=0.5):
        try:
            while not self.__shutdown_request:
                r, w, e = _eintr_retry(select.select, [self], [], [], poll_interval)
                if self in r:
                    self.handle_request_noblock()
        finally:
            self.socket.close()

    def handle_request_noblock(self):
        try:
            request, client_address = self.socket.accept()
        except socket.error:
            return
        self.RequestHandlerClass(request, client_address, self)
        request.close()

    def setup_environ(self):
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST']=''
        env['CONTENT_LENGTH']=''
        env['SCRIPT_NAME'] = ''

    def get_app(self):
        return self.application

    def set_app(self,application):
        self.application = application


def make_server(
        host, port, app, server_class=WSGIServer,
        handler_class=WSGIRequestHandler
):
    server = server_class((host, port), handler_class)
    server.set_app(app)
    server.serve_forever()


if __name__ == "__main__":
    from app import simple_app, AppClass
    make_server("", 8000, AppClass)
