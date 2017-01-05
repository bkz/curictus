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

import sqlalchemy as sa
import sqlalchemy.orm as orm

from sqlalchemy import Table, Column, ForeignKey, CheckConstraint
from sqlalchemy import Boolean, Integer, DateTime, String, Unicode, UnicodeText
from sqlalchemy.orm import deferred

from vrs.db import ActiveRecord, metadata
from vrs.db import has_one, has_many, computed_field
from vrs.db import PropertySpec, PropertyDict
from vrs.db import Enum, Bitfield
from vrs.db import UnicodeCompressedText

#############################################################################
# Utilities.
#############################################################################

def makeguid():
    return str(uuid.uuid4())


#############################################################################
# Test DB schema.
#############################################################################

UserKind = Enum('Customer', 'Support', 'Admin', 'Guest')

IssueStatus = Enum('Open', 'Closed')

IssueSeverity = Enum('Injury', 'NoInjury')

STATS_PROPERTY_TYPEMAP = {
    "b_key" : PropertySpec(bool, False),
    "s_key" : PropertySpec(str, "value"),
    "u_key" : PropertySpec(unicode, "value"),
    "i_key" : PropertySpec(long, 1),
    "f_key" : PropertySpec(float, -1),
}

bind_labels = Table("bind_labels", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_guid", String, ForeignKey('issues.guid'), nullable=False),
    Column("label_guid", String, ForeignKey('labels.guid'), nullable=False))

bind_comments = Table("bind_comments", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_guid", String, ForeignKey('issues.guid'), nullable=False),
    Column("comment_guid", String, ForeignKey('comments.guid'), nullable=False))

bind_users = Table("bind_users", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_guid", String, ForeignKey('issues.guid'), nullable=False),
    Column("user_guid", String, ForeignKey('users.guid'), nullable=False))


class Contact(ActiveRecord):
    __tablename__ = "contacts"
    guid          = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)
    phone         = Column(String, unique=True, nullable=False)


class Customer(ActiveRecord):
    __tablename__ = "customers"

    guid          = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)
    contact_guid  = Column(String, ForeignKey('contacts.guid'), nullable=False)

    name          = Column(UnicodeText, nullable=False)
    kind          = Column(String, CheckConstraint("kind in ('live', 'beta', 'stage')"), nullable=False)
    contact       = has_one(Contact)
    users         = has_many("User")


class User(ActiveRecord):
    __tablename__ = "users"

    guid          = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)
    customer_guid = Column(String, ForeignKey('customers.guid'), nullable=False)

    email         = Column(Unicode, nullable=False, index=True)
    kind          = Column(Bitfield(UserKind), nullable=False, default=UserKind.Customer)
    customer      = has_one(Customer)
    issues        = has_many("Issue", secondary=bind_users)


class Label(ActiveRecord):
    __tablename__ = "labels"

    guid          = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)
    title         = Column(String, nullable=False)
    users         = has_many("Issue", secondary=bind_labels)


class Comment(ActiveRecord):
    __tablename__ = "comments"

    guid        = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)
    created     = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    modified    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    revision    = Column(Integer, default=0, nullable=False)
    content     = Column(UnicodeCompressedText, nullable=False, default=u"")
    user_guid   = Column(String, ForeignKey('users.guid'), nullable=False)
    user        = has_one(User)


class Issue(ActiveRecord):
    __tablename__ = "issues"

    guid        = Column(String, primary_key=True, unique=True, nullable=False, index=True, default=makeguid)

    created     = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    modified    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    deleted     = Column(Boolean, default=False, nullable=False, index=True)
    description = Column(UnicodeCompressedText, nullable=False, default=u"")
    severity    = Column(Bitfield(IssueSeverity), nullable=False)
    status      = Column(Bitfield(IssueStatus), nullable=False, default=IssueStatus.Open)
    stats       = deferred(Column(PropertyDict(typemap=STATS_PROPERTY_TYPEMAP)))

    labels      = has_many("Label", secondary=bind_labels)
    comments    = has_many("Comment", secondary=bind_comments)
    users       = has_many("User", secondary=bind_users)

    c_year      = computed_field(int)
    c_week      = computed_field(int)
    c_weekday   = computed_field(int)

    m_year      = computed_field(int)
    m_week      = computed_field(int)
    m_weekday   = computed_field(int)

    @orm.reconstructor
    def _onload(self):
        (self.c_year, self.c_week, self.c_weekday) = self.created.isocalendar()
        (self.m_year, self.m_week, self.m_weekday) = self.modified.isocalendar()


#############################################################################
# Generate test data.
#############################################################################

LABELS = [
    "Bug",
    "Feature",
    "Critical",
    "VRS Hardware",
    "VRS Software",
    "PCMS",
    ]

CUSTOMERS = [
    (u"curictus.com", "111-111 111"),
    (u"netflix.com" , "222-222 222"),
    (u"mtv.com"     , "333-333 333"),
    ]

ADMIN_USERS = [
    u"babar.zafar@curictus.com",
    ]

SUPPORT_USERS = [
    u"babar.zafar@curictus.com",
    u"daniel.goude@curictus.com",
    u"mihaela.golic@curictus.com",
    ]

CUSTOMER_USERS = [
    u"john.rambo@netflix.com",
    u"rick.james@mtv.com",
    ]


def setupDB(db):
    for label in LABELS:
        l = db.query(Label).filter(Label.title == label).first()
        if not l:
            l = Label(title=label)
            db.add(l)
            db.commit()

    for (name, phone) in CUSTOMERS:
        p = db.query(Contact).filter(Contact.phone == phone).first()
        if not p:
            p = Contact(phone=phone)
            db.add(p)
            db.commit()
        c = db.query(Customer).filter(Customer.name == name).first()
        if not c:
            c = Customer(name=name, contact=p)
            db.add(c)
            db.commit()

    for email in ADMIN_USERS:
        s = db.query(User).filter(User.email == email).first()
        if not s:
            c = db.query(Customer).filter(Customer.name == email.split("@")[1]).one()
            s = User(email=email, kind=UserKind.Admin|UserKind.Support, customer=c)
            db.add(s)
            db.commit()

    for email in SUPPORT_USERS:
        s = db.query(User).filter(User.email == email).first()
        if not s:
            c = db.query(Customer).filter(Customer.name == email.split("@")[1]).one()
            s = User(email=email, kind=UserKind.Support, customer=c)
            db.add(s)
            db.commit()

    for email in CUSTOMER_USERS:
        s = db.query(User).filter(User.email == email).first()
        if not s:
            c = db.query(Customer).filter(Customer.name == email.split("@")[1]).one()
            s = User(email=email, kind=UserKind.Customer, customer=c)
            db.add(s)
            db.commit()


##############################################################################
# Test case.
##############################################################################

def runtest(db):
    for user in db.query(User):
        if (user.kind & UserKind.Admin):
            print user.email, "at", user.customer.name, "is an administrator"
        if (user.kind & UserKind.Support):
            print user.email, "at", user.customer.name, "is a member of the support staff"
        if (user.kind & UserKind.Customer):
            print user.email, "at", user.customer.name, "is a customer"


##############################################################################
# The End.
##############################################################################