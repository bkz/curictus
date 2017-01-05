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

import os
import cPickle
import logging
import struct

import sqlalchemy as sa

_log = logging.getLogger('dump')

##############################################################################
# Data format.
##############################################################################

# 1. Table rows are written sequentially to disk as pickled dicts, table B data
#    starts immediately after the last row of table A and so on.
#
# table_a_row_1 = {'col-1':value, 'col-2':value, ..., 'col-n':value}
# table_a_row_1 = {'col-1':value, 'col-2':value, ..., 'col-n':value}
# ...
# table_a_row_n = { ... }
#
# 2. After the last row at list of table metadata is written which contains N
#    tuples of (table_name, columns, rowcount, offset) where N = table count.
#
# [(table_name, ...), (table_name, ...), ..., (table_name, ...)]
#
#  -> table_name : str  = name of table
#  -> columns    : dict = column names (keys) => column SQL datatype (values)
#  -> rowcount   : int  = table serialized row count
#  -> offset     : int  = offset in bytes to the first pickled row for table
#
# 3. A single 4-byte int is the last element in the file which is the offset in
#    bytes to the table metadata (2).
#
# Writing a table dump involves steps 1,2,3 while reading a dump reverses the
# order, first you read the offset to the table metadata (3), unpickle and read
# the table offsets (2) and finally unpickle rows for a selected table.

##############################################################################
# Utilities.
##############################################################################

def get_primary_key(table):
    """
    Get primary key sa.Column() for ``table``, return None on failure.
    """
    for c in table.columns:
        if c.primary_key:
            return c
    else:
        return None


##############################################################################
# Restore table data from dump.
##############################################################################

def get_table_info(f):
    """
    Return a list of metadata in the form (name, columns, rowcount, offset).
    """
    f.seek(-struct.calcsize('I'), os.SEEK_END)
    pos = struct.unpack('I', f.read(struct.calcsize('I')))[0]
    f.seek(pos)
    table_info = cPickle.load(f)
    f.seek(0)
    return table_info


def iterrows(filename, table_name):
    """
    Iterate (yield) over all rows for ``table_name`` in dumped database
    ``filename``. Will raise an exception if ``table_name`` doesn't exist.
    """
    with open(filename, "rb") as f:
        for (name, columns, rowcount, offset) in get_table_info(f):
            if name == table_name:
                f.seek(offset)
                for i in xrange(rowcount):
                    row = cPickle.load(f)
                    yield row
                break # Table found, exit successfully.
        else:
            raise RuntimeError("Table %s not found in dump" % table_name)


##############################################################################
# Dump table data to disk.
##############################################################################

NUM_ROWS_PER_SELECT = 50000

def write(filename, source_url, table_names=[]):
    """
    Dump ``table_names`` from DB at ``source_url`` to ``filename``. If
    tables has a primary key dumping will be queried in an efficient manner
    (paged batch selects) otherwise we''l resort to a single select statement.
    """
    engine = sa.create_engine(source_url)
    conn = engine.connect()
    metadata = sa.MetaData(bind=conn, reflect=True)
    with open(filename, "wb") as f:
        table_info = []
        for table in [metadata.tables[name] for name in table_names]:
            offset = f.tell()
            rowcount = table.count().scalar()
            columns = dict((c.name, str(c.type)) for c in table.columns)
            # Note: we have to involve an ORDER BY statement in our paginated
            # queries since the LIMIT/OFFSET statement have no order semantics,
            # PostgreSQL will for example random results unless one explictely
            # specifies the sort order.
            _log.debug("Dumping %d rows from '%s'" % (rowcount, table.name))
            pk = get_primary_key(table)
            if (pk is not None):
                for i in range(0, rowcount, NUM_ROWS_PER_SELECT):
                    query = sa.select([table]).offset(i).limit(NUM_ROWS_PER_SELECT).order_by(pk)
                    for row in conn.execute(query):
                        cPickle.dump(dict(row), f, cPickle.HIGHEST_PROTOCOL)
            else:
                for row in conn.execute(sa.select([table])):
                    cPickle.dump(dict(row), f, cPickle.HIGHEST_PROTOCOL)
            table_info.append((table.name, columns, rowcount, offset))
        offset = f.tell()
        cPickle.dump(table_info, f, cPickle.HIGHEST_PROTOCOL)
        f.write(struct.pack('I', offset))
    conn.close()


##############################################################################
# The End.
##############################################################################
