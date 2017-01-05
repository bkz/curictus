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
import itertools

import sqlalchemy as sa
import sqlalchemy.orm as orm

from sqlalchemy import Table, Column, ForeignKey, CheckConstraint
from sqlalchemy import Boolean, Integer, DateTime, String, UnicodeText
from sqlalchemy.orm import deferred

import vrs.db

from vrs.db import ActiveRecord
from vrs.db import metadata
from vrs.db import has_one, has_many, computed_field, computed_array

##############################################################################
# VRS shared DB schema.
#############################################################################

from vrs.db.schema import Zone, Station, Activity, Patient, Session

##############################################################################
# VRS server DB schema.
#############################################################################

class SyncMetaData(ActiveRecord):
    __tablename__ = "syncmetadata"

    id           = Column(Integer, primary_key=True)

    zone_guid    = Column(String, ForeignKey('zones.guid'), nullable=False)
    station_guid = Column(String, ForeignKey('stations.guid'), nullable=False)

    last_ping    = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    curr_sync    = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_sync    = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    need_sync    = Column(Boolean, default=False, nullable=False)

    zone         = has_one(Zone)
    station      = has_one(Station)


##############################################################################
# Database configuration (local and global).
#############################################################################

def setupDB(db, config):
    vrs.db.schema.setupDB(db, config)

    # Register customer zones and passwords.
    for (guid, (alias, password, hostname)) in config.CUSTOMER_ZONES.iteritems():
        z = db.query(Zone).filter(Zone.guid == guid).first()
        if not z:
            z = Zone(guid=guid, alias=alias, email="", password=password)
            db.add(z)
            db.commit()
        else:
            z.alias = alias
            db.commit()


##############################################################################
# The End.
#############################################################################
