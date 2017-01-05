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
from sqlalchemy import Boolean, Integer, DateTime, String, UnicodeText
from sqlalchemy.orm import deferred

##############################################################################
# SQLAlchemy ORM declarative configuration.
##############################################################################

from sqlalchemy.ext.declarative import declarative_base

metadata = sa.MetaData()

ActiveRecord = declarative_base(metadata=metadata)

engine = None

session = None

##############################################################################
# DB commit hook support.
##############################################################################

_commit_hooks = []

def register_commit_hook(fn):
    """
    Register function/method ``fn`` to be called when ever we commit to the
    database (i.e track insert/update/delete).
    """
    assert callable(fn)
    if fn not in _commit_hooks:
        _commit_hooks.append(fn)

        
class CommitHook(orm.interfaces.SessionExtension):
    """
    Helper class which is used to extend a SQLAlchemy session to allow us to
    recieve notification on various DB events.
    """
    def after_commit(self, session):        
        for fn in _commit_hooks: fn()

            
##############################################################################
# Setup global connection.
##############################################################################

# SQLlite has pretty good concurrent read support but lacks somewhat when it
# comes to multiple threads/processes trying to write to the DB. SQLAlchemy by
# defaults uses queue-style connection pooling which easily causes
# OperationError(database is locked) exception when we have multiple
# writers.
#
# To deal with this we simply disable pooling altogether (since connecting to a
# SQLite DB is basically fopen()) and instead increase the timeout limit. This
# will cause starved writers to hopefully wait long enough that the other
# finish their writes.
#
# If you have a thread/process which wants to write a lot of data you are
# recomended to write the data in small batches and interleve the writes with
# calls to sleep() in order to let others write to the DB as well.

def connect_sqlite(filename, debug=False):
    global engine, session
    engine = sa.create_engine("sqlite:///%s" % filename, echo=debug, poolclass=sa.pool.NullPool, connect_args={'timeout':60})
    metadata.create_all(engine)
    session = orm.scoped_session(orm.sessionmaker(bind=engine, extension=CommitHook()))
    return session()

def connect_postgres(name, user, passwd, port=5432, debug=False):
    global engine, session
    engine = sa.create_engine("postgresql+psycopg2://%s:%s@localhost:%s/%s" % (user, passwd, port, name), echo=debug)
    metadata.create_all(engine)
    session = orm.scoped_session(orm.sessionmaker(bind=engine, extension=CommitHook()))
    return session()


##############################################################################
# ORM metadata (mapping) helpers.
##############################################################################

def has_one(*args, **kwargs):
    """
    Dummy wrapper for ``orm.relation`` which is used to document that the
    result of evaluating a relationship results in a scalar value, i.e. a we
    are referencing another table via a ``ForeignKey``.
    """
    kwargs['uselist'] = False
    return orm.relation(*args, **kwargs)


def has_many(*args, **kwargs):
    """
    Dummy wrapper for ``orm.relation`` which is used to document that the
    result of evaluating a relationship results in a list of values, i.e. a we
    are filtering another table with keys which point to us.
    """
    return orm.relation(*args, **kwargs)


##############################################################################
# Runtime computed metadata (mapping) helpers.
#############################################################################

class computed_field(object):
    """
    Metadata for scalar value of a static type.
    """
    def __init__(self, field_type=None):
        self.field_type = field_type

class computed_array(object):
    """
    Metadata for array fields.
    """
    def __init__(self, field_type=None):
        self.field_type = field_type

        
###########################################################################
# Transactional decorator.
###########################################################################

def transactional(fn):
    """
    Add transactional semantics to a method. Expect that the class instance has
    an instance variable ``self.db`` which is sqlalchemy ScopedSession instance
    (normally created via the orm.scoped_session() helper). Note: we support
    recursive call between methods which have decorated by only initiaing and
    releasing the transaction at the toplevel method.
    """
    def transact(self, *args, **kwargs):
        _cleanup_session = False
        if not hasattr(self, '_transaction_lock'):
            self._transaction_lock = True
            _cleanup_session = True
        try:
            return fn(self, *args, **kwargs)
        except:
            if _cleanup_session:
                self.db.rollback()
            raise
        finally:
            if _cleanup_session:
                delattr(self, '_transaction_lock')
                self.db.close()
    transact.__name__ = fn.__name__
    return transact


#############################################################################
# DB Schema
#############################################################################

import random
import string

def genguid():
    return str(uuid.uuid4())

def randpasswd():
    return "".join([random.choice(string.letters+string.digits) for x in range(32)])


class UserKind(object):
    CUSTOMER = 0
    SUPPORT  = 1

    
class IssueStatus(object):
    OPEN   = 0
    CLOSED = 1


class IssueSeverity(object):
    INJURY    = 0
    NO_INJURY = 2
    

bind_labels = Table("bind_labels", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_id", Integer, ForeignKey('issues.id'), nullable=False),
    Column("label_id", Integer, ForeignKey('labels.id'), nullable=False))

bind_comments = Table("bind_comments", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_id", Integer, ForeignKey('issues.id'), nullable=False),
    Column("comment_id", Integer, ForeignKey('comments.id'), nullable=False))

bind_users = Table("bind_users", ActiveRecord.metadata,
    Column("id", Integer, primary_key=True),
    Column("issue_id", Integer, ForeignKey('issues.id'), nullable=False),
    Column("user_id", Integer, ForeignKey('users.id'), nullable=False))


class User(ActiveRecord):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    guid          = Column(String, unique=True, nullable=False, index=True, default=genguid)
    email         = Column(String, unique=True, nullable=False, index=True)
    password      = Column(String, nullable=False, default=randpasswd)
    kind          = Column(Integer, nullable=False, default=UserKind.CUSTOMER)
    issues        = has_many("Issue", secondary=bind_users)


class Label(ActiveRecord):
    __tablename__ = "labels"

    id            = Column(Integer, primary_key=True)
    guid          = Column(String, unique=True, nullable=False, index=True, default=genguid)
    title         = Column(String, nullable=False)
    users         = has_many("Issue", secondary=bind_labels)


class Comment(ActiveRecord):
    __tablename__ = "comments"
    
    id          = Column(Integer, primary_key=True)
    guid        = Column(String, unique=True, nullable=False, index=True, default=genguid)
    created     = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    modified    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    text        = Column(UnicodeText, nullable=False, default=u"")
    user_id     = Column(Integer, ForeignKey('users.id'), nullable=False)
    user        = has_one(User)

    
class Issue(ActiveRecord):
    __tablename__ = "issues"

    id          = Column(Integer, primary_key=True)
    guid        = Column(String, unique=True, nullable=False, index=True, default=genguid)
    created     = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    modified    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    description = Column(UnicodeText, nullable=False, default=u"")
    severity    = Column(Integer, nullable=False)
    status      = Column(Integer, nullable=False, default=IssueStatus.OPEN)
    labels      = has_many("Label", secondary=bind_labels)
    comments    = has_many("Comment", secondary=bind_comments)
    users       = has_many("User", secondary=bind_users)


#############################################################################
# The End.
#############################################################################
