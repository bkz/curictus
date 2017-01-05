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

from sqlalchemy import *

from vrs.db.migrate import \
    PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint, UniqueConstraint

# This script will update the server DB from 0.35 to the last schema, get rid
# of BLOB columns for storing raw session logs and the migration metadata table
# used by SQLAlchemy-migrate since we now use our own in-house solution.

def upgrade(engine, metadata):
    # ---
    # DROP TABLE migrate_version
    # ---

    migrate_version = Table('migrate_version', metadata, autoload=True, autoload_with=engine)

    migrate_version.drop()

    # ---
    # ALTER TABLE sessions
    # DELETE COLUMN
    #   Column(u'log_raw', BYTEA(length=None), nullable=False)
    # DELETE COLUMN
    #   Column(u'log_analyzed', BYTEA(length=None))
    # DELETE COLUMN
    #   Column(u'log_kinematics', BYTEA(length=None))
    # DELETE COLUMN
    #   Column(u'log_activity', BYTEA(length=None))
    # ---

    sessions = Table('sessions', metadata, autoload=True, autoload_with=engine)
    for colname in ['log_raw', 'log_activity', 'log_kinematics', 'log_analyzed']:
        sessions.c[colname].drop()
