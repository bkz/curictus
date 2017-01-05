##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import os
import datetime
import logging
import threading
import time
import uuid

_log = logging.getLogger('client')

##############################################################################
# Setup local dashboard service server.
##############################################################################

from amfast.encoder import Encoder
from amfast.decoder import Decoder
from amfast.class_def import ClassDefMapper
from amfast.remoting.tornado_channel import TornadoChannelSet, TornadoChannel

from vrs import as3rpc
from vrs.client.DashboardService import DashboardService

EXPOSE_SERVICES = [DashboardService]

def createserver(config, jobqueue, db):
    channel_set = TornadoChannelSet()
    polling_channel = TornadoChannel('amf')
    channel_set.mapChannel(polling_channel)
    class_mapper = ClassDefMapper()
    encoder = Encoder(amf3=True, use_collections=True, use_proxies=True, use_references=True, class_def_mapper=class_mapper)
    decoder = Decoder(amf3=True, class_def_mapper=class_mapper)
    for channel in channel_set:
        channel.endpoint.encoder = encoder
        channel.endpoint.decoder = decoder

    srcpath = os.path.join(os.environ["CUREGAME_ROOT"], "../flex/lib/")
    if not os.path.exists(srcpath):
        srcpath = None

    for klass in EXPOSE_SERVICES:
        as3rpc.bind_amfast_service(klass, channel_set, class_mapper, args=(config, jobqueue, db), srcpath=srcpath)

    bin_path = os.path.join(os.environ["CUREGAME_ROOT"], "../flex/Dashboard/bin")
    static_path = os.path.join(os.environ["CUREGAME_ROOT"], "media")
    template_path = os.path.join(os.environ["CUREGAME_ROOT"], "media/html")
    return tornado.web.Application([
            (r"/dashboard/amf/", polling_channel.request_handler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": bin_path}),
            ], static_path=static_path, template_path=template_path)


##############################################################################
# Background Tornado web server thread.
##############################################################################

import tornado.ioloop
import tornado.httpserver
import tornado.web

class ServerThread(threading.Thread):
    def __init__(self, config, application):
        self.config = config
        self.application = application
        self.stopevent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(ServerThread, self).__init__()

    def run(self):
        try:
            server = tornado.httpserver.HTTPServer(self.application)
            server.listen(self.config.LOCAL_PORT, self.config.LOCAL_ADDR)
            io_loop = tornado.ioloop.IOLoop.instance()
            stophandler = tornado.ioloop.PeriodicCallback(self.check_stop, 500)
            stophandler.start()
            self.started.set()
            io_loop.start()
        except Exception, e:
            _log.exception("Unhandled exception in ServerThread.run()")
            self.error = e
            self.started.set()

    def stop(self, timeout=None):
        self.stopevent.set()
        threading.Thread.join(self, timeout)

    def check_stop(self):
        if self.stopevent.isSet():
            tornado.ioloop.IOLoop.instance().stop()


##############################################################################
# Module public interface.
##############################################################################

import vrs.db

server_thread = None


def get_db_url(config):
    return vrs.db.make_sqlite_url(os.path.join(os.environ["CUREGAME_TEMPPATH"], "vrs.db"))


def analyze_db(config, metadata):
    from vrs.db import migrate
    return migrate.analyze(get_db_url(config), metadata)


def upgrade_db(config):
    from vrs.db import migrate
    repository = os.path.join(os.path.dirname(__file__), "migrations")
    return migrate.upgrade(get_db_url(config), repository)


def connect_db(config, on_commit=None, debug=False, reset=False):
    filename = os.path.join(os.environ["CUREGAME_TEMPPATH"], "vrs.db")
    if reset and os.path.exists(filename):
        os.remove(filename)

    upgrade_db(config)

    db = vrs.db.connect_sqlite(filename, debug)

    from vrs.client import schema
    schema.setupDB(db, config)

    if analyze_db(config, schema.metadata):
        raise RuntimeError("DB schema not up to date")

    if on_commit:
        vrs.db.register_commit_hook(on_commit)

    return db


def start(config, jobqueue, db):
    global server_thread
    application = createserver(config, jobqueue, db)
    server_thread = ServerThread(config, application)
    server_thread.start()
    server_thread.started.wait()
    if server_thread.error:
        _log.warning("Caught exception in HTTP server thread during startup")
        raise server_thread.error


def stop():
    global server_thread
    if server_thread:
        _log.info("Stopping HTTP server thread")
        server_thread.stop()
        if server_thread.error:
            _log.warning("Caught exception in HTTP server thread during shutdown")


##############################################################################
# The End.
##############################################################################
