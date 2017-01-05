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
import itertools

import sqlalchemy as sa
import sqlalchemy.orm as orm

from sqlalchemy import Table, Column, ForeignKey, CheckConstraint
from sqlalchemy import Boolean, Integer, DateTime, PickleType, String, UnicodeText
from sqlalchemy.orm import deferred

from vrs.config import activities

from vrs.db import metadata, ActiveRecord
from vrs.db import has_one, has_many, computed_field, computed_array
from vrs.db import UnicodeCompressedText, PropertySpec, PropertyDict

_log = logging.getLogger('db-shared')

#############################################################################
# Shared DB Schema (client/server).
#############################################################################

##############################
# Zone.
##############################

class Zone(ActiveRecord):
    """
    Zone Table
    """
    __tablename__ = "zones"
    __amf_class__ = "vrs.shared.Zone"

    id       = Column(Integer, primary_key=True)
    guid     = Column(String, unique=True, nullable=False, index=True)

    modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision = Column(Integer, default=0, nullable=False)

    alias    = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email    = Column(String, nullable=False)

    @classmethod
    def __serialize__(cls):
        return [Zone.id, Zone.guid, Zone.alias, Zone.email]


##############################
# Station.
##############################

class Station(ActiveRecord):
    """
    Station Table
    """
    __tablename__ = "stations"
    __amf_class__ = "vrs.shared.Station"

    id        = Column(Integer, primary_key=True)
    zone_guid = Column(String, ForeignKey('zones.guid'), nullable=False)
    guid      = Column(String, unique=True, nullable=False, index=True)

    modified  = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision  = Column(Integer, default=0, nullable=False)

    alias     = Column(String, unique=True, nullable=False)
    ip        = Column(String, nullable=False)
    version   = Column(String, nullable=False)

    zone      = has_one(Zone)

    @classmethod
    def __serialize__(cls):
        return [Station.id, Station.guid, Station.alias, Station.ip, Station.version]


class Activity(ActiveRecord):
    """
    Activity Table
    """
    __tablename__ = "activities"
    __amf_class__ = "vrs.shared.Activity"

    id       = Column(Integer, primary_key=True)
    guid     = Column(String, unique=True, nullable=False, index=True)

    modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision = Column(Integer, default=0, nullable=False)

    alias    = Column(String, unique=True, nullable=False)
    kind     = Column(String, CheckConstraint("kind in ('game', 'test')"), nullable=False)
    version  = Column(String, nullable=False)

    sessions = has_many("Session", primaryjoin="Activity.guid==Session.activity_guid")


    @classmethod
    def __serialize__(cls):
        return [Activity.id, Activity.guid, Activity.alias, Activity.kind, Activity.version]


##############################
# Patient.
##############################

MEDICAL_RECORD_PROPERTY_TYPEMAP = {
    "birthdate"                : PropertySpec(str, ""),
    "disease_date"             : PropertySpec(str, ""),
    "gender"                   : PropertySpec(str, "unspecified", allowed=["male", "female", "unspecified"]),
    "first_session_date"       : PropertySpec(datetime.datetime, datetime.datetime.utcnow()),
    "latest_session_date"      : PropertySpec(datetime.datetime, datetime.datetime.utcnow()),
    "assessment_session_count" : PropertySpec(int, 0),
    "training_session_count"   : PropertySpec(int, 0),
    "total_session_count"      : PropertySpec(int, 0),
    "diagnosis"                : PropertySpec(str, ""),
    "symptoms"                 : PropertySpec(str, ""),
    "notes"                    : PropertySpec(str, ""),
}

SETTINGS_GAME_PROPERTY_TYPEMAP = {
    "archery2_level"    : PropertySpec(int, activities.get_default_level("archery2"), allowed=activities.get_level_xrange("archery2")),
    "bandit_level"      : PropertySpec(int, activities.get_default_level("bandit"), allowed=activities.get_level_xrange("bandit")),
    "bingo2_level"      : PropertySpec(int, activities.get_default_level("bingo2"), allowed=activities.get_level_xrange("bingo2")),
    "codebreak_level"   : PropertySpec(int, activities.get_default_level("codebreak"), allowed=activities.get_level_xrange("codebreak")),
    "colors_level"      : PropertySpec(int, activities.get_default_level("colors"), allowed=activities.get_level_xrange("colors")),
    "fishtank2_level"   : PropertySpec(int, activities.get_default_level("fishtank2"), allowed=activities.get_level_xrange("fishtank2")),
    "math2_level"       : PropertySpec(int, activities.get_default_level("math2"), allowed=activities.get_level_xrange("math2")),
    "memory_level"      : PropertySpec(int, activities.get_default_level("memory"), allowed=activities.get_level_xrange("memory")),
    "pong_level"        : PropertySpec(int, activities.get_default_level("pong"), allowed=activities.get_level_xrange("pong")),
    "racer_level"       : PropertySpec(int, activities.get_default_level("racer"), allowed=activities.get_level_xrange("racer")),
    "simon2_level"      : PropertySpec(int, activities.get_default_level("simon2"), allowed=activities.get_level_xrange("simon2")),
}

