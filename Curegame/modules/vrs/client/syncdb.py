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

import vrs.db.schema
import vrs.db.utils

from vrs.db.schema import Zone
from vrs.db.sync import SyncAPI

_log = logging.getLogger('vrs-syncdb')

###########################################################################
# Client <---> Server DB synchronization.
###########################################################################

_DATETIME_EPOCH = datetime.datetime.utcfromtimestamp(0)

def get_client_changes(zone_guid, db, table, expected_modtime_range):
    selected = db.query(table)\
        .filter(table.modified >  expected_modtime_range[0])\
        .filter(table.modified <= expected_modtime_range[1])
    if hasattr(table, "zone_guid") and zone_guid != "*":
        z = db.query(Zone).filter(Zone.guid == zone_guid).one()
        selected = selected.join(Zone).filter(Zone.id == z.id)
    changes = {}
    for row in selected:
        changes[row.guid] = (row.revision, row.modified)
    return changes


def have_client_record(db, table, guid):
    return db.query(table).filter(table.guid == guid).first()


def have_client_record_revision(db, table, guid, revision):
    return db.query(table)\
        .filter(table.guid == guid)\
        .filter(table.revision == revision)\
        .first()


def select_client_record(db, table, guid, revision, expected_modtime_range):
    record = db.query(table)\
        .filter(table.guid == guid)\
        .filter(table.revision == revision)\
        .filter(table.modified >  expected_modtime_range[0])\
        .filter(table.modified <= expected_modtime_range[1])\
        .first()
    if record:
        return vrs.db.utils.asdict(record)
    else:
        return None


def insert_client_record(db, table, guid, server_record):
    assert not have_client_record(db, table, guid)
    args, kwargs = [], server_record
    db.add(table(*args, **kwargs))
    db.commit()


def replace_client_record(db, table, guid, server_record, expected_modtime_range):
    values = {}
    for (key,value) in server_record.iteritems():
        column = table.metadata.tables[table.__tablename__].c[key]
        values[column] = value
    try:
        n = db.query(table)\
            .with_lockmode('update')\
            .filter(table.guid == guid)\
            .filter(table.modified >  expected_modtime_range[0])\
            .filter(table.modified <= expected_modtime_range[1])\
            .update(values)
        db.commit()
        return (n == 1)
    except (sa.orm.exc.NoResultFound):
        return False


def set_client_record_modtime(db, table, guid, revision, modified, expected_modtime_range):
    values = {table.modified:modified}
    n = db.query(table)\
        .with_lockmode('update')\
        .filter(table.guid == guid)\
        .filter(table.revision == revision)\
        .filter(table.modified >  expected_modtime_range[0])\
        .filter(table.modified <= expected_modtime_range[1])\
        .update(values)
    db.commit()
    return (n == 1)


def sync_client_with_server(rpc, zone_guid, db, table, last_sync, curr_sync):
    table_name = table.__tablename__

    all_client_changes = get_client_changes(zone_guid, db, table, expected_modtime_range=(last_sync, curr_sync))
    client_changes = rpc.invoke(SyncAPI.filter_client_changes, table_name, all_client_changes)

    if len(all_client_changes) > 0:
        _log.debug("Server filtered away %d/%d changes from %s" % (
                len(all_client_changes) - len(client_changes),
                len(all_client_changes),
                table_name))

    count = 0

    for (guid, (revision, modified)) in client_changes.iteritems():
        _log.debug("Client record changed: %s %s %s %s" % (table_name, guid, revision, modified))
        client_record = select_client_record(db, table, guid, revision, expected_modtime_range=(last_sync, curr_sync))
        if not client_record:
            _log.warning("Client record updated during sync, skipping upload")
        else:
            if not rpc.invoke(SyncAPI.upload_record_to_server, table_name, guid, client_record):
                _log.error("Failed to upload record to server")
            else:
                count += 1

    return count


def sync_server_with_client(rpc, zone_guid, db, table, last_sync, curr_sync):
    table_name = table.__tablename__

    server_changes = rpc.invoke(SyncAPI.get_server_changes, zone_guid, table_name, expected_modtime_range=(last_sync, curr_sync))

    count = 0

    for (guid, (revision, modified)) in server_changes.iteritems():
        _log.debug("Server record changed: %s %s %s %s" % (table_name, guid, revision, modified))
        if not have_client_record(db, table, guid):
            server_record = rpc.invoke(SyncAPI.download_server_record, table_name, guid, revision)
            if server_record:
                insert_client_record(db, table, guid, server_record)
                count += 1
            else:
                _log.warning("Server record revision not available (modified during sync), skipping insert")
        else:
            if have_client_record_revision(db, table, guid, revision):
                _log.info("Skipping download, client already has up-to-date revision (update timestamp)")
                if not set_client_record_modtime(db, table, guid, revision, modified, expected_modtime_range=(_DATETIME_EPOCH, curr_sync)):
                    _log.warning("Client record modified during sync, not updating timestamp")
            else:
                server_record = rpc.invoke(SyncAPI.download_server_record, table_name, guid, revision)
                if not server_record:
                    _log.warning("Server record updated during sync, skipping replace")
                else:
                    if not replace_client_record(db, table, guid, server_record, expected_modtime_range=(_DATETIME_EPOCH, curr_sync)):
                        _log.warning("Client record modified during sync, record not replaced with server revision")
                    else:
                        count += 1

    return count


###########################################################################
# Client DB sync public interface.
###########################################################################

def sync_tables(rpc, config, db, stopevent, client_tables=[], server_tables=[], allzones=False):
    (last_sync, curr_sync) = rpc.invoke(SyncAPI.sync_begin, config)

    _log.info("Sync begin: last: %s, curr: %s" % (last_sync, curr_sync))

    if allzones:
        sync_client_with_server(rpc, "*", db, Zone, last_sync, curr_sync)
        sync_server_with_client(rpc, "*", db, Zone, last_sync, curr_sync)
        zone_guids = [row.guid for row in db.query(Zone)]
    else:
        zone_guids = [config.ZONE_GUID]

    num_client_changes = 0
    num_server_changes = 0

    for zone_guid in zone_guids:
        for table in client_tables:
            if stopevent.isSet(): return -1
            _log.info("Syncing table '%s' from client" % table.__tablename__)
            num_client_changes += sync_client_with_server(rpc, zone_guid, db, table, last_sync, curr_sync)
        for table in server_tables:
            if stopevent.isSet(): return -1
            _log.info("Syncing table '%s' from server" % table.__tablename__)
            num_server_changes += sync_server_with_client(rpc, zone_guid, db, table, last_sync, curr_sync)

    assert rpc.invoke(SyncAPI.sync_commit, config, num_client_changes)

    total_changes = num_client_changes + num_server_changes

    vrs.db.schema.dump(db)

    _log.info("Sync commit: local:%d - remote:%d - total:%d"  % (num_client_changes, num_server_changes, total_changes))

    return total_changes


###########################################################################
# The End.
###########################################################################
