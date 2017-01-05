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
   Provide exception classes for :mod:`migrate`
"""


class Error(Exception):
    """Error base class."""


class ApiError(Error):
    """Base class for API errors."""


class KnownError(ApiError):
    """A known error condition."""


class UsageError(ApiError):
    """A known error condition where help should be displayed."""


class ControlledSchemaError(Error):
    """Base class for controlled schema errors."""


class InvalidVersionError(ControlledSchemaError):
    """Invalid version number."""


class DatabaseNotControlledError(ControlledSchemaError):
    """Database should be under version control, but it's not."""


class DatabaseAlreadyControlledError(ControlledSchemaError):
    """Database shouldn't be under version control, but it is"""


class WrongRepositoryError(ControlledSchemaError):
    """This database is under version control by another repository."""


class NoSuchTableError(ControlledSchemaError):
    """The table does not exist."""


class PathError(Error):
    """Base class for path errors."""


class PathNotFoundError(PathError):
    """A path with no file was required; found a file."""


class PathFoundError(PathError):
    """A path with a file was required; found no file."""


class RepositoryError(Error):
    """Base class for repository errors."""


class InvalidRepositoryError(RepositoryError):
    """Invalid repository error."""


class ScriptError(Error):
    """Base class for script errors."""


class InvalidScriptError(ScriptError):
    """Invalid script error."""


class InvalidVersionError(Error):
    """Invalid version error."""

# migrate.changeset

class NotSupportedError(Error):
    """Not supported error"""


class InvalidConstraintError(Error):
    """Invalid constraint error"""

class MigrateDeprecationWarning(DeprecationWarning):
    """Warning for deprecated features in Migrate"""
