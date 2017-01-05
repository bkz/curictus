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

import inspect
import sqlalchemy

##############################################################################
# Global constants.
##############################################################################

NLTAB = ',\n    '

COLUMN = """Column(%(name)r, %(type)s%(constraints)s%(args)s)"""

FOREIGN_KEY = """ForeignKeyConstraint(%(names)s, %(specs)s, name=%(name)s)"""

TABLE = """\
Table('%(name)s', metadata,
    %(columns)s,
    %(constraints)s)
"""

##############################################################################
# Override __repr__ for SA objects to match the original code.
##############################################################################


def textclause_repr(self):
    return 'text(%r)' % self.text


def table_repr(self):
    data = {
        'name': self.name,
        'columns': NLTAB.join([repr(cl) for cl in self.columns]),
        'constraints': NLTAB.join(
            [repr(cn) for cn in self.constraints
            if isinstance(cn, sqlalchemy.ForeignKeyConstraint)]),
        }

    if data['constraints']:
        data['constraints'] = data['constraints'] + ','

    return TABLE % data


def column_repr(self):
    kwarg = []

    if self.key != self.name:
        kwarg.append( 'key')

    if hasattr(self, 'primary_key'):
        if self.primary_key:
            kwarg.append( 'primary_key')
    if self.index:
        kwarg.append( 'index')

    if self.unique:
        kwarg.append( 'unique')

    if not self.nullable:
        kwarg.append( 'nullable')

    if self.default:
        kwarg.append( 'default')

    if hasattr(self, 'check'):
        kwarg.append('check')

    if self.onupdate:
        kwarg.append( 'onupdate')

    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg )

    name = self.name

    coltype = repr(self.type)

    data = {'name': self.name,
            'type': coltype,
            'constraints': ', '.join([repr(cn) for cn in self.constraints]),
            'args': ks and ks or '',
            }

    if data['constraints']:
        if data['constraints']:
            data['constraints'] = ', ' + data['constraints']
    if data['args']:
        if data['args']:
            data['args'] = ', ' + data['args']

    return COLUMN % data


def foreignkeyconstraint_repr(self):
    data = {'name': repr(self.name),
            'names': repr([x.parent.name for x in self.elements]),
            'specs': repr([x._get_colspec() for x in self.elements])
            }
    return FOREIGN_KEY % data


def columnsdefault_repr(self):
    if self.is_callable:
        return "<lambda>"
    else:
        return repr(self.arg)


def checkconstraint_repr(self):
    return """CheckConstraint("%s")""" % self.sqltext


def string_repr(self):
    return "%s(%s)" % (
        self.__class__.__name__,
        ", ".join("%s=%r" % (k, getattr(self, k, None))
                  for k in inspect.getargspec(self.__init__)[0][1:]
                  if bool(k) and k not in ['length', 'convert_unicode','assert_unicode','unicode_error','_warn_on_bytestring']))


##############################################################################
# Automatically monkey-patch SA on import.
##############################################################################

sqlalchemy.sql.expression._TextClause.__repr__ = textclause_repr
sqlalchemy.schema.Table.__repr__ = table_repr
sqlalchemy.schema.Column.__repr__ = column_repr
sqlalchemy.schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr
sqlalchemy.schema.ColumnDefault.__repr__ = columnsdefault_repr
sqlalchemy.schema.CheckConstraint.__repr__ = checkconstraint_repr
sqlalchemy.types.String.__repr__ = string_repr


##############################################################################
# The End.
##############################################################################
