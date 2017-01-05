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

import logging
import datetime
import os

import sqlalchemy as sa

import vrs.db
import vrs.db.schema
import vrs.db.utils

from vrs.db.sync import SyncAPI as ISyncAPI
from vrs.db.utils import transactional

from vrs.server.schema import Zone, Station, SyncMetaData
from vrs.util import crypto
from vrs.util import remotepy

_log = logging.getLogger('vrs-syncdb')

###########################################################################
# Utilities.
###########################################################################

def get_sync_metadata(db, config):
    metadata = db.query(SyncMetaData)\
        .with_lockmode('update')\
        .filter(SyncMetaData.station_guid == config.STATION_GUID)\
        .first()
    if not metadata:
        one_year_ago = datetime.datetime.utcnow() - datetime.timedelta(365)
        metadata = SyncMetaData(zone_guid=config.ZONE_GUID, station_guid=config.STATION_GUID, last_sync=one_year_ago)
        db.add(metadata)
        db.commit()
    return metadata


###########################################################################
# Syncing RPC API implementation.
###########################################################################

class SyncAPI(ISyncAPI):
    def __init__(self, config, db):
        self.config, self.db = config, db


    @transactional
    def ping(self, config, ip4):
        if self.config.SYSTEM_VERSION != config.SYSTEM_VERSION:
            _log.warning("Version mismatch: %s (station: %s, zone: %s) is running %s" % (
                    config.STATION_ALIAS, config.STATION_GUID, config.ZONE_GUID, config.SYSTEM_VERSION))
            return False
        zone = self.db.query(Zone).filter(Zone.guid == config.ZONE_GUID).first()
        if not zone:
            _log.debug("Register client zone: %s" % config.ZONE_GUID)
            zone = Zone(guid=config.ZONE_GUID, alias=config.ZONE_GUID, password="", email="")
            self.db.add(zone)
            self.db.commit()
        station = self.db.query(Station).with_lockmode('update').filter(Station.guid == config.STATION_GUID).first()
        if not station:
            _log.debug("Register client station: %s (%s)" % (config.STATION_ALIAS, config.STATION_GUID))
            station = Station(zone=zone, guid=config.STATION_GUID, alias=config.STATION_ALIAS, ip=ip4, version=config.SYSTEM_VERSION)
            self.db.add(station)
            self.db.commit()
        else:
            alias = "%s (%s)" % (config.STATION_ALIAS, config.HARDWARE_GUID)
            version = "%s (%s)" % (config.SYSTEM_VERSION, config.SYSTEM_BUILD)
            if (station.alias != alias) or (station.ip != ip4) or (station.version != version):
                station.alias = alias
                station.ip = ip4
                station.version = version
                self.db.commit()
        _log.info("Ping from %s [ip: %s version: %s, station: %s]" % (
                station.alias, station.ip, station.version, station.guid))
        metadata = get_sync_metadata(self.db, config)
        metadata.last_ping = datetime.datetime.utcnow()
        self.db.commit()
        return True


    @transactional
    def is_zone_modified(self, config):
        metadata = self.db.query(SyncMetaData).filter(SyncMetaData.station_guid == config.STATION_GUID).first()
        if not metadata:
            return True
        else:
            return metadata.need_sync


    @transactional
    def sync_begin(self, config):
        metadata = get_sync_metadata(self.db, config)
        metadata.curr_sync = datetime.datetime.utcnow()
        self.db.commit()

        _log.info("Sync begin: %s:%s (last: %s, curr: %s)" % (metadata.zone.alias, metadata.station.alias, metadata.last_sync, metadata.curr_sync))

        return (metadata.last_sync, metadata.curr_sync)


    @transactional
    def sync_reset(self, config):
        metadata = self.db.query(SyncMetaData).filter(SyncMetaData.station_guid == config.STATION_GUID).first()
        if metadata:
            _log.info("Sync reset: %s:%s" % (metadata.zone.alias, metadata.station.alias))
            self.db.delete(metadata)
            self.db.commit()
        else:
            _log.info("No sync metadata for: zone:%s station:%s" % (config.ZONE_GUID, config.STATION_GUID))


    @transactional
    def sync_commit(self, config, num_client_changes):
        metadata = self.db.query(SyncMetaData).with_lockmode('update').filter(SyncMetaData.station_guid == config.STATION_GUID).one()

        vrs.db.schema.dump(self.db)
        _log.info("Sync commit: %s:%s %d changes (last: %s, curr: %s)" % (
                metadata.zone.alias, metadata.station.alias, num_client_changes,
                metadata.last_sync, metadata.curr_sync))

        metadata.last_sync = metadata.curr_sync
        metadata.need_sync = False
        self.db.commit()

        if num_client_changes > 0:
            _log.info("Client committed %d changes, marking zone:%s as dirty" % (num_client_changes, config.ZONE_GUID))
            self.db.query(SyncMetaData)\
                .with_lockmode('update')\
                .filter(SyncMetaData.zone_guid == config.ZONE_GUID)\
                .update({SyncMetaData.need_sync: True})
            self.db.commit()

        return True


    @transactional
    def get_server_changes(self, zone_guid, table_name, expected_modtime_range):
        table = vrs.db.utils.find_orm_class(table_name)
        assert table is not None
        selected = self.db.query(table)\
            .filter(table.modified >  expected_modtime_range[0])\
            .filter(table.modified <= expected_modtime_range[1])
        if hasattr(table, "zone_guid") and zone_guid != "*":
            z = self.db.query(Zone).filter(Zone.guid == zone_guid).one()
            selected = selected.join(Zone).filter(Zone.id == z.id)
        changes = {}
        for row in selected:
            changes[row.guid] = (row.revision, row.modified)
            _log.debug("Table '%s' row %s:%s changed %s" % (table_name, row.guid, row.revision, row.modified))
        return changes



    @transactional
    def download_server_record(self, table_name, guid, expected_revision):
        table = vrs.db.utils.find_orm_class(table_name)
        assert table is not None
        _log.info("Download %s:%s" % (table_name, guid))
        record = self.db.query(table).filter(table.guid == guid).filter(table.revision == expected_revision).first()
        if record:
            return vrs.db.utils.asdict(record)
        else:
            return None


    @transactional
    def filter_client_changes(self, table_name, client_changes):
        result = {}
        for (guid, (revision, modified)) in client_changes.iteritems():
            if self._need_upload_record(table_name, guid, revision, modified):
                result[guid] = (revision, modified)
        return result


    @transactional
    def upload_record_to_server(self, table_name, guid, client_record):
        table = vrs.db.utils.find_orm_class(table_name)
        assert table is not None
        _log.info("Upload %s:%s" % (table_name, guid))
        return self._update_server_record(table, guid, client_record)


    @transactional
    def upload_sessionlog(self, zone_guid, session_guid, xml):
        _log.debug("Recieved session log '%s' from zone: %s" % (session_guid, zone_guid))
        storage_dir = os.path.join(os.environ["CUREGAME_TEMPPATH"], self.config.S3_UPLOAD_DIR, 'session', zone_guid)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        if self.config.SESSION_SECRET:
            xml = crypto.encrypt(xml, password=self.config.SESSION_SECRET)
        filepath = os.path.join(storage_dir, session_guid + '.xml')
        with open(filepath, "wb") as f:
            f.write(xml)
        return vrs.db.sync.import_sessionlog(self.config, self.db, filepath, compressed=False)


    ################################
    # Helpers.
    ################################


    def _have_server_record(self, table, guid):
        return self.db.query(table).filter(table.guid == guid).first()


    def _insert_server_record(self, table, guid, client_record):
        assert self.db.query(table).filter(table.guid == guid).first() is None
        args, kwargs = [], client_record
        # Mark modified flag to force all clients re-sync this row.
        kwargs.update(modified=datetime.datetime.utcnow())
        self.db.add(table(*args, **kwargs))
        self.db.commit()


    def _need_upload_record(self, table_name, guid, revision, modified):
        table = vrs.db.utils.find_orm_class(table_name)
        assert table is not None
        if not self._have_server_record(table, guid):
            return True
        else:
            row = self.db.query(table).filter(table.guid == guid).first()
            if row.revision == revision and row.modified == modified:
                return False
            else:
                return (modified > row.modified)


    def _update_server_record(self, table, guid, client_record):
        if not self._have_server_record(table, guid):
            self._insert_server_record(table, guid, client_record)
            return True
        else:
            row = self.db.query(table).filter(table.guid == guid).first()

            # NOTE: client revision could be never than row if we are for example
            # re-uploading distributed data from client due to a database backup
            # restore.
            if row.revision <= client_record["revision"]:
                values = {}
                for (key,value) in client_record.iteritems():
                    assert key not in ["id"] and not key.endswith("_id")
                    column = table.metadata.tables[table.__tablename__].c[key]
                    values[column] = value
                try:
                    # A. Restoring revision to latest version from client
                    # B. Commit changed client data to a new revision
                    if row.revision < client_record["revision"]:
                        _log.info("Revert '%s':%s using client (mod: %s, rev: %s) onto server: (mod: %s, rev: %s)" % (
                                guid, table.__tablename__, client_record["modified"], client_record["revision"], row.modified, row.revision))
                        values[table.metadata.tables[table.__tablename__].c["revision"]] = client_record["revision"]
                    else:
                        _log.info("Commit '%s':%s using client (mod: %s, rev: %s) onto server: (mod: %s, rev: %s)" % (
                                guid, table.__tablename__, client_record["modified"], client_record["revision"], row.modified, row.revision))
                        values[table.metadata.tables[table.__tablename__].c["revision"]] = table.metadata.tables[table.__tablename__].c["revision"] + 1
                    # Mark modified flag to force all other clients re-sync this row
                    values[table.metadata.tables[table.__tablename__].c["modified"]] = datetime.datetime.utcnow()
                    n = self.db.query(table)\
                        .with_lockmode('update')\
                        .filter(table.guid == guid)\
                        .filter(table.revision <= client_record["revision"])\
                        .update(values)
                    self.db.commit()
                    return (n == 1)
                except (sa.orm.exc.NoResultFound):
                    return False
            else:
                _log.info("Skipping merge '%s':%s client (mod: %s, rev: %s) older than server: (mod: %s, rev: %s)" % (
                        guid, table.__tablename__, client_record["modified"], client_record["revision"], row.modified, row.revision))
                return True


###########################################################################
# The End.
###########################################################################
