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
import hashlib
import logging
import threading
import time
import uuid

import tornado.ioloop
import tornado.httpserver
import tornado.web

import vrs.db
from vrs.db.utils import transactional
from vrs.locale import translate as _
from vrs.util import remotepy

_log = logging.getLogger('vrs-server')

##############################################################################
# Admin interface HTTP request handlers.
##############################################################################

from vrs.server.schema import Zone, Station, SyncMetaData

ADMIN_USERS = ["babar", "daniel", "mihaela"]
ADMIN_PASSWORD_SHA1 = "6967084c27279e5a5b842e5b592d8d98279f729f"

class AdminBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class AdminLoginHandler(AdminBaseHandler):
    def get(self):
        self.render("login.html", next=self.get_argument("next","/"))

    def post(self):
        url = self.get_argument("next", "/")
        user = self.get_argument("user", "")
        password = hashlib.sha1(self.get_argument("password", "")).hexdigest()
        if user in ADMIN_USERS and password == ADMIN_PASSWORD_SHA1:
            self.set_secure_cookie("user", user)
            self.redirect(url)
        else:
            self.clear_cookie("user")
            self.redirect("/admin/login/?next=%s" % url)


class AdminLogoutHandler(AdminBaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("http://www.curictus.com")


class AdminListStationsHandler(AdminBaseHandler):
    def __init__(self, application, request, db):
        AdminBaseHandler.__init__(self, application, request)
        self.db = db

    @transactional
    @tornado.web.authenticated
    def get(self):
        syncdata = self.db.query(SyncMetaData).join(Zone).order_by(Zone.alias).all()
        self.render("admin.html", syncdata=syncdata)


class AdminResetClientSyncHandler(AdminBaseHandler):
    def __init__(self, application, request, db):
        AdminBaseHandler.__init__(self, application, request)
        self.db = db

    @transactional
    @tornado.web.authenticated
    def post(self):
        station_guid = self.get_argument("station_guid")
        metadata = self.db.query(SyncMetaData)\
            .join(Station)\
            .filter(Station.guid == station_guid)\
            .one()
        metadata.last_sync = datetime.datetime(1970, 1, 1)
        metadata.need_sync = True
        self.db.commit()
        self.redirect("/admin/list/")


class AdminStatusCheckHandler(AdminBaseHandler):
    def __init__(self, application, request, db):
        AdminBaseHandler.__init__(self, application, request)
        self.db = db

    def get(self):
        self.write("OK(%d)" % self.db.query(SyncMetaData).count())


##############################################################################
# Flash/Flex HTML wrapper.
##############################################################################

class FlashAppHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, config, title, flash_id, flash_version, flash_movie, movie_md5):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.config, self.title = config, title
        self.flash_id = flash_id
        self.flash_movie = flash_movie
        self.flash_version = flash_version
        self.movie_md5 = movie_md5

    def get_user_locale(self):
        return tornado.locale.get(self.config.SYSTEM_LOCALE)

    def get(self):
        self.render("flash.html")


##############################################################################
# Setup PCMS service server.
##############################################################################

from amfast.encoder import Encoder
from amfast.decoder import Decoder
from amfast.class_def import ClassDefMapper
from amfast.remoting.tornado_channel import TornadoChannelSet, TornadoChannel

from vrs import as3rpc
from vrs.server.PCMService import PCMService, GeneratePatientExcelHandler

EXPOSE_SERVICES = [PCMService]

