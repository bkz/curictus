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
import uuid

from sqlalchemy import *
from migrate.changeset import *
from migrate.changeset.constraint import PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint, UniqueConstraint

def makeguid():
    return str(uuid.uuid4())


CUSTOMERS = [
    (u"curictus.com", "111-111 111"),
    (u"netflix.com" , "222-222 222"),
    (u"mtv.com"     , "333-333 333"),
]

def fixpk(table):
    PrimaryKeyConstraint(table.c.id).drop(cascade=True)
    table.c.id.drop()

    table.c.guid.alter(type=String, primary_key=True, index=True, unique=True, nullable=False, default=makeguid)
    PrimaryKeyConstraint(table.c.guid).create()


def upgrade(conn, metadata):
    # ---
    # DROP TABLE stats
    # ---

    stats = Table('stats', metadata, autoload=True, autoload_with=conn)

    stats.drop()

    # ---
    # ALTER TABLE issues
    # ALTER COLUMN
    #   Column(u'guid', VARCHAR(), nullable=False)
    #   Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>)
    # DELETE COLUMN
    #   Column(u'id', INTEGER(), primary_key=True, nullable=False)
    # ---

    issues = Table('issues', metadata, autoload=True, autoload_with=conn)

    fixpk(issues)

    # ---
    # CREATE TABLE contacts
    # ---

    contacts = Table('contacts', metadata,
        Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=makeguid),
        Column('phone', String(), unique=True, nullable=False),
        )

    contacts.drop()
    contacts.create()

    for (name, phone) in CUSTOMERS:
        conn.execute(contacts.insert(), phone=phone)

    # ---
    # ALTER TABLE labels
    # ALTER COLUMN
    #   Column(u'guid', VARCHAR(), nullable=False)
    #   Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>)
    # DELETE COLUMN
    #   Column(u'id', INTEGER(), primary_key=True, nullable=False)
    # ---

    labels = Table('labels', metadata, autoload=True, autoload_with=conn)

    fixpk(labels)

    # ---
    # ALTER TABLE customers
    # ADD COLUMN
    #   Column('contact_guid', String(), nullable=False)
    # ADD COLUMN
    #   Column('kind', String(), CheckConstraint("kind in ('live', 'beta', 'stage')"), nullable=False)
    # ALTER COLUMN
    #   Column(u'guid', VARCHAR(), nullable=False)
    #   Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>)
    # ALTER COLUMN
    #   Column(u'name', VARCHAR(), nullable=False)
    #   Column('name', UnicodeText(), nullable=False)
    # DELETE COLUMN
    #   Column(u'id', INTEGER(), primary_key=True, nullable=False)
    # ---

    customers = Table('customers', metadata, autoload=True, autoload_with=conn)

    fixpk(customers)

    c = Column('kind', String(), CheckConstraint("kind in ('live', 'beta', 'stage')"), default="live", nullable=False)
    c.create(customer, populate_default=True)

    c = Column('kind', String(), CheckConstraint("kind in ('live', 'beta', 'stage')"), default="live", nullable=False)
    c.create(customer, populate_default=True)

    for (name, phone) in CUSTOMERS:
        c = conn.execute(select([contacts], contacts.c.phone==phone)).fetchone()
        conn.execute(customers.update().where(customers.c.name == name).values(phone=phone))

    # for (name, phone) in CUSTOMERS:
    #     conn.execute(customers.update().where(
    #     if name == row["name"]:
    #         c = conn.execute(select([contacts], contacts.c.phone==phone)).fetchone()
    #         row["contact_guid"] = c.guid

    #      row["name"] = unicode(row["name"])
    #      row["kind"] = "live"
    #      del row["id"]

    # ---
    # ALTER TABLE users
    # ALTER COLUMN
    #   Column(u'guid', VARCHAR(), nullable=False)
    #   Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>)
    # ALTER COLUMN
    #   Column(u'email', VARCHAR(), nullable=False)
    #   Column('email', Unicode(), index=True, nullable=False)
    # DELETE COLUMN
    #   Column(u'id', INTEGER(), primary_key=True, nullable=False)
    # ---

    users = Table('users', metadata, autoload=True, autoload_with=conn)

    users.c.email.alter(type=Unicode, index=True, nullable=False)

    fixpk(users)


    # ---
    # ALTER TABLE comments
    # ADD COLUMN
    #   Column('revision', Integer(), nullable=False, default=0)
    # ADD COLUMN
    #   Column('content', UnicodeCompressedText(), nullable=False, default=u'')
    # ALTER COLUMN
    #   Column(u'guid', VARCHAR(), nullable=False)
    #   Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>)
    # DELETE COLUMN
    #   Column(u'text', BYTEA(length=None), nullable=False)
    # DELETE COLUMN
    #   Column(u'id', INTEGER(), primary_key=True, nullable=False)
    # ---

    comments = Table('comments', metadata, autoload=True, autoload_with=conn)

    fixpk(comments)
