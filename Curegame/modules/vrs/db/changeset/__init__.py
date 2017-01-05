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
   This module extends SQLAlchemy and provides additional DDL [#]_
   support.

   .. [#] SQL Data Definition Language
"""
import re
import warnings

import sqlalchemy
from sqlalchemy import __version__ as _sa_version

warnings.simplefilter('always', DeprecationWarning)

_sa_version = tuple(int(re.match("\d+", x).group(0)) for x in _sa_version.split("."))
SQLA_06 = _sa_version >= (0, 6)

del re
del _sa_version

from ..changeset.schema import *
from ..changeset.constraint import *

sqlalchemy.schema.Table.__bases__ += (ChangesetTable, )
sqlalchemy.schema.Column.__bases__ += (ChangesetColumn, )
sqlalchemy.schema.Index.__bases__ += (ChangesetIndex, )

sqlalchemy.schema.DefaultClause.__bases__ += (ChangesetDefaultClause, )
