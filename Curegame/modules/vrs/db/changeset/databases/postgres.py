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
   `PostgreSQL`_ database specific implementations of changeset classes.

   .. _`PostgreSQL`: http://www.postgresql.org/
"""
from ...changeset import ansisql, SQLA_06

if not SQLA_06:
    from sqlalchemy.databases import postgres as sa_base
    PGSchemaGenerator = sa_base.PGSchemaGenerator
else:
    from sqlalchemy.databases import postgresql as sa_base
    PGSchemaGenerator = sa_base.PGDDLCompiler


class PGColumnGenerator(PGSchemaGenerator, ansisql.ANSIColumnGenerator):
    """PostgreSQL column generator implementation."""
    pass


class PGColumnDropper(ansisql.ANSIColumnDropper):
    """PostgreSQL column dropper implementation."""
    pass


class PGSchemaChanger(ansisql.ANSISchemaChanger):
    """PostgreSQL schema changer implementation."""
    pass


class PGConstraintGenerator(ansisql.ANSIConstraintGenerator):
    """PostgreSQL constraint generator implementation."""
    pass


class PGConstraintDropper(ansisql.ANSIConstraintDropper):
    """PostgreSQL constaint dropper implementation."""
    pass


class PGDialect(ansisql.ANSIDialect):
    columngenerator = PGColumnGenerator
    columndropper = PGColumnDropper
    schemachanger = PGSchemaChanger
    constraintgenerator = PGConstraintGenerator
    constraintdropper = PGConstraintDropper
