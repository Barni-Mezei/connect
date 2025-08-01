#!/usr/bin/env python

#Tornado
from tornado.options import options, define
import tornado.httpserver
import tornado.ioloop
import tornado.web

import signal

#Import other files
from color import Color
from socket_handler import SocketHandler

define('port', type = int, default = 5500)
define('address', type = str, default = "0.0.0.0")

indexHtml = "index.html"
errorHtml = "404.html"

class RootHandler(tornado.web.RequestHandler):
    def get(self): self.render(indexHtml)

class NotFoundHandler(tornado.web.RequestHandler):
    def get(self):
        #self.render(errorHtml)
        with open(errorHtml, "r", encoding="utf8") as f:
            self.write(f.read())

class PublicResourceHandler(tornado.web.StaticFileHandler): pass

def main():
    tornado_app = tornado.web.Application([
        ('/', RootHandler),
        (r'/websocket', SocketHandler),
        (r'/public/(.*)', PublicResourceHandler, {"path": "./public/"}),
        (r".*", NotFoundHandler)

    ])
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)

    print(Color.paint("Server started", Color.green))

    #Start server
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        SocketHandler.fullStop()
        tornado.ioloop.IOLoop.instance().stop()

    # '\b\b' to remove '^C'
    print(Color.paint("\b\bServer stopped", Color.red))

if __name__ == '__main__':
    main()