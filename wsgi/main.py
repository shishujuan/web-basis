#!/usr/bin/env python

from handlers import WSGIRequestHandler
from server import WSGIServer

def make_server(
        host, port, app, server_class=WSGIServer,
        handler_class=WSGIRequestHandler
):
    server = server_class((host, port), handler_class)
    server.set_app(app)
    server.serve_forever()


if __name__ == "__main__":
    from app import simple_app, AppClass
    #make_server("", 8000, AppClass)
    make_server("", 8000, simple_app)