class Patient(ActiveRecord):
    """
    Patient Table
    """
    __tablename__ = "patients"
    __amf_class__ = "vrs.shared.Patient"

    id              = Column(Integer, primary_key=True)
    zone_guid       = Column(String, ForeignKey('zones.guid'), nullable=False)
    guid            = Column(String, unique=True, nullable=False, index=True)

    active          = Column(Boolean, default=True, nullable=False)
    modified        = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision        = Column(Integer, default=0, nullable=False)


    alias           = Column(String, nullable=False, index=True)
    pincode         = Column(String, nullable=False, index=True)

    medical_record  = deferred(Column(PropertyDict(typemap=MEDICAL_RECORD_PROPERTY_TYPEMAP)))
    settings_game   = deferred(Column(PropertyDict(typemap=SETTINGS_GAME_PROPERTY_TYPEMAP)))
    settings_system = deferred(Column(PropertyDict))

    zone            = has_one(Zone)
    sessions        = has_many("Session", primaryjoin="Patient.guid==Session.patient_guid")

    @classmethod
    def __serialize__(cls):
        return [Patient.id, Patient.guid,
                Patient.alias, Patient.pincode,
                Patient.active, Patient.medical_record]


##############################
# Session.
##############################

SCORE_PROPERTY_TYPEMAP = {
    "level"          : PropertySpec(int, 0),
    "score"          : PropertySpec(int, 0),
    "left_score"     : PropertySpec(int, 0),
    "right_score"    : PropertySpec(int, 0),
    "player_score"   : PropertySpec(int, 0),
    "opponent_score" : PropertySpec(int, 0),
    "moves"          : PropertySpec(int, 0),
    "mistakes"       : PropertySpec(int, 0),
    "duration"       : PropertySpec(float, 0.0),
    "perfect"        : PropertySpec(bool, False),
    "win"            : PropertySpec(bool, False),
}

class Session(ActiveRecord):
    """
    Session Table
    """
    __tablename__ = "sessions"
    __amf_class__ = "vrs.shared.Session"

    id               = Column(Integer, primary_key=True)
    zone_guid        = Column(String, ForeignKey('zones.guid'), nullable=False)
    station_guid     = Column(String, ForeignKey('stations.guid'), nullable=False)
    activity_guid    = Column(String, ForeignKey('activities.guid'), nullable=False)
    patient_guid     = Column(String, ForeignKey('patients.guid'), nullable=False)
    guid             = Column(String, unique=True, nullable=False, index=True)

    modified         = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision         = Column(Integer, default=0, nullable=False)

    version_activity = Column(String, nullable=False)
    version_system   = Column(String, nullable=False)
    version_haptics  = Column(String, nullable=False)

    timestamp        = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    duration         = Column(Integer, nullable=False)
    score            = deferred(Column(PropertyDict(typemap=SCORE_PROPERTY_TYPEMAP)))

    is_processed     = Column(Boolean, default=False, nullable=False, index=True)
    is_valid         = Column(Boolean, default=False, nullable=False, index=True)

    zone             = has_one(Zone)
    station          = has_one(Station)
    activity         = has_one(Activity)
    patient          = has_one(Patient)

    year             = computed_field(int)
    week             = computed_field(int)
    weekday          = computed_field(int)

    @orm.reconstructor
    def _onload(self):
        (self.year, self.week, self.weekday) = self.timestamp.isocalendar()

    @classmethod
    def __serialize__(cls):
        return [Session.id, Session.guid,
                Session.timestamp, Session.duration, Session.score,
                Session.year, Session.week, Session.weekday,
                Session.zone, Session.activity, Session.patient]


##############################################################################
# Global database configuration.
#############################################################################

def register_activity(db, alias, guid, kind, version):
    activity = db.query(Activity).filter(Activity.guid == guid).first()
    if not activity:
        activity = Activity(guid=guid, alias=alias, kind=kind, version=version)
        db.add(activity)
        db.commit()
    else:
        # Don't rename unless needed (all changes result in syncing).
        if activity.alias != alias:
            activity.alias = alias
            db.commit()


def setupDB(db, config):
    # Register deleted versions of activities so that we can import and sync
    # older sessions. Since we treat alises as a kind UUID we'll silentely
    # rename deprecated activities if there are any naming clashes. To
    # reference these 'older' activities you'll have use their GUIDs instead.
    taken_aliases = set(
        activities.HGT_TESTS.keys() +
        activities.HGT_GAMES.keys() )
    entries = itertools.chain(
        activities.DELETED_HGT_TESTS.iteritems(),
        activities.DELETED_HGT_GAMES.iteritems(),
        activities.DELETED_LEGACY_GAMES.iteritems())
    for (alias, (path, x3d, version, kind, guid)) in entries:
        if alias in taken_aliases:
            alias = "%s_deleted_%s" % (alias, guid)
        register_activity(db, alias, guid, kind, version)

    # Internalize latest versions of all available activities and make sure
    # aliases are correctly setup in case of renaming etc.
    entries = itertools.chain(
        activities.HGT_TESTS.iteritems(),
        activities.HGT_GAMES.iteritems())
    for (alias, (path, x3d, version, kind, guid)) in entries:
        register_activity(db, alias, guid, kind, version)


##############################################################################
# Debugging utilities.
#############################################################################

def dump(db, full=False):
    if full:
        for row in db.query(Zone):
            _log.debug("  zone     -> %s %s %s %s" % (row.guid, row.revision, row.modified, row.alias))
        for row in db.query(Station):
            _log.debug("  station  -> %s %s %s %s" % (row.guid, row.revision, row.modified, row.alias))
        for row in db.query(Activity):
            _log.debug("  activity -> %s %s %s %s" % (row.guid, row.revision, row.modified, row.alias))
        for row in db.query(Patient):
            _log.debug("  patient  -> %s %s %s %s" % (row.guid, row.revision, row.modified, row.alias))
        for row in db.query(Session):
            _log.debug("  session  -> %s %s %s"    % (row.guid, row.revision, row.modified))

    stats = " ".join(["%s:%s" % (table.__tablename__, db.query(table).count())
                      for table in [Zone, Station, Activity, Patient, Session]])

    _log.debug("DB dump: %s" % stats)


##############################################################################
# The End.
#############################################################################
