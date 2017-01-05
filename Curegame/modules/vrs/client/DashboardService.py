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

import logging
import re
import socket
import time
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as orm

import vrs.locale
import vrs.metrics

from vrs.as3rpc import remotemethod
from vrs.config import activities
from vrs.db import has_one, has_many, computed_field, computed_array
from vrs.db.utils import transactional
from vrs.client.ActivityConfig import GameConfig, TestConfig
from vrs.client.schema import Zone, Station, Activity, Patient, Session
from vrs.util import httputil

_log = logging.getLogger('dashboard')

##############################################################################
# SystemInfo.
##############################################################################

CHECKIP_HOST = "checkip.dyndns.com"
CHECKIP_PATH = "/"

class SystemInfo(object):
    __amf_class__ = "vrs.system.SystemInfo"

    zone_guid      = computed_field(str)
    station_guid   = computed_field(str)
    station_alias  = computed_field(str)
    local_ip       = computed_field(str)
    public_ip      = computed_field(str)
    openvpn_ip     = computed_field(str)
    connected_net  = computed_field(bool)
    version        = computed_field(str)

    def __init__(self, config=None):
        if config:
            self.config = config
            self.station_alias = config.STATION_ALIAS
            self.zone_guid = config.ZONE_GUID
            self.station_guid = config.STATION_GUID
            self.local_ip = self.get_local_ip()
            self.public_ip = self.get_public_ip()
            self.openvpn_ip = self.get_openvpn_ip()
            self.connected_net = self.public_ip != ""
            self.version = config.SYSTEM_BUILD


    def get_local_ip(self):
        """
        Return (DHCP) IP of local ehternet interface in string form (returns
        empty string if not connected).
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('google.se', 80))
            return s.getsockname()[0]
        except:
            return ""


    def get_public_ip(self):
        """
        Return public (router) IP via DynDNS HTTP service in string form
        (returns empty string if not connected).
        """
        page = httputil.get(CHECKIP_HOST, CHECKIP_PATH) or ""
        match = re.search(r"Current IP Address: (\d+\.\d+\.\d+\.\d+)", page)
        if match:
            return match.group(1)
        else:
            return ""

    def get_openvpn_ip(self):
        """
        Return IP of OpenVPN Tun/Tap device in string form (returns empty
        string if not connected).
        """
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip.startswith('10.3'):
                return ip
        else:
            return ""


    @classmethod
    def __serialize__(cls):
        return [SystemInfo.station_alias,
                SystemInfo.zone_guid,
                SystemInfo.station_guid,
                SystemInfo.local_ip,
                SystemInfo.public_ip,
                SystemInfo.openvpn_ip,
                SystemInfo.connected_net,
                SystemInfo.version]


##############################################################################
# DashboardService.
##############################################################################

class DashboardService(object):
    __amf_service__ = "vrs.DashboardService"

    def __init__(self, config, jobqueue, db):
        self.config = config
        self.jobqueue = jobqueue
        self.db = db
        self.patientId = None
        self.lastSessionId = None
        self.language = config.SYSTEM_LOCALE


    def addjob(self, cmd, *args):
        self.jobqueue.put((cmd, args))


    def isValidPincode(self, pincode):
        return len(pincode) == 4 and pincode.isdigit()


    def getLastSessionId(self):
        assert self.patientId is not None
        lastSession = session = self.db.query(Session) \
            .order_by(Session.id.desc()) \
            .join(Patient).filter(Patient.id == self.patientId) \
            .first()
        if lastSession:
            return lastSession.id
        else:
            return None


    @remotemethod(str, value=str)
    def echo(self, value):
        return value


    @remotemethod(str)
    def clock(self):
        return time.asctime()


    @remotemethod(str)
    def raiseException(self):
        raise RuntimeError("forced exception")


    @remotemethod(SystemInfo)
    def getSystemInfo(self):
        return SystemInfo(self.config)


    @remotemethod(str)
    def getSystemBuild(self):
        return self.config.SYSTEM_BUILD


    @remotemethod(bool)
    def haveNetworkAccess(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('google.se', 80))
            s.close()
            return True
        except Exception, e:
            return False


    @remotemethod(str)
    def getLanguageCode(self):
        return self.language


    @remotemethod(bool, lang=str)
    def setLanguageCode(self, lang):
        self.language = lang
        return True


    @remotemethod(dict)
    def getTranslations(self):
        return vrs.locale.get_json_catalog(self.language)


    @remotemethod(dict)
    def getFeatureFlags(self):
        return dict(self.config.FEATURES)


    @remotemethod(bool)
    def terminate(self):
        self.addjob("terminate")
        return True


    @remotemethod(bool)
    def shutdown(self):
        self.addjob("shutdown")
        return True


    @transactional
    @remotemethod(bool, pincode=str)
    def createNewLogin(self, pincode):
        if not self.isValidPincode(pincode):
            raise RuntimeError("invalid pincode")
        if self.isPincodeInUse(pincode):
            raise RuntimeError("Pincode is alreay in use")
        zone = self.db.query(Zone).filter(Zone.guid == self.config.ZONE_GUID).one()
        patient = Patient(guid=str(uuid.uuid4()), alias=str(pincode), pincode=pincode, zone=zone)
        _log.debug("Creating patient: %s (%s)" % (patient.alias, patient.guid))
        self.db.add(patient)
        self.db.commit()
        vrs.metrics.track("create-login")
        return True


    @transactional
    @remotemethod(bool, pincode=str)
    def isPincodeInUse(self, pincode):
        if not self.isValidPincode(pincode):
            return False
        result = self.db.query(Patient).filter(Patient.pincode == pincode).\
            join(Zone).filter(Zone.guid == self.config.ZONE_GUID).all()
        return len(result) != 0


    @transactional
    @remotemethod(str)
    def getNextUnusedPincode(self):
        patients = self.db.query(Patient)\
            .filter(Patient.alias != "guest")\
            .filter(Patient.active == True)\
            .join(Zone)\
            .filter(Zone.guid == self.config.ZONE_GUID)\
            .all()
        # This is a bit of a back but since we only support 4-digit pincodes we
        # can safely scan the linear range 0001-9999 to find an unused value.
        pincodes = tuple(int(float(p.pincode)) for p in patients if p.pincode.isdigit())
        for n in range(1, 9999):
            if n not in pincodes:
                return ("%4s" % n).replace(' ', '0')
        else:
            raise RuntimeError("No 4-digit pincodes available")


    @remotemethod(bool)
    def isPatientLoggedIn(self):
        return self.patientId is not None


    @transactional
    @remotemethod(bool)
    def loginAsGuest(self):
        self.patientId = self.db.query(Patient).\
            filter(Patient.alias == "guest").\
            filter(Patient.guid == self.config.ZONE_GUID).\
            join(Zone).filter(Zone.guid == self.config.ZONE_GUID).one().id
        self.lastSessionId = self.getLastSessionId()
        _log.debug("Logged in as 'guest'")
        vrs.metrics.track("login", {"type" : "guest"})
        return True


    @transactional
    @remotemethod(bool, pincode=str)
    def loginWithPincode(self, pincode):
        self.patientId = self.db.query(Patient).filter(Patient.pincode == pincode).\
            join(Zone).filter(Zone.guid == self.config.ZONE_GUID).one().id
        self.lastSessionId = self.getLastSessionId()
        _log.debug("Logged in with pincode '%s'" % pincode)
        vrs.metrics.track("login", {"type" : "pincode"})
        return True


    @remotemethod(bool)
    def logout(self):
        self.patientId = None
        self.lastSessionId = None
        _log.debug("Logout")
        return True


    @remotemethod(bool)
    def reset(self):
        self.logout()
        self.addjob("reset")
        return True


    @transactional
    @remotemethod(Patient)
    def getCurrentPatient(self):
        if self.patientId is None:
            raise RuntimeError("patient not logged in")
        return self.db.query(Patient).filter(Patient.id == self.patientId).one()


    @transactional
    @remotemethod(bool)
    def hasNewSession(self):
        if self.patientId is None:
            return False
        session = self.db.query(Session) \
            .order_by(Session.id.desc()) \
            .join(Patient).filter(Patient.id == self.patientId) \
            .first()
        # (1) No session recorded at all for patient.
        if session is None:
            return False
        # (2) First session recorded, no previous one.
        if self.lastSessionId is None:
            return True
        # (3) Check if a new session was added.
        return (session.id != self.lastSessionId)


    @transactional
    @remotemethod(Session)
    def getLastSession(self):
        if self.patientId is None:
            raise RuntimeError("patient not logged in")
        session = self.db.query(Session) \
            .order_by(Session.id.desc()) \
            .join(Patient).filter(Patient.id == self.patientId) \
            .first()
        if (session is None):
            raise RuntimeError("no session recorded for patient")
        return session


    @transactional
    @remotemethod(bool, alias=str)
    def launchTest(self, alias):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        self.lastSessionId = self.getLastSessionId()
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        _log.debug("Launch test: %s" % alias)
        test_cfg = TestConfig(self.language, self.config.FEATURES)
        self.addjob("start_test", alias, patient.alias, patient.guid, test_cfg)
        vrs.metrics.track("launch", {"type" : "test", "alias" : alias})
        return True


    @transactional
    @remotemethod(bool, alias=str)
    def launchGame(self, alias):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        self.lastSessionId = self.getLastSessionId()
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        _log.debug("Launch game: %s" % alias)
        game_cfg = GameConfig(self.language, self.config.FEATURES, patient.settings_game)
        self.addjob("start_game", alias, patient.alias, patient.guid, game_cfg)
        vrs.metrics.track("launch", {"type" : "game", "alias" : alias})
        return True


    ####################################
    # Generate recent users data.
    ####################################

    @transactional
    @remotemethod([Patient])
    def listPatients(self):
        patients = self.db.query(Patient).filter(Patient.alias != "guest").filter(Patient.active == True).order_by(Patient.modified.desc()).all()
        result = []
        for p in patients:
            s = self.db.query(Session)\
                .join(Patient)\
                .filter(Patient.id == p.id)\
                .order_by(Session.modified.desc())\
                .limit(1)\
                .first()
            if s:
                result.append((p, max(p.modified, s.modified)))
            else:
                result.append((p, p.modified))
        result.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in result]


    ####################################
    # Difficulty level support.
    ####################################

    @remotemethod(dict, activityAlias=str)
    def getDifficultyLevels(self, activityAlias):
        return activities.DIFFICULTY_LEVELS[activityAlias]


    @transactional
    @remotemethod(int, activityAlias=str)
    def getCurrentDifficultyLevel(self, activityAlias):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        return patient.settings_game[activityAlias + '_level']


    @transactional
    @remotemethod(bool, activityAlias=str, level=int)
    def setDifficultyLevel(self, activityAlias, level):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        patient.settings_game[activityAlias + '_level'] = level
        self.db.commit()
        return True


    ####################################
    # High score support.
    ####################################

    @remotemethod(bool, session=Session)
    def wasLowScoring(self, session):
        return (not activities.SCORE_FILTERS[session.activity.alias](session.score))


    @transactional
    @remotemethod(bool, activityAlias=str)
    def hasPlayedBefore(self, activityAlias):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
        return self.db.query(Session)\
            .join(Activity)\
            .filter(Session.activity == activity)\
            .join(Patient)\
            .filter(Session.patient == patient)\
            .count() > 0


    @transactional
    @remotemethod([Session], activityAlias=str, maxCount=int)
    def getActivityHighscoreList(self, activityAlias, maxCount):
        if self.patientId is None:
            raise RuntimeError("patient/guest not logged in")
        if activityAlias not in activities.SCORE_SORTERS:
            return []
        patient = self.db.query(Patient).filter(Patient.id == self.patientId).one()
        activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
        sessions = self.db.query(Session)\
            .join(Activity, Patient)\
            .filter(Activity.id == activity.id)\
            .filter(Patient.id == patient.id)\
            .all()
        # 1. Filter away sessions with invalid/incomplete scores.
        result = [s for s in sessions if activities.SCORE_FILTERS[activityAlias](s.score)]
        # 2. For activities which support difficulty levels - only keep scores
        # from sessions which match the patient's current level.
        if activityAlias in activities.DIFFICULTY_LEVELS:
            level = self.getCurrentDifficultyLevel(activityAlias)
            result = [s for s in result if s.score["level"] == level]
        # 2. Order sessions to form a highscore list (sort from highest to lowest score).
        result.sort(key=lambda s: s.score, cmp=activities.SCORE_SORTERS[activityAlias])
        _log.debug("Filtered away %d/%d highscore result for activity '%s'" % (
                len(sessions) - len(result), len(sessions), activityAlias))
        # 3. Limit highscore list to N entries..
        return result[:maxCount]


    ####################################
    # Helpers.
    ####################################


    @transactional
    @remotemethod([Activity])
    def listActivities(self):
        return self.db.query(Activity).all()


    @transactional
    @remotemethod(str, alias=str)
    def getActivityKind(self, alias):
        """
        Retrieve activity kind (game|test) for ``alias`` as configured in DB
        via the ``vrs.config.activities`` module.
        """
        activity = self.db.query(Activity).filter(Activity.alias == alias).one()
        return activity.kind


    @transactional
    @remotemethod([Session], activity=Activity, patient=Patient)
    def findSessions(self, activity, patient):
        """
        Find all sessions of type ``activity`` for ``patient. Returns an array
        of sessions or an empty array if none were found.
        """
        sessions = self.db.query(Session).join(Activity, Patient).\
            filter(Activity.id == activity.id).filter(Patient.id == patient.id).all()
        return sessions



##############################################################################
# The End.
##############################################################################
