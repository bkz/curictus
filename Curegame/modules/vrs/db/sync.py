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
import time

from vrs import SessionLog
from vrs.db.schema import Zone, Station, Activity, Patient, Session

_log = logging.getLogger('db')

###########################################################################
# Client/Server Sync API abstract interface.
###########################################################################

class SyncAPI(object):
    def ping(self, config, ip4):
        raise NotImplementedError

    def is_zone_modified(self, config):
        raise NotImplementedError

    def sync_begin(self, config):
        raise NotImplementedError

    def sync_reset(self, config):
        raise NotImplementedError

    def sync_commit(self, config, num_client_changes):
        raise NotImplementedError

    def get_server_changes(self, zone_guid, table_name, expected_modtime_range):
        raise NotImplementedError

    def download_server_record(self, table_name, guid, expected_revision):
        raise NotImplementedError

    def filter_client_changes(self, table_name, client_changes):
        raise NotImplementedError

    def upload_record_to_server(self, table_name, guid, client_record):
        raise NotImplementedError

    def upload_sessionlog(self, zone_guid, session_guid, xml):
        raise NotImplementedError


###########################################################################
# Shared syncing helpers.
###########################################################################

def make_pincode(alias):
    """
    Make a "temporary" pincode by padding (prefixing) 'alias' with zeroes with
    if ``alias`` is less than 4 characters long.
    """
    return ("%4s" % alias).replace(' ', '0')


def import_sessionlog(config, db, filepath, compressed=True):
    """
    Import and insert a single VRS session log ``filepath` to local DB,
    registering activities and patients if needed.

    Note: the raw XML is data is NOT imported, we still need to have the XML
    around if want to get the logged kinematics and activity data.

    If ``compressed`` is True we'll assume ``filepath`` is a .xml.gz otherwise
    we'll treat as a plain XML text file.

    Returns True/False to signal success/failure.
    """
    _log.info("Importing session log: %s" % filepath)

    try:
        sessionlog = SessionLog.load(filepath, password=config.SESSION_SECRET, zip=compressed)
    except IOError, e:
        _log.exception("Exception while loading session log %s" % filepath)
        return False

    if db.query(Session).filter(Session.guid == sessionlog.guid).first():
        _log.debug("Already imported session: %s" % sessionlog.guid)
        return True

    zone = db.query(Zone)\
        .filter(Zone.guid == sessionlog.zone_guid).first()
    if not zone:
        zone = Zone(guid=sessionlog.zone_guid, alias=sessionlog.zone_alias, email="", password="")
        db.add(zone)
        db.commit()

    station = db.query(Station)\
        .filter(Station.guid == sessionlog.station_guid).first()
    if not station:
        station = Station(guid=sessionlog.station_guid, alias=sessionlog.station_alias, ip="", version="", zone=zone)
        db.add(station)
        db.commit()

    activity = db.query(Activity).filter(Activity.guid == sessionlog.activity_guid).first()
    if not activity:
        _log.error("Unknown activity (%:%s) skipping import: %s" % (
                sessionlog.activity_alias, sessionlog.activity_guid, filepath))
        return False

    patient = db.query(Patient).filter(Patient.guid == sessionlog.patient_guid).first()
    if not patient:
        _log.debug("Insert patient: '%s' (%s)" % (sessionlog.patient_alias, sessionlog.patient_guid))
        # We'll temporary assign the newly created patient a pincode using
        # their alias since the pincode isn't serialized as part of the session
        # logs. The syncer will replace the pincode with the "real" one once it
        # has fetched the patient data from the master server. Note: This
        # scenario will only happen when we completely reset the local cache DB
        # and force an import of existing session logs.
        pincode = make_pincode(sessionlog.patient_alias)
        patient = Patient(guid=sessionlog.patient_guid, alias=sessionlog.patient_alias,
                          pincode=pincode, zone=zone)
        db.add(patient)
        db.commit()

    _log.debug("Importing session: %s %s %s %s" % (
            sessionlog.activity_alias, sessionlog.activity_kind,
            sessionlog.timestamp, sessionlog.guid))

    session = Session(guid=sessionlog.guid,
                      version_activity=sessionlog.activity_version,
                      version_system=sessionlog.version,
                      version_haptics=sessionlog.get_hardware_xml(),
                      timestamp=datetime.datetime.utcfromtimestamp(float(sessionlog.timestamp)),
                      duration=int(round(float(sessionlog.duration))),
                      score=sessionlog.score,
                      activity=activity,
                      patient=patient,
                      zone=zone,
                      station=station)
    db.add(session)
    db.commit()
    return True


###########################################################################
# Shared syncing helpers.
###########################################################################