def createserver(config, rootdir, db):
    channel_set = TornadoChannelSet()
    polling_channel = TornadoChannel('amf')
    channel_set.mapChannel(polling_channel)
    class_mapper = ClassDefMapper()
    encoder = Encoder(amf3=True, use_collections=True, use_proxies=True, use_references=True, class_def_mapper=class_mapper)
    decoder = Decoder(amf3=True, class_def_mapper=class_mapper)
    for channel in channel_set:
        channel.endpoint.encoder = encoder
        channel.endpoint.decoder = decoder

    srcpath = os.path.join(rootdir, "../flex/lib/")
    if not os.path.exists(srcpath):
        srcpath = None

    for klass in EXPOSE_SERVICES:
        as3rpc.bind_amfast_service(klass, channel_set, class_mapper, args=(config, db), srcpath=srcpath)

    swf_path = os.path.join(rootdir, "media/swf")
    static_path = os.path.join(rootdir, "media")
    template_path = os.path.join(rootdir, "media/html")
    pcms_md5 = hashlib.md5(open(os.path.join(swf_path, "pcms.swf"), "rb").read()).hexdigest()

    return tornado.web.Application([
            (r"/remotepy/rpc/", remotepy.RemotePyHandler),
            (r"/pcms/amf/", polling_channel.request_handler),
            (r"/pcms/excel/", GeneratePatientExcelHandler, {"db" : db}),
            (r"/admin/login/", AdminLoginHandler),
            (r"/admin/logout/", AdminLogoutHandler),
            (r"/admin/list/", AdminListStationsHandler, {"db" : db}),
            (r"/admin/reset/sync/", AdminResetClientSyncHandler, {"db" : db}),
            (r"/admin/status/", AdminStatusCheckHandler, {"db" : db}),
            (r"/", FlashAppHandler, {"config":config, "title" : _("VRS Analytics"), "flash_id":"pcms", "flash_version": "10.1.0", "flash_movie":"pcms.swf", "movie_md5":pcms_md5}),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": swf_path}),
            ], login_url="/admin/login/", cookie_secret="529397d22d7bd16a1f4616726f3312fe4d4b48c1", static_path=static_path, template_path=template_path)


##############################################################################
# Module public interface.
##############################################################################

def get_db_url(config):
    if config.POSTGRES_DB and config.POSTGRES_USER:
        return vrs.db.make_postgres_url(config.POSTGRES_DB, config.POSTGRES_USER, config.POSTGRES_PASS, config.POSTGRES_PORT)
    else:
        filename = os.path.join(os.environ["CUREGAME_TEMPPATH"], "server.db")
        return vrs.db.make_sqlite_url(filename)


def analyze_db(config, metadata):
    from vrs.db import migrate
    return migrate.analyze(get_db_url(config), metadata)


def upgrade_db(config):
    from vrs.db import migrate
    repository = os.path.join(os.path.dirname(__file__), "migrations")
    return migrate.upgrade(get_db_url(config), repository)


def connect_db(config):
    if config.POSTGRES_DB and config.POSTGRES_USER:
        return vrs.db.connect_postgres(config.POSTGRES_DB, config.POSTGRES_USER, config.POSTGRES_PASS, config.POSTGRES_PORT)
    else:
        filename = os.path.join(os.environ["CUREGAME_TEMPPATH"], "server.db")
        return vrs.db.connect_sqlite(filename)


def main(rootdir):
    try:
        from vrs.config import Config
        config = Config(os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"))

        import vrs.locale
        i18n_path = os.path.join(rootdir, "media/i18n")
        vrs.locale.load_translations(i18n_path, "vrs")
        vrs.locale.set_locale(config.SYSTEM_LOCALE)

        upgrade_db(config)

        db = connect_db(config)

        from vrs.server import schema
        schema.setupDB(db, config)

        if analyze_db(config, schema.metadata):
            _log.warning("DB schema not up to date")
            return

        from vrs.db.sync import SyncAPI as ISyncAPI
        from vrs.server.syncdb import SyncAPI
        remotepy.register(SyncAPI(config, db), interface=ISyncAPI)

        def check_restart():
            if code_changed():
                _log.info("Server exiting to reload modified code")
                tornado.ioloop.IOLoop.instance().stop()

        _log.info("Starting PCMS %s server at http://%s:%s" % (
                config.SYSTEM_VERSION, config.REMOTE_ADDR, config.REMOTE_PORT))

        application = createserver(config, rootdir, db)
        server = tornado.httpserver.HTTPServer(application)
        server.listen(config.REMOTE_PORT, config.REMOTE_ADDR)
        io_loop = tornado.ioloop.IOLoop.instance()
        callback = tornado.ioloop.PeriodicCallback(check_restart, 500)
        callback.start()
        io_loop.start()

    except KeyboardInterrupt:
        _log.info("Server manual exit")


##############################################################################
# The End.
##############################################################################
