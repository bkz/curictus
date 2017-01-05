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

##############################################################################
# SQLAlchemy ORM declarative configuration.
##############################################################################

import sqlalchemy as sa
import sqlalchemy.orm as orm

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

def make_sqlite_url(filename):
    return "sqlite:///%s" % filename


def make_postgres_url(name, user, passwd, port=5432):
    return "postgresql+psycopg2://%s:%s@localhost:%s/%s" % (user, passwd, port, name)


def connect_sqlite(filename, debug=False):
    global engine, session
    engine = sa.create_engine(make_sqlite_url(filename), echo=debug, poolclass=sa.pool.NullPool, connect_args={'timeout':60})
    metadata.create_all(engine)
    session = orm.scoped_session(orm.sessionmaker(bind=engine, extension=CommitHook()))
    return session


def connect_postgres(name, user, passwd, port=5432, debug=False):
    global engine, session
    engine = sa.create_engine(make_postgres_url(name, user, passwd, port), echo=debug)
    metadata.create_all(engine)
    session = orm.scoped_session(orm.sessionmaker(bind=engine, extension=CommitHook()))
    return session


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


#############################################################################
# PropertySpec.
#############################################################################

class PropertySpec(object):
    """
    Helper class use to declare type information and default value for
    PropertyDict keys.

    Examples:

      PropertySpec(int, 0)
      PropertySpec(int, 0, [0,1,2])
      PropertySpec(str, "unspecified", allowed=["male", "female", "unspecified"])
      PropertySpec(datetime.datetime, datetime.datetime.utcnow())

    """

    def __init__(self, valtype, defvalue, allowed=[]):
        """
        Declare a field of ``valtype`` with a `defvalue``. Optionally specify a
        value validator in the form of ``allowed`` which supports lookups using
        'in' operator (i.e. lists/tupes or classes with special methods).
        """
        self.valtype, self.defvalue, self.allowed = valtype, defvalue, allowed
        if self.allowed:
            assert self.defvalue in self.allowed


    def filter(self, value):
        """
        Returns validated and transformed ``value``, converting it to the
        appropriate type or reverting it to the default value if required.
        """
        try:
            if type(value) is not self.valtype:
                if type(value) in [str, unicode] and self.valtype is bool:
                    value = value.strip().lower() in ["yes", "true", "1", "ok"]
                elif type(value) in [str, unicode] and self.valtype in [str, unicode]:
                    value = unicode(value)
                else:
                    value = self.valtype(value)
            if self.allowed and value not in self.allowed:
                return self.defvalue
            else:
                return value
        except ValueError:
            return self.defvalue


    def __repr__(self):
        if self.allowed:
            return "PropertySpec(%s, %s, %s)" % (self.valtype.__name__, repr(self.defvalue), repr(self.allowed))
        else:
            return "PropertySpec(%s, %s)" % (self.valtype.__name__, repr(self.defvalue))


#############################################################################
# PropertyDict (custom upgradeable dict column type).
#############################################################################

class PropertyDict(sa.types.TypeDecorator):
    """
    Custom SQLAlchemy database type for serializing (pickeling) a strongly
    typed dictionary with a dynamic 'schema' which automatically
    upgrades/validates data as it is read from and written to the DB.

    Example:

      # Simple schema for a medical record type.
      MEDICAL_RECORD_TYPEMAP = {
        "gender"    : PropertySpec(str, "unspecified", allowed=["male", "female", "unspecified"]),
        "timestamp" : PropertySpec(datetime.datetime, datetime.datetime.utcnow())
        }

      # Dynamically upgrade corrupt dates (perhaps due to a bug?).
      def upgrade(old, new):
          if old["timestamp"] < datetime.datetime(2000, 1, 1):
              new["timestamp"] = datetime.datetime(2000, 1, 1);


      # SQLAlchemy ORM column declaration.
      medical_record  = Column(PropertyDict(typemap=MEDICAL_RECORD_TYPEMAP)))

    """
    impl = sa.types.PickleType


    def __init__(self, typemap=None, upgrade_func=None, **kwargs):
        """
        Setup property specfication using ``typemap`` dict which maps key names
        to PropertySpec() instances. Optionally provide a ``upgrade_func`` with
        the signature(old, new) which perform and in-place mutation of the
        upgraded 'new' version of the dict if needed.
        """
        self.typemap, self.upgrade_func = typemap, upgrade_func
        sa.types.TypeDecorator.__init__(self, **kwargs)


    def process_bind_param(self, value, dialect):
        """
        SA override, transform ``value`` before it's bound in a SQL statement.
        """
        if value is None: value = {}
        assert type(value) is dict
        return self.upgrade(value)


    def process_result_value(self, value, dialect):
        """
        SA override, transform ``value`` after it's been pulled from the DB.
        """
        if value is None: value = {}
        assert type(value) is dict
        return self.upgrade(value)


    def copy(self):
        """
        SA override, clone the current instance.
        """
        return PropertyDict(typemap=self.typemap, upgrade_func=self.upgrade_func)


    def upgrade(self, d):
        """
        Upgrade (automatically inject missing fields) and validate (revert
        values) the dict ``d`` if instance was supplied with a typemap and/or
        custom upgrade callback.
        """
        if self.typemap:
            result = dict((key, spec.defvalue) for (key, spec) in self.typemap.iteritems())
            for (key, value) in d.iteritems():
                try:
                    result[key] = self.typemap[key].filter(value)
                except KeyError:
                    pass
        else:
            result = d.copy()
        if self.upgrade_func:
            self.upgrade_func(d, result)
        return result


