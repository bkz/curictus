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

import os, sys
import datetime
import logging
import re

import sqlalchemy as sa

import tabledump
import formatter

VERSION_TABLENAME = 'migrate'

_log = logging.getLogger('migrate')

##############################################################################
# Integrate SQLAlchemy-migrate library.
##############################################################################

# Importing library will resulting in SA being monkeypatched to extend the DDL
# in order to support create/drop/etc statements needed to perform migrations.
from changeset.constraint import \
    PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint, UniqueConstraint


##############################################################################
# Utilities.
##############################################################################

def write_comment(s):
    print 3 * ' ', "#", s


def write_code(s):
    print 3 * ' ', s


def write_create_table(table):
    """
    Generate template code definition for ``table``.
    """
    code = "%s = %s" % (table.name, repr(table))
    for line in code.split("\n"):
        write_code(line)
    write_code("%s.create()" % table.name)
    write_code("")


def write_table_autoload(table, drop=False):
    """
    Generate template code to setup a reflected sa.Table() for ``table``.
    """
    write_code("%s = Table('%s', metadata, autoload=True, autoload_with=conn)" % (table.name, table.name))
    if drop:
        write_code("")
        write_code("%s.drop()" % table.name)


def write_load_tabledump(table, add_cols=[], alter_cols=[], delete_cols=[]):
    """
    Generate template code for performing add/alter/delete columns operation
    for ``table`` using a tabledump.
    """
    if add_cols or alter_cols or delete_cols:
        write_code("def f_%s(row):" % table.name)
        for c in add_cols:
            write_code("    row['%s'] =" % c.name)
        for (new_c, old_c) in alter_cols:
            write_code("    row['%s'] = " % new_c.name)
        for c in delete_cols:
            write_code("    del row['%s']" % c.name)
        write_code("")
        write_code("migrate.load_tabledump(conn, %s, DUMP_FILENAME, row_filters=f_%s)" % (table.name, table.name))
    else:
        write_code("migrate.load_tabledump(conn, %s, DUMP_FILENAME)" % table.name)


def list_table_names(conn):
    """
    Return names of all available tables in the DB via ``conn``.
    """
    return [table.name for table in sa.MetaData(bind=conn, reflect=True).sorted_tables]


##############################################################################
# Analyze and compare live DB with new schema metadata.
##############################################################################

def get_columndesc(col):
    """
    Generate a string with SQL statement describing ``col```.
    """
    d = []
    if col.primary_key:
        d.append("PRIMARY KEY")
    if col.nullable is not None:
        d.append("NOT_NULL")
    if col.index is not None:
        d.append("INDEX")
    if col.unique is not None:
        d.append("UNIQUE")
    if col.default is not None:
        d.append("DEFAULT")
    if col.server_default is not None:
        d.append("SERVER_DEFAULT")
    if col.onupdate is not None:
        d.append("ONUPDATE")
    if col.server_onupdate is not None:
        d.append("SERVER_ONUPDATE")
    return "|".join(d)


