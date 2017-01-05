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

import uuid

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
# VRS client DB Schema.
#############################################################################

# ...

##############################################################################
# Database configuration (local and global).
#############################################################################

def setupDB(db, config):
    vrs.db.schema.setupDB(db, config)

    # Register our station and the zone we're associated with.
    z = db.query(Zone).filter(Zone.guid == config.ZONE_GUID).first()
    if not z:
        z = Zone(guid=config.ZONE_GUID, alias="", email="", password="")
        db.add(z)
        db.commit()
    s = db.query(Station).filter(Station.guid == config.STATION_GUID).first()
    if not s:
        s = Station(guid=config.STATION_GUID, alias=config.STATION_ALIAS, ip="", version=config.SYSTEM_VERSION, zone=z)
        db.add(s)
        db.commit()

    # NOTE: we'll re-use the zone guid as the unique indentifier for the guest
    # account to make sure we only have a single guest account per zone.
    g = db.query(Patient).filter(Patient.alias == "guest").first()
    if not g:
        g = Patient(guid=z.guid, alias="guest", pincode="guest", zone=z)
        db.add(g)
        db.commit()


##############################################################################
# The End.
#############################################################################
