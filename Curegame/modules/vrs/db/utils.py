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

import gc, inspect
import functools

from sqlalchemy.orm import class_mapper

import vrs.db

###########################################################################
# SQLAlchemy utilities.
###########################################################################

_orm_class_cache = {}

def find_orm_class(table_name):
    """
    Return Python class which has been mapped using the SQLAlchemy ORM for
    ``table_name`` or None if no class is found.
    """
    try:
        return _orm_class_cache[table_name]
    except KeyError:
        _orm_class_cache[table_name] = None
        if table_name in vrs.db.metadata.tables:
            for klass in [x for x in gc.get_objects() if inspect.isclass(x)]:
                if hasattr(klass, '__tablename__') and klass.__tablename__ == table_name:
                    _orm_class_cache[table_name] = klass
                    break
        return _orm_class_cache[table_name]


def asdict(row):
    """
    Map SQLAlchemy queryset ``row`` as a dict (column name -> value) while
    exluding all id:s (primary keys and foreign keys which use the standard
    'id' and '*_id' convention).
    """
    return dict((col.name, getattr(row, col.name))
                for col in class_mapper(row.__class__).mapped_table.c
                if not (col.name  == "id"  or col.name.endswith("_id")))


###########################################################################
# Transactional decorator.
###########################################################################

def transactional(fn):
    """
    Add transactional semantics to a method. Expect that the class instance has
    an instance variable ``self.db`` which is sqlalchemy ScopedSession instance
    (normally created via the orm.scoped_session() helper). When a new
    transaction is started we forcefully expire any existing objects bound to
    the Session to make sure we always get a fresh view of the DB. On unhandled
    exception we'll rollback the transaction automatically to reset the DB
    state.

    Note: we support recursive call between methods which have decorated by
    only initiaing and releasing the transaction at the toplevel method.
    """
    @functools.wraps(fn)
    def transact(self, *args, **kwargs):
        _cleanup_session = False
        if not hasattr(self, '_transaction_lock'):
            self._transaction_lock = True
            # SQAlchemy maintains an identity map for objects which have
            # previously been queried from the DB and uses it as a kind of
            # cache. In order to support multiple Python processes talking to
            # the same DB we basically force SQLAlchemy to expire objects in
            # the cache and re-fetch their attributes (i.e. row values) from
            # the DB. Doing this makes sure that the connected client always
            # serves data which is up-to-date.
            self.db.expire_all()
            _cleanup_session = True
        try:
            return fn(self, *args, **kwargs)
        except:
            if _cleanup_session:
                # SQLAlchemy `expunging` basically means that we'll forcefully
                # reset the indentity map and invalidate and any loaded objects
                # from the DB to make sure we don't go forward with the query.
                self.db.expunge_all()
                self.db.rollback()
            raise
        finally:
            if _cleanup_session:
                delattr(self, '_transaction_lock')
    # Update wrapper with private attributes (i.e. ones starting with a single
    # underscore). We mainly do this to be able to use the transaction wrapper
    # with AS3RPC code generation decorators.
    for attr in [attr for attr in dir(fn) if attr[:1] == "_" and attr[:2] != "__"]:
        setattr(transact, attr, getattr(fn, attr))
    return transact


###########################################################################
# The End.
###########################################################################