def analyze(source_url, new_metadata, dump_tables=[]):
    """
    Analyze database at ``source_url`` and compare it to new schema of
    ``new_metadata``. Outputs template code (to stdout) for SA DDL statements
    and performing the migration using tabledumps. Tune it manually and replace
    various steps with optimized SQL statements etc. as needed.

    Return True if schema in DB differs from ``new_metadata``.

    NOTE: If you intend to dump tables to disk and perform manual filtering,
    specify a list tables names via ``dump_tables`` to have analyze() generate
    boiler-plate code along with template.

    Example output (with dump_tables=['customers']):

        # ---
        # TABLE stats DELETE
        # ---

        stats = Table('stats', metadata, autoload=True, autoload_with=conn)

        stats.drop()

        # ---
        # TABLE contacts CREATE
        # ---

        contacts = Table('contacts', metadata,
            Column('guid', String(), primary_key=True, index=True, unique=True, nullable=False, default=<lambda>),
            Column('phone', String(), unique=True, nullable=False),
            )

        # ---
        # TABLE customers COPY
        # TABLE customers COLUMN ADD contact_guid TYPE VARCHAR (NOT_NULL)
        # TABLE customers COLUMN ALTER name TYPE VARCHAR -> TEXT (NOT_NULL)
        # TABLE customers COLUMN DELETE id
        # ---

        customers = Table('customers', metadata, autoload=True, autoload_with=conn)

        def f_customers(row):
            row['contact_guid'] = NEW VARCHAR
            row['name'] = CONVERT row['name'] FROM VARCHAR TO TEXT
            del row['id']

        migrate.load_tabledump(conn, customers, filename, row_filters=f_customers)

    The idea is that you run analyze on the 'old' DB schema comparing it to
    your current schema, copy the template code into a migration script and
    fill in the blanks to alter/insert/delete as needed to perform the upgrade.
    """
    have_changes = False

    db_engine = sa.create_engine(source_url)
    db_metadata = sa.MetaData(bind=db_engine, reflect=True)

    new_dialect = db_engine.dialect

    db_tables = {} # {table-name -> {column-name:column}}
    for table in db_metadata.sorted_tables:
        db_tables[table.name] = dict((c.name, c) for c in table.columns)

    for table_name in set(db_metadata.tables.keys()).difference(set(new_metadata.tables.keys())):
        if table_name == VERSION_TABLENAME: continue # Skip migrate metadata table.
        write_comment("---")
        write_comment("DROP TABLE %s" % table_name)
        write_comment("---")
        write_code("")
        write_table_autoload(db_metadata.tables[table_name], drop=True)
        write_code("")
        have_changes = True

    for table in new_metadata.sorted_tables:
        if table.name == VERSION_TABLENAME: continue # Skip migrate metadata table.
        if not table.name in db_tables:
            write_comment("---")
            write_comment("CREATE TABLE %s" % table.name)
            write_comment("---")
            write_code("")
            write_create_table(table)
            write_code("")
            have_changes = True
        else:
            add_cols, alter_cols, delete_cols = [], [], []
            for new_col in table.columns:
                new_type = str(new_col.type.compile(new_dialect))
                try:
                    old_col = db_tables[table.name][new_col.name]
                except KeyError:
                    add_cols.append(new_col)
                    continue
                old_type = str(old_col.type.compile(db_engine.dialect))
                if (new_type != old_type) or (new_col.primary_key != old_col.primary_key):
                    alter_cols.append((new_col, old_col))
                else:
                    pass
            for (colname, c) in db_tables[table.name].iteritems():
                if colname not in table.columns:
                    delete_cols.append(c)
            if (table.name in dump_tables) or add_cols or alter_cols or delete_cols:
                write_comment("---")
                write_comment("ALTER TABLE %s" % table.name)
                for c in add_cols:
                    write_comment("ADD COLUMN")
                    write_comment("  %s" % repr(c))
                for (new_c, old_c) in alter_cols:
                    write_comment("ALTER COLUMN")
                    write_comment("  %s" % repr(old_c))
                    write_comment("  %s" % repr(new_c))
                for c in delete_cols:
                    write_comment("DELETE COLUMN")
                    write_comment("  %s" % repr(c))
                write_comment("---")
                write_code("")
                write_table_autoload(table)
                write_code("")
                if table.name in dump_tables:
                    write_load_tabledump(table, add_cols, alter_cols, delete_cols)
                write_code("")
                have_changes = True
    del new_dialect
    del db_metadata
    del db_engine
    return have_changes


##############################################################################
# Portable DB-agnostic table dump and restore.
##############################################################################

NUM_ROWS_PER_INSERT = 50000

def paged_insert(conn, table, rows, limit):
    """
    Perform 'pagiated' insert to ``table`` via the ``conn`` connection from the
    list of ``rows`` (which needs to behave like an interable and really a
    list). To keep the DB connection from overloading we'll ``limit`` the
    number of insert at a time to keep memory usage under control.
    """
    count = 0
    batch = []

    for r in rows:
        batch.append(r)
        if len(batch) >= limit:
            _log.debug("Inserting rows %d-%d" % (count, count+len(batch)))
            conn.execute(table.insert(), batch)
            batch = []
            count += limit
    if batch:
        _log.debug("Inserting rows %d-%d" % (count, count+len(batch)))
        conn.execute(table.insert(), batch)
        count += len(batch)


