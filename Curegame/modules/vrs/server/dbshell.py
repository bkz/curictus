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
import logging

_log = logging.getLogger('vrs-dbshell')

###########################################################################
# DB shell entry-point.
###########################################################################

def main(rootdir):
    try:
        from vrs.db import ActiveRecord
        from vrs.db.schema import Zone, Station, Activity, Patient, Session
        from vrs.server.schema import SyncMetaData

        from vrs.config import Config
        config = Config(os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"))

        import vrs.server
        db = vrs.server.connect_db(config)

        import vrs.db
        banner = "PCMS DB Shell %s => %s" % (config.SYSTEM_VERSION, str(vrs.db.engine.url))

        def reset_sync(station_guid):
            """
            Reset sync metadata for station identified by ``station_guid``
            which will result in a full resync on the next sync attempt.
            """
            s = db.query(Station).filter(Station.guid == station_guid).one()
            r = db.query(SyncMetaData).filter(SyncMetaData.station == s).one()
            db.delete(r)
            db.commit()

        import code
        code.interact(banner=banner, local=locals())

    except KeyboardInterrupt:
        pass


###########################################################################
# The End.
###########################################################################