#############################################################################
# Enum (bitfield flags) type.
#############################################################################

class Enum(dict):
    """
    Enum like object which maps keys to a sequence of bits (2^N) values which
    can combined to together etc. The flags (enum keys) can be accessed as
    ordinary attributes of a 'Enum' instance.

    Note: enum values/flags have to begin with a capitalized letter!

    Example:
      # 1. Use case: standard enumeration.
      Color = Enum('Black', 'White')

      background = Color.White

      if background != Color.Black:
        print "Background isn't black!"

      # 2. Use case: flags combined for storage in bitfield.
      UserRole = Enum('Admin', 'Support', 'Moderator', 'Guest')

      role = UserRole.Admin | UserRole.Moderator

      if role & UserRole.Moderator:
        print "User has moderation rights!"

      if (role & UserRole.Support) == 0:
        print "User isn't in a support role!"

    Note: enums are essentially a dict with predeterminied key values, using
    the standard dict methods to explore the contents of an instance.
    """

    def __init__(self, *args):
        self.__dict__.__init__()
        for (n, key) in enumerate(args):
            assert(type(key) in [str, unicode])
            self[key.capitalize()] = 2**n

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise KeyError("Enum has no indentifier '%s'" % name)

    def __missing__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        self[name] = value

    def __repr__(self):
        return "Enum(%s)" % ",".join([repr(k) for k in self])


#############################################################################
# Custom flags (enum/bitfield) column type.
#############################################################################

class Bitfield(sa.types.TypeDecorator):
    """
    Custom SQLAlchemy database type for storing single or combined enumeration
    flags in a bitfield. Column will default to 0 which is the empty bitfield.

    Example:
      # User role enumeration.
       UserRole = Enum('Admin', 'Support', 'Moderator', 'Guest')

      # SQLAlchemy ORM column declaration.
      role  = Column(Bitfield(UserRole), default

    """
    impl = sa.types.Integer


    def __init__(self, enum, **kwargs):
        assert type(enum) is Enum
        self.enum = enum
        self.maxbits = (2**len(enum) - 1) # All possible flags joined together.
        sa.types.TypeDecorator.__init__(self, **kwargs)

    def process_bind_param(self, value, dialect):
        """
        SA override, transform ``value`` before it's bound in a SQL statement.
        """
        if value is None: value = 0
        assert value <= self.maxbits
        return value


    def process_result_value(self, value, dialect):
        """
        SA override, transform ``value`` after it's been pulled from the DB.
        """
        if value is None: value = 0
        assert value <= self.maxbits
        return value


    def copy(self):
        """
        SA override, clone the current instance.
        """
        return Bitfield(self.enum)


#############################################################################
# Custom zlib compressed UTF-8 field for storing unicode data.
#############################################################################

import zlib

class UnicodeCompressedText(sa.types.TypeDecorator):
    impl = sa.types.LargeBinary

    def process_bind_param(self, value, dialect):
        """
        SA override, transform ``value`` before it's bound in a SQL statement.
        """
        if value is None:
            value = u""
        if type(value) is not unicode:
            value = unicode(value)
        return zlib.compress(value.encode('utf-8'))


    def process_result_value(self, value, dialect):
        """
        SA override, transform ``value`` after it's been pulled from the DB.
        """
        if value:
            return zlib.decompress(value).decode('utf-8')
        else:
            return u""


    def copy(self):
        """
        SA override, clone the current instance.
        """
        return UnicodeCompressedText(self.impl.length)


##############################################################################
# The End.
##############################################################################