def load_tabledump(conn, table, filename, table_name=None, row_filters=[], exclude_columns=[]):
    """
    Migrate (insert) data to ``table`` (declarative or Table) for via ``conn``.
    Source data is read from ``filename`` which should contain the expected
    table ``table_name`` (if None we'll use the the same name as ``table``).

    In order to filter and mutate row data as it is inserted two mechanism are provided:

    1. ``row_filters`` which is a single func or a list of functions with the
       following signature filter(row), where 'row' is dict mapping columns to
       keys and value as row values. Filter may freely mutate values, add and
       delete keys.

    2. ``exclude_columns`` is list of column names which will be automatically
       be deleted from each row as we iterate over the source data. If set,
       deletion of columns will be performed before running any row filters.

    Copying and filtering is tuned for low memory usage, everything is
    connected as a stream of generators where data flows from the source, via
    filters and finally to the target DB for insertion. No operations ever
    requires that the entire dataset be in memory which would become
    impractical quickly.
    """
    if hasattr(table, '__table__'):
        table = table.__table__
    if type(row_filters) not in (tuple, list):
        row_filters = [row_filters]
    if table_name is None:
        table_name = table.name
    _log.info("Populating '%s' from dumped table '%s'" % (table.name, table_name))
    rows = tabledump.iterrows(filename, table_name)
    # Create filter for deleting columns from source table data.
    if exclude_columns:
        def remove_cols(row):
            for colname in exclude_columns:
                del row[colname]
        row_filters = [remove_cols] + row_filters
    # Wrap all filter in single function we can apply using a generator.
    if row_filters:
        def apply_filters(row):
            for f in row_filters:
                f(row)
            return row
        rows = (apply_filters(r) for r in rows)
    # Custom SA columns (which inherit from TypeDecorator) need to be decoded
    # via the custom bind/result processors as we dumped data from the source
    # DB straight to disk without involving the custom legacy SA DB schema. For
    # example, a PickleType columns will be saved to disk in raw form, not
    # converted to dicts as you'd expected. Why? Because when we reflected the
    # source DB we only learned about the basic DB types used to stored the
    # data - we don' know anything about the abstractions built on top. Thus we
    # have to turn the data back to dicts in this case before we can pass it to
    # SA and the new schema which knows that the columns is of custom type.
    #
    # As you proably can guess, this will break whenever you move from a custom
    # column to another one as we'll try to deserialize data as though it was
    # of the new type. In order to handle this case you need manually convert
    # the old data and serialize it to a raw form which will pass trough
    # without causing any errors. Why not simply disable the filterting for
    # certain columns? Well, aside from adding another special case doing it
    # this way make sure that _all_ of the data is good condition as it is
    # deserialzied and serialized back again.
    def sa_type_filter(row):
        try:
            column_filters = sa_type_filter._column_filters
        except AttributeError:
            column_filters = []
            for c in [c for c in table.columns if c.name in row]:
                func = c.type.result_processor(conn.dialect, c.type)
                if func:
                    column_filters.append((c,func))
                    _log.debug("Decoding custom type '%s.%s'" % (table.name, c.name))
            setattr(sa_type_filter, '_column_filters', column_filters)
        for (c, func) in column_filters:
            row[c.name] = func(row[c.name])
        return row
    rows = (sa_type_filter(r) for r in rows)
    paged_insert(conn, table, rows, NUM_ROWS_PER_INSERT)


def save_tabledump(source_url, filename, table_names=[]):
    """
    Dump ``tables`` from DB at ``source_url`` to ``filename``.
    """
    tabledump.write(filename, source_url, table_names)


##############################################################################
# Migration script template.
##############################################################################

MIGRATION_TEMPLATE="""\
from sqlalchemy import *

from vrs.db.migrate import \\
    PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint, UniqueConstraint

def upgrade(engine, metadata):
"""


##############################################################################
# Migration support (upgrade using repository with scripts).
##############################################################################

def get_dbversion(source_url):
    """
    Attempt to locate migration metadata table and find the latest (highest)
    migrated version for the DB at ``source_url``. Returns version as an int or
    None on failure.
    """
    version = None
    engine = sa.create_engine(source_url)
    try:
        table = sa.Table(VERSION_TABLENAME, sa.MetaData(), autoload=True, autoload_with=engine)
        row = engine.execute(sa.select([table.c.version]).order_by(table.c.version.desc())).fetchone()
        if row:
            version = row[table.c.version]
    except sa.exc.NoSuchTableError:
        pass
    return version


