"""Base classes for server/gateway implementations"""

from types import StringType
import sys, os, time
import mimetools
import urllib
import socket
from util import is_hop_by_hop, Headers, format_date_time

__all__ = ['WSGIRequestHandler', 'SimpleHandler']


class WSGIRequestHandler(object):

    rbufsize = -1
    wbufsize = 0
    timeout = 10

    default_request_version = "HTTP/1.1"

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()

        try:
            self.handle()
        finally:
            self.finish()

    def setup(self):
        self.log_message("client_address:%s", self.client_address[:2])
        self.connection = self.request
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.connection.settimeout(self.timeout)
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)

    def address_string(self):
        host, port = self.client_address[:2]
        return socket.getfqdn(host)

    def get_environ(self):
        env = self.server.base_environ.copy()
        env['SERVER_PROTOCOL'] = self.request_version
        env['REQUEST_METHOD'] = self.command
        if '?' in self.path:
            path,query = self.path.split('?',1)
        else:
            path,query = self.path,''

        env['PATH_INFO'] = urllib.unquote(path)
        env['QUERY_STRING'] = query

        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]

        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader

        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for h in self.headers.headers:
            k,v = h.split(':',1)
            k=k.replace('-','_').upper(); v=v.strip()
            if k in env:
                continue                    # skip content length, type,etc.
            if 'HTTP_'+k in env:
                env['HTTP_'+k] += ','+v     # comma-separate multiple headers
            else:
                env['HTTP_'+k] = v
        return env

    def parse_request(self):
        """Parse a request (internal).
        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = self.raw_requestline
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()

        if len(words) == 3:
            command, path, version = words
        elif len(words) == 2:
            command, path = words
        elif not words:
            return False
        else:
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive
        self.headers = self.MessageClass(self.rfile, 0)

        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'keep-alive':
            self.close_connection = 0
        return True

    def handle(self):
        """Handle a single HTTP request"""

        self.raw_requestline = self.rfile.readline(65537)
        if not self.parse_request():
            return

        handler = SimpleHandler(
            self.rfile, self.wfile, sys.stderr, self.get_environ()
        )
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())

    def log_request(self, code='-', size='-'):
        """Log an accepted request.
        """
        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def log_message(self, format, *args):
        import datetime
        date_time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          date_time_string,
                          format%args))

    def finish(self):
        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except:
                pass
        self.wfile.close()
        self.rfile.close()

    MessageClass = mimetools.Message

    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
              'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
        }


class SimpleHandler(object):
    """Manage the invocation of a WSGI application"""

    # Configuration parameters; can override per-subclass or per-instance
    wsgi_version = (1,0)
    wsgi_multithread = True
    wsgi_multiprocess = True
    wsgi_run_once = False

    http_version  = "1.1"   # Version that should be used for response

    # os_environ is used to supply configuration from the OS environment:
    # by default it's a copy of 'os.environ' as of import time, but you can
    # override this in e.g. your __init__ method.
    os_environ = dict(os.environ.items())

    status = result = None
    headers_sent = False
    headers = None
    bytes_sent = 0

    def __init__(self,stdin,stdout,stderr,environ,
        multithread=True, multiprocess=False
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.base_env = environ
        self.wsgi_multithread = multithread
        self.wsgi_multiprocess = multiprocess

    def run(self, application):
        """Invoke the application"""
        try:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
        except:
            self.handle_error()
        finally:
            self.close()

    def handle_error(self):
        """Log current error, and send error output to client if possible"""
        self.log_exception(sys.exc_info())
        if not self.headers_sent:
            self.result = self.error_output(self.environ, self.start_response)
            self.finish_response()

    def error_output(self, environ, start_response):
        """WSGI mini-app to create error output
        """
        error_status = "500 Internal Server Error"
        error_headers = [('Content-Type','text/plain')]
        error_body = "A server error occurred.  Please contact the administrator."
        start_response(error_status, error_headers[:], sys.exc_info())
        return [error_body]

    def log_exception(self,exc_info):
        """Log the 'exc_info' tuple in the server log
        """
        try:
            from traceback import print_exception
            stderr = sys.stderr
            print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                None, stderr
            )
            stderr.flush()
        finally:
            exc_info = None

    def setup_environ(self):
        """Set up the environment for one request"""

        env = self.environ = self.os_environ.copy()
        self.environ.update(self.base_env) # Add cgi env vars

        env['wsgi.input']        = self.stdin
        env['wsgi.errors']       = self.stderr
        env['wsgi.version']      = self.wsgi_version
        env['wsgi.run_once']     = self.wsgi_run_once
        env['wsgi.url_scheme']   = self.get_scheme()
        env['wsgi.multithread']  = self.wsgi_multithread
        env['wsgi.multiprocess'] = self.wsgi_multiprocess

    def finish_response(self):
        """Send any iterable data, then close self and the iterable
        """
        try:
            for data in self.result:
                self.write(data)
        finally:
            self.close()

    def get_scheme(self):
        """Return the URL scheme being used"""
        if self.environ.get("HTTPS") in ('yes','on','1'):
            return 'https'
        else:
            return 'http'

    def set_content_length(self):
        """Compute Content-Length or switch to chunked encoding if possible"""
        try:
            blocks = len(self.result)
        except (TypeError,AttributeError,NotImplementedError):
            pass
        else:
            if blocks==1:
                self.headers['Content-Length'] = str(self.bytes_sent)
                return

    def cleanup_headers(self):
        if 'Content-Length' not in self.headers:
            self.set_content_length()

    def start_response(self, status, headers,exc_info=None):
        """'start_response()' callable as specified by PEP 333"""

        if exc_info:
            try:
                if self.headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None        # avoid dangling circular ref
        elif self.headers is not None:
            raise AssertionError("Headers already set!")

        self.status = status
        self.headers = Headers(headers)
        return self.write

    def send_preamble(self):
        """Transmit version/status/date/server"""
        self._write('HTTP/%s %s\r\n' % (self.http_version,self.status))
        if 'Date' not in self.headers:
            self._write(
                'Date: %s\r\n' % format_date_time(time.time())
            )
        if 'Server' not in self.headers:
            self._write('Server: WSGIServer\r\n')

    def write(self, data):
        """'write()' callable as specified by PEP 333"""

        assert type(data) is StringType,"write() argument must be string"

        if not self.status:
            raise AssertionError("write() before start_response()")
        elif not self.headers_sent:
            # Before the first output, send the stored headers
            self.bytes_sent = len(data)    # make sure we know content-length
            self.send_headers()
        else:
            self.bytes_sent += len(data)

        # XXX check Content-Length and truncate if too many bytes written?
        self._write(data)
        self.stdout.flush()

    def _write(self, data):
        self.stdout.write(data)

    def close(self):
        """Close the iterable (if needed) and reset all instance vars
        """
        try:
            if hasattr(self.result, 'close'):
                self.result.close()
        finally:
            self.result = self.headers = self.status = self.environ = None
            self.bytes_sent = 0
            self.headers_sent = False

    def send_headers(self):
        """Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = True
        self.send_preamble()
        self.stdout.write(str(self.headers))
