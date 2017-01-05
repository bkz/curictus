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

import datetime
import logging
import os
import shutil
import sys
import time

import vrs.db.sync

from vrs import SessionLog
from vrs.client import syncdb
from vrs.db.schema import Station, Activity, Patient, Session
from vrs.db.utils import transactional
from vrs.db.sync import SyncAPI
from vrs.util import remotepy
from vrs.util import singleinstance

_log = logging.getLogger('vrs-sync')

###########################################################################
# Ping sync server.
###########################################################################

def ping_server(rpc, config):
    """
    Ping master server with current IP and station information from ``config``
    to let it to if we are active or not.
    """
    vrs_ip = "127.0.0.1"
    try:
        # Figure out the IP assigned to the virtual OpenVPN TUN-device.
        import socket
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip.startswith('10.3'):
                vrs_ip = ip
                break
        else:
            # If we couldn't detect a suitable OpenVPN interface there isn't
            # much else to do but report the IP of the interface used to
            # connect to the Internet. It might be a public IP but most times
            # it will a local IP assigned via DHCP.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('google.com', 80))
            vrs_ip = s.getsockname()[0]
    except Exception:
        pass # Network access not available.
    return rpc.invoke(SyncAPI.ping, config, vrs_ip)


###########################################################################
# Sync client DB.
###########################################################################

def is_zone_modified(config):
    try:
        rpc = remotepy.RemotePyClient(config.REMOTE_ADDR, "/remotepy/rpc/", port=config.REMOTE_PORT)
        if ping_server(rpc, config):
            return rpc.invoke(SyncAPI.is_zone_modified, config)
    except remotepy.RemotePyConnectError:
        _log.warning("RemotePy server %s:%s not responding" % (config.REMOTE_ADDR, config.REMOTE_PORT))
    except Exception:
        _log.exception("Unhandled exception while determining if station needs to sync")
    return False


def backup_sessionlog(filepath, directory):
    """
    Securely backup session log ``filepath`` into a timestamped (ex:
    '<dir>/2010/05/<filename>.xml.gz') folder in ``directory``.
    """
    backupdir = os.path.join(directory, time.strftime("%Y/%m"))
    try:
        if not os.path.isdir(backupdir):
            os.makedirs(backupdir)
        shutil.copy(filepath, backupdir)
        os.remove(filepath)
    except Exception:
        _log.exception("Exception while backing up session log: %s" % filepath)


def sync_sessionlogs(rpc, config, db, stopevent):
    log_directory = os.environ["CUREGAME_TEMPPATH"]
    log_files = [filename for filename in os.listdir(log_directory)
                 if filename.endswith(".xml.gz")]
    _log.info("Syncing %d session logs from %s" % (len(log_files), log_directory))
    for filename in log_files:
        if stopevent.isSet(): break
        filepath = os.path.join(log_directory, filename)
        vrs.db.sync.import_sessionlog(config, db, filepath)
        try:

            session = SessionLog.load(filepath, password=config.SESSION_SECRET)
        except IOError, e:
            _log.exception("Failed to load session log: %s" % filepath)
            # Rename corrupted logs to keep us from processing them on every
            # sync attempt. Will require manual investigation but in most cause
            # there isn't really much to do.
            os.rename(filepath, filepath + "-corrupt.%s" % time.time())
            continue
        rpc.invoke(SyncAPI.upload_sessionlog, session.zone.get("guid"), session.guid, session.toxml())
        backup_sessionlog(filepath, os.environ["CUREGAME_SESSIONLOG_PATH"])


def sync_station(config, db, stopevent):
    try:
        rpc = remotepy.RemotePyClient(config.REMOTE_ADDR, "/remotepy/rpc/", port=config.REMOTE_PORT)
        if ping_server(rpc, config):
            # Sync DB tables before session logs to get the system in a usable
            # state as quickly as possible, the logs should be treated a backup
            # task with much lower priority.
            try:
                # Forcefully expire entire SQLAlchemy identity map to force data to be
                # re-fetched from the DB before performing the sync.
                db.expire_all()
                syncdb.sync_tables(rpc, config, db, stopevent,
                                   client_tables=[Station, Activity, Patient, Session],
                                   server_tables=[Station, Activity, Patient, Session])
                sync_sessionlogs(rpc, config, db, stopevent)
                return True
            except Exception:
                db.rollback()
                raise
        else:
            _log.warning("Server denied sync ping (software update needed?)")
    except remotepy.RemotePyConnectError:
        _log.warning("RemotePy server %s:%s not responding" % (config.REMOTE_ADDR, config.REMOTE_PORT))
    except Exception:
        _log.exception("Unhandled exception while syncing station")
    return False


###########################################################################
# Background sync thread (data uploader).
###########################################################################

import Queue
import threading

