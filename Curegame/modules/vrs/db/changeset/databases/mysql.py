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
   MySQL database specific implementations of changeset classes.
"""

from sqlalchemy.databases import mysql as sa_base
from sqlalchemy import types as sqltypes

from ...changeset import exceptions
from ...changeset import ansisql, SQLA_06


if not SQLA_06:
    MySQLSchemaGenerator = sa_base.MySQLSchemaGenerator
else:
    MySQLSchemaGenerator = sa_base.MySQLDDLCompiler

class MySQLColumnGenerator(MySQLSchemaGenerator, ansisql.ANSIColumnGenerator):
    pass


class MySQLColumnDropper(ansisql.ANSIColumnDropper):
    pass


class MySQLSchemaChanger(MySQLSchemaGenerator, ansisql.ANSISchemaChanger):

    def visit_column(self, delta):
        table = delta.table
        colspec = self.get_column_specification(delta.result_column)
        if delta.result_column.autoincrement:
            primary_keys = [c for c in table.primary_key.columns
                       if (c.autoincrement and
                            isinstance(c.type, sqltypes.Integer) and
                            not c.foreign_keys)]

            if primary_keys:
                first = primary_keys.pop(0)
                if first.name == delta.current_name:
                    colspec += " AUTO_INCREMENT"
        old_col_name = self.preparer.quote(delta.current_name, table.quote)

        self.start_alter_table(table)

        self.append("CHANGE COLUMN %s " % old_col_name)
        self.append(colspec)
        self.execute()

    def visit_index(self, param):
        # If MySQL can do this, I can't find how
        raise exceptions.NotSupportedError("MySQL cannot rename indexes")


class MySQLConstraintGenerator(ansisql.ANSIConstraintGenerator):
    pass

if SQLA_06:
    class MySQLConstraintDropper(MySQLSchemaGenerator, ansisql.ANSIConstraintDropper):
        def visit_migrate_check_constraint(self, *p, **k):
            raise exceptions.NotSupportedError("MySQL does not support CHECK"
                " constraints, use triggers instead.")

else:
    class MySQLConstraintDropper(ansisql.ANSIConstraintDropper):

        def visit_migrate_primary_key_constraint(self, constraint):
            self.start_alter_table(constraint)
            self.append("DROP PRIMARY KEY")
            self.execute()

        def visit_migrate_foreign_key_constraint(self, constraint):
            self.start_alter_table(constraint)
            self.append("DROP FOREIGN KEY ")
            constraint.name = self.get_constraint_name(constraint)
            self.append(self.preparer.format_constraint(constraint))
            self.execute()

        def visit_migrate_check_constraint(self, *p, **k):
            raise exceptions.NotSupportedError("MySQL does not support CHECK"
                " constraints, use triggers instead.")

        def visit_migrate_unique_constraint(self, constraint, *p, **k):
            self.start_alter_table(constraint)
            self.append('DROP INDEX ')
            constraint.name = self.get_constraint_name(constraint)
            self.append(self.preparer.format_constraint(constraint))
            self.execute()


class MySQLDialect(ansisql.ANSIDialect):
    columngenerator = MySQLColumnGenerator
    columndropper = MySQLColumnDropper
    schemachanger = MySQLSchemaChanger
    constraintgenerator = MySQLConstraintGenerator
    constraintdropper = MySQLConstraintDropper