def set_dbversion(source_url, version):
    """
    Attempt to locate migration metadata table and find the base version of DB
    at ``source_url``. Returns version as an int or None on failure.
    """
    engine = sa.create_engine(source_url)
    metadata = sa.MetaData(bind=engine)
    table = sa.Table(VERSION_TABLENAME, metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('timestamp', sa.DateTime, default=datetime.datetime.utcnow),
                     sa.Column('version', sa.Integer, unique=True, nullable=False))
    metadata.create_all()
    row = engine.execute(sa.select([table.c.version]).order_by(table.c.version.desc())).fetchone()
    if (not row) or row["version"] != version:
        engine.execute(table.insert(), version=version)
    return get_dbversion(source_url)


def import_module(filepath):
    """
    Import and return module object for file at ``filepath``.
    """
    path, filename = os.path.split(filepath)
    filename, ext = os.path.splitext(filename)
    sys.path.append(path)
    module = __import__(filename)
    del sys.path[-1]
    return module


def runscript(db_url, module):
    """
    Execute migration script ``module`` to upgrade DB at ``db_url``.

    Note: ``module`` should have the same interface as MIGRATION_TEMPLATE.
    """
    try:
        callback = getattr(module, 'upgrade')
    except AttributeError:
        raise RuntimeError("Invalid/corrupt migraction script %s" % module)

    engine = sa.create_engine(db_url, strategy='threadlocal')
    engine.begin()
    try:
        callback(engine, sa.MetaData(bind=engine))
        engine.commit()
    except:
        engine.rollback()
        raise
    finally:
        pass


def list_files(path, ext):
    """
    List all files in ``path`` with extensions ``ext``.
    """
    return (filename for filename in os.listdir(path)
            if os.path.splitext(filename)[1] == ext)


def list_migration_scripts(repository):
    """
    Enumerate all migration scripts named <from>_<to>.py (i.e 001_to_002.py) in
    ``repository`` and return a dict mapping:
      old_version (int) -> tuple(new_version, filename).
    """
    config = {}
    # We have to support migrations support as both .py files and as compiled
    # .pyc if we are running in frozen mode (where the .py aren't
    # available). We also have to give preference to .py files in order to
    # catch changes, otherwise stale .pyc would be used instead re-compiling
    # the migration scripts.
    files = list_files(repository, ".py") or list_files(repository, ".pyc")
    for filename in sorted(files):
        m = re.match(r"(\d+)_to_(\d+).+(py|pyc)$", filename)
        if m:
            v_from, v_to = int(m.group(1)), int(m.group(2))
            # Only allow upgrade from N to N+1 to keep linear order.
            if (v_from in config) or ((v_from+1) != v_to):
                raise RuntimeError("Only single step migration are allowed (%s)" % filename)
            config[v_from] = (v_to, os.path.join(repository, filename))
            _log.debug("Found migration script %d -> %d (%s)" % (v_from, v_to, filename))
    # Make sure we have a linear sequence of migration scripts,
    # i.e. 001_to_002.py -> 002_to_003.py -> 003_to_004.py ...
    def check_version(a,b):
        if not (a+1) == b:
            a_filename = config[a][1]
            b_filename = config[b][1]
            raise RuntimeError("Non linear migration sequence %s -> %s" % (a_filename, b_filename))
        return b
    reduce(check_version, sorted(config.keys()))
    return config


def latest_version(migrations):
    """
    Retrieve the highest version number available for ``migrations`` from a
    repository. Returns and int or None on failure.
    """
    if len(migrations):
        return max([v_to for (v_to, filename) in migrations.itervalues()])
    else:
        return None


def upgrade(url, repository):
    """
    Migrate DB at ``url`` to the latest version using scripts in ``repository``.
    """
    migrations  = list_migration_scripts(repository)
    max_version = latest_version(migrations)

    version = get_dbversion(url)
    if version is None:
        # Newly created databases will be up-to-date since the SA will
        # automatically create tables etc. Missing the migration metadata table
        # in this case is not that big of a deal. Client with existing DB which
        # aren't version controlled require manually inspection anyway so
        # bumping to the latest version (and not performing any destructive
        # migrations actions) is pretty safe.
        _log.warning("DB not under version control (marking as latest version %d)" % max_version)
        set_dbversion(url, max_version)
    else:
        if version == max_version:
            _log.info("DB at latest version %d" % max_version)
        else:
            _log.info("DB at version %d, latest version %d" % (version, max_version))
            while version != max_version:
                new_version, filename = migrations[version]
                _log.info("Upgrading DB from version %d to %d" % (version, new_version))
                runscript(url, import_module(filename))
                set_dbversion(url, new_version)
                version = new_version


##############################################################################
# The End.
##############################################################################