class DBSyncThread(threading.Thread):
    """
    Thread for running a (stoppable) VRS DB synchronizer.
    """

    def __init__(self, config, jobqueue, db):
        self.config = config
        self.jobqueue = jobqueue
        self.db = db
        self.stopevent = threading.Event()
        self.triggerEvent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(DBSyncThread, self).__init__()


    @transactional
    def import_sessionlog(self, filepath):
        vrs.db.sync.import_sessionlog(self.config, self.db, filepath)


    def run(self):
        # Note: we don't run the main sync loop inside a transaction since we
        # want the system to be able to recover from failures in a more
        # fine-grained style. Exceptions or DB failures which bubble up to this
        # level should be treated as fatal errors.
        try:
            self.started.set()

            # Syncing is performed as following:
            #
            # (1) A default sync always occurs no matter after
            # DEFAULT_SYNC_INTERVAL_SEC to make sure that we always get the
            # latest data.
            #
            # (2) Sync can be trigger from outside this loop via the trigger()
            # function which is supposed to be called whenever a DB commit
            # occurs.
            #
            # (3) We ping the server every ZONE_MODIFIED_CHECK_INTERVAL_SEC to
            # see if some other client (station) in the zone has commited data
            # and if so we trigger a sync. This keep us from pounding the
            # server with frequent heavy-weight sync requests, the server is
            # free to maintain a per zone flag which it can use to hint us to
            # take the appropriate action.
            #
            # (4) Should a sync operation fail we'll attempt to automatically
            # retry after DEFAULT_RETRY_SYNC_ON_ERROR_INTERVAL_SEC. Likely
            # causes are stale client (who need a software update) or fragile
            # network connections.

            DEFAULT_SYNC_INTERVAL_SEC = 15*60

            DEFAULT_RETRY_SYNC_ON_ERROR_INTERVAL_SEC = 30

            ZONE_MODIFIED_CHECK_INTERVAL_SEC = 10

            TRIGGER_SYNC_WAIT_TIME_SEC = 5

            next_sync, last_sync = time.time(), time.time()

            while not self.stopevent.isSet():
                # Triggered sync results in a sync attempt after a period
                # waiting to prevent a small period of time to prevent lots of
                # serial commits to trigger individual requests.
                if self.triggerEvent.isSet():
                    self.triggerEvent.clear()
                    next_sync = time.time() + TRIGGER_SYNC_WAIT_TIME_SEC
                if time.time() > next_sync:
                    if sync_station(self.config, self.db, self.stopevent):
                        last_sync = time.time()
                        next_sync = last_sync + DEFAULT_SYNC_INTERVAL_SEC
                    else:
                        last_sync = time.time()
                        next_sync = last_sync + DEFAULT_RETRY_SYNC_ON_ERROR_INTERVAL_SEC
                elif (time.time() - last_sync) > ZONE_MODIFIED_CHECK_INTERVAL_SEC:
                    if is_zone_modified(self.config):
                        _log.info("Zone modified, triggering DB sync")
                        self.triggerEvent.set()
                    last_sync = time.time()
                else:
                    time.sleep(0.1)
        except Exception, e:
            _log.exception("Unhandled exception in DBSyncThread.run()")
            self.error = e
            self.started.set()


    def stop(self, timeout=None):
        self.stopevent.set()
        threading.Thread.join(self, timeout)



dbsync_thread = None

def start(config, jobqueue, db):
    """
    Start background VRS DB synchronizer thread.
    """
    global dbsync_thread
    dbsync_thread = DBSyncThread(config, jobqueue, db)
    dbsync_thread.start()
    dbsync_thread.started.wait()
    if dbsync_thread.error:
        _log.warning("Caught exception in DB sync thread during startup")
        raise dbsync_thread.error


def trigger():
    """
    Signal to background VRS DB thread that we want to manually trigger a sync.
    """
    global dbsync_thread
    if dbsync_thread:
        dbsync_thread.triggerEvent.set()


def stop():
    """
    Stop background VRS DB synchronizer thread.
    """
    global dbsync_thread
    if dbsync_thread:
        _log.info("Stopping DB sync thread")
        dbsync_thread.stop()
        if dbsync_thread.error:
            _log.warning("Caught exception in DB sync thread during shutdown")


def import_sessionlog(filepath):
    """
    Import and backup session log ``filepath``.
    """
    global dbsync_thread
    if dbsync_thread is not None:
        dbsync_thread.import_sessionlog(filepath) # Use sync thread to get DB handle.
    else:
        _log.warning("Attempted to import session log without active sync thread")


###########################################################################
# VRS syncer entry-point (standalone mode).
###########################################################################

DEBUG = (os.environ["CUREGAME_OPT_DEBUG"] == "1")

def main():
    try:
        if not singleinstance.lock("vrs-sync"):
            _log.warning("An instance of VRS sync is already running")
            return

        from vrs.config import Config
        config = Config(os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"))

        if not config.FEATURES["enable_data_sync"]:
            return # Treat pings as a form of data synchronization.

        rpc = remotepy.RemotePyClient(config.REMOTE_ADDR, "/remotepy/rpc/", port=config.REMOTE_PORT)

        try:
            if not ping_server(rpc, config):
                _log.warning("Server denied sync ping (software update needed?)")
        except remotepy.RemotePyConnectError:
            _log.warning("RemotePy server %s:%s not responding" % (config.REMOTE_ADDR, config.REMOTE_PORT))

    except KeyboardInterrupt:
        pass
    except:
        if not DEBUG:
            _log.exception("Unhandled exception in VRS sync")
            from vrs.debug import email_crashreport
            email_crashreport(
                os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"),
                os.environ["CUREGAME_LOGPATH"])


###########################################################################
# The End.
###########################################################################
