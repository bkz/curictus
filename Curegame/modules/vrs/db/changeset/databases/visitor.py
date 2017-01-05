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

"""
   Module for visitor class mapping.
"""
import sqlalchemy as sa

from ...changeset import ansisql
from ...changeset.databases import sqlite, postgres, mysql

# Map SA dialects to the corresponding Migrate extensions
DIALECTS = {
    "default": ansisql.ANSIDialect,
    "sqlite": sqlite.SQLiteDialect,
    "postgres": postgres.PGDialect,
    "postgresql": postgres.PGDialect,
    "mysql": mysql.MySQLDialect,
}


def get_engine_visitor(engine, name):
    """
    Get the visitor implementation for the given database engine.

    :param engine: SQLAlchemy Engine
    :param name: Name of the visitor
    :type name: string
    :type engine: Engine
    :returns: visitor
    """
    # TODO: link to supported visitors
    return get_dialect_visitor(engine.dialect, name)


def get_dialect_visitor(sa_dialect, name):
    """
    Get the visitor implementation for the given dialect.

    Finds the visitor implementation based on the dialect class and
    returns and instance initialized with the given name.

    Binds dialect specific preparer to visitor.
    """

    # map sa dialect to migrate dialect and return visitor
    sa_dialect_name = getattr(sa_dialect, 'name', 'default')
    migrate_dialect_cls = DIALECTS[sa_dialect_name]
    visitor = getattr(migrate_dialect_cls, name)

    # bind preparer
    visitor.preparer = sa_dialect.preparer(sa_dialect)

    return visitor

def run_single_visitor(engine, visitorcallable, element,
    connection=None, **kwargs):
    """Taken from :meth:`sqlalchemy.engine.base.Engine._run_single_visitor`
    with support for migrate visitors.
    """
    if connection is None:
        conn = engine.contextual_connect(close_with_result=False)
    else:
        conn = connection
    visitor = visitorcallable(engine.dialect, conn)
    try:
        if hasattr(element, '__migrate_visit_name__'):
            fn = getattr(visitor, 'visit_' + element.__migrate_visit_name__)
        else:
            fn = getattr(visitor, 'visit_' + element.__visit_name__)
        fn(element, **kwargs)
    finally:
        if connection is None:
            conn.close()
