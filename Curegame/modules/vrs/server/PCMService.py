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
import datetime
import math
import logging
import time
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as orm

import vrs.locale

from vrs.as3rpc import remotemethod
from vrs.config.activities import HGT_TESTS, HGT_GAMES
from vrs.db import has_one, has_many, computed_field, computed_array
from vrs.db.utils import transactional
from vrs.server.schema import Zone, Station, Activity, Patient, Session, SyncMetaData
from vrs import SessionLog

_log = logging.getLogger('pcms')

##############################################################################
# Supporting HTTP web-service.
##############################################################################

import tornado.web

class GeneratePatientExcelHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, db):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.db = db

    def get(self):
        patient_guid = self.get_argument("patient_guid")
        patient = self.db.query(Patient).filter(Patient.guid == patient_guid).one()
        self.set_header("Content-Type", "text/plain")
        self.write(patient.alias)


##############################################################################
# Utilities.
##############################################################################

def iterfind(node, match):
    """
    Helper which either uses ElementTree.Element findall() for Python 2.6 or
    iterfind() for Python 2.7+.
    """
    try:
        return node.iterfind(match)
    except AttributeError:
        return node.findall(match)


##############################################################################
# ActivityInfo.
##############################################################################

class ActivityType(object):
    __amf_class__ = "vrs.shared.ActivityType"
    __amf_enum__  = str

    ASSESSMENT    = "test"
    TRAINING_GAME = "game"


class ActivityInfo(object):
    __amf_class__ = "vrs.shared.ActivityInfo"

    alias    = computed_field(str)
    version  = computed_field(str)
    kind     = computed_field(ActivityType)


    def __init__(self, alias=None, version=None, kind=None):
        self.alias, self.version, self.kind = alias, version, kind


    @staticmethod
    def __serialize__():
        return [ActivityInfo.alias, ActivityInfo.version, ActivityInfo.kind]


##############################################################################
# PCMService.
##############################################################################

class PCMService(object):
    __amf_service__ = "vrs.PCMService"

    def __init__(self, config, db):
        self.config = config
        self.db = db


    def _markdirty(self, patient):
        self.db.query(SyncMetaData)\
            .with_lockmode('update')\
            .filter(SyncMetaData.zone_guid == patient.zone.guid)\
            .update({SyncMetaData.need_sync: True})
        self.db.commit()


    @remotemethod(str, value=str)
    def echo(self, value):
        return value


    @remotemethod(str)
    def clock(self):
        return time.asctime()


    @remotemethod(str)
    def raiseException(self):
        raise RuntimeError("forced exception")


    @remotemethod(str)
    def getSystemLangCode(self):
        return self.config.SYSTEM_LOCALE


    @remotemethod(bool, zone_guid=str)
    def needZoneRedirect(self, zone_guid):
        try:
            (alias, password, hostname) = self.config.CUSTOMER_ZONES[zone_guid]
            return (hostname != self.config.REMOTE_HOST)
        except KeyError:
            raise RuntimeError("Unknown zone: %s" % zone_guid)


    @remotemethod(str, zone_guid=str)
    def getZoneRedirectURL(self, zone_guid):
        try:
            (alias, password, hostname) = self.config.CUSTOMER_ZONES[zone_guid]
            return "http://%s" % hostname
        except KeyError:
            raise RuntimeError("Unknown zone: %s" % zone_guid)


    @remotemethod(dict, lang=str)
    def getTranslations(self, lang):
        return vrs.locale.get_json_catalog(lang)


    @transactional
    @remotemethod(bool, p=Patient, record=dict)
    def saveMedicalRecord(self, p, record):
        """
        Replace patient ``p`` medical record with ``record``.
        """
        patient = self.db.query(Patient).filter(Patient.id == p.id).one()
        patient.medical_record = record
        patient.revision += 1
        self.db.commit()
        self._markdirty(patient)
        return True


    @transactional
    @remotemethod([Zone])
    def listZones(self):
        """
        Enumerate all zones, returns an array of zones or an empty array.
        """
        return self.db.query(Zone).order_by(Zone.alias).all()


    @transactional
    @remotemethod(bool, zone_guid=str, password=str)
    def authenticate(self, zone_guid, password):
        """
        Attempt to authenticate user trying to login to zone using
        ``password``, return True/False to signal success.
        """
        zone = self.db.query(Zone)\
            .filter(Zone.guid == zone_guid)\
            .one()
        if zone and zone.password == password:
            return True
        else:
            return False


    @transactional
    @remotemethod([Patient], zone=Zone)
    def listPatients(self, zone):
        """
        Find all patients in ``zone``. Returns an array of patients or an empty
        array if none were found.
        """
        patients = self.db.query(Patient)\
            .join(Zone).filter(Zone.id == zone.id)\
            .filter(Patient.active == True)\
            .order_by(Patient.modified.desc())\
            .all()
        for p in patients:
            # FIXME: temporary fix until background data analytics are implemented!
            p.medical_record['training_session_count'] = self.db.query(Session)\
                .join(Patient).filter(Patient.id == p.id)\
                .join(Activity).filter(Activity.kind == "game")\
                .count()
            p.medical_record['assessment_session_count'] = self.db.query(Session)\
                .join(Patient).filter(Patient.id == p.id)\
                .join(Activity).filter(Activity.kind == "test")\
                .count()
            p.medical_record['total_session_count'] = \
                p.medical_record['training_session_count'] + \
                p.medical_record['assessment_session_count']
            first_session = self.db.query(Session)\
                .join(Patient).filter(Patient.id == p.id)\
                .order_by(Session.timestamp.asc())\
                .first()
            if first_session:
                p.medical_record['first_session_date'] = first_session.timestamp
            else:
                p.medical_record['first_session_date'] = datetime.datetime(1970, 1, 1)
            latest_session = self.db.query(Session)\
                .join(Patient).filter(Patient.id == p.id)\
                .order_by(Session.timestamp.desc())\
                .first()
            if latest_session:
                p.medical_record['latest_session_date'] = latest_session.timestamp
            else:
                p.medical_record['latest_session_date'] = datetime.datetime(1970, 1, 1)
        patients = sorted(patients, reverse=True, key=lambda(p): p.medical_record['latest_session_date'])
        # FIXME: temporary fix to filter out redundant (legacy) guest accounts,
        # there should only one guest account per zone.
        return [p for p in patients if (p.alias != "guest" or p.guid == zone.guid)]


    @transactional
    @remotemethod(bool, patient_guid=str)
    def deactivatePatient(self, patient_guid):
        """
        Deactivate a patient making him/her not visible externally.
        """
        p = self.db.query(Patient)\
            .filter(Patient.guid == patient_guid)\
            .one()
        if p and p.alias != "guest":
            p.active = False
            p.pincode = "inactive_%s_%s" % (p.pincode, p.guid)
            p.revision += 1
            self.db.commit()
            self._markdirty(p)
            return True
        else:
            return False


    @remotemethod([ActivityInfo])
    def listActivities(self):
        """
        Return a list of all available assessments and training games.
        """
        result = []
        for db in [HGT_TESTS, HGT_GAMES]:
            for (alias, info) in db.iteritems():
                (path, x3d, version, kind, guid) = info
                result.append(ActivityInfo(alias, version, kind))
        return result


    @remotemethod([ActivityInfo])
    def listAssessments(self):
        """
        Return a list of all available assessments.
        """
        result = []
        for (alias, info) in HGT_TESTS.iteritems():
            (path, x3d, version, kind, guid) = info
            result.append(ActivityInfo(alias, version, kind))
        return result


    @transactional
    @remotemethod([Session], patient=Patient)
    def findSessions(self, patient):
        """
        Find all sessions for ``patient``. Returns an array of sessions or an
        empty array if none were found.
        """
        sessions = self.db.query(Session)\
            .options(orm.undefer('score'))\
            .options(orm.eagerload('zone'))\
            .options(orm.eagerload('activity'))\
            .options(orm.eagerload('patient'))\
            .join(Patient).filter(Patient.id == patient.id)\
            .order_by(Session.timestamp.desc())\
            .limit(500).all()
        return sessions


    @transactional
    @remotemethod([Session], patient=Patient, activityAlias=str)
    def findActivitySessions(self, patient, activityAlias):
        """
        Find all sessions for ``patient`` of activity type ``activityAlias``
        Returns an array of sessions or an empty array if none were found.
        """
        activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
        sessions = self.db.query(Session)\
            .options(orm.undefer('score'))\
            .options(orm.eagerload('zone'))\
            .options(orm.eagerload('activity'))\
            .options(orm.eagerload('patient'))\
            .join(Patient).filter(Patient.id == patient.id)\
            .join(Activity).filter(Session.activity == activity)\
            .order_by(Session.timestamp.desc())\
            .limit(500).all()
        return sessions


    @transactional
    @remotemethod(bool, guid=str)
    def deleteSession(self, guid):
        """
        Delete training/assessment session identified via ``guid``, return True
        on success.
        """
        session = self.db.query(Session).filter(Session.guid == guid).first()
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        else:
            return False


    @transactional
    @remotemethod([], patient=Patient, activityAlias=str, ndays=int)
    def groupSessionsByDay(self, patient, activityAlias, ndays):
        """
        Group all sessions for ``patient`` max ``ndays`` old (passing 0 means
        all matching sessions) of activity type ``activityAlias`` (passing "*"
        means all types of activities). Returns an array of dicts which map
        dates to arrays of sessions which were recording during that day. If
        ``ndays`` is > 0 we'll "fill in the blanks" so that interleaving days
        where no sessions were recorded are also included in the result:

          result = [
             {"date" : Date(2010,8,23), "sessions" : [s1, s2, s3, ...]},
             {"date" : Date(2010,8,22), "sessions" : []},
             {"date" : Date(2010,8,21), "sessions" : [s4, s5, s6, ...]},
          ]

        """
        today = datetime.datetime.utcnow()
        day_sessions = {}

        query = self.db.query(Session)\
            .options(orm.undefer('score'))\
            .options(orm.eagerload('zone'))\
            .options(orm.eagerload('activity'))\
            .options(orm.eagerload('patient'))\
            .join(Patient).filter(Patient.id == patient.id)

        if activityAlias != "*":
            activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
            query = query.join(Activity).filter(Session.activity == activity)

        if ndays > 0:
            for n in range(ndays):
                date = today - datetime.timedelta(n)
                day_sessions[datetime.datetime(date.year, date.month, date.day)] = []
            query = query.filter(Session.timestamp >= today - datetime.timedelta(ndays))

        query = query\
            .order_by(Session.timestamp)

        for row in query:
            date = datetime.datetime(row.timestamp.year, row.timestamp.month, row.timestamp.day)
            day_sessions.setdefault(date, []).append(row)

        result = []
        for day in sorted(day_sessions.keys()):
            result.append({"date":day, "sessions":day_sessions[day]})
        return result


    @transactional
    @remotemethod([], patient=Patient, activityAlias=str, nmonths=int)
    def groupSessionsByMonth(self, patient, activityAlias, nmonths):
        """
        Group all sessions for ``patient`` max ``nmonths`` old (passing 0 means
        all matching sessions) of activity type ``activityAlias`` (passing "*"
        means all types of activities). Returns an array of dicts which map
        dates to arrays of sessions which were recording during that month.  If
        ``nmonths`` is > 0 we'll "fill in the blanks" so that interleaving
        months where no sessions were recorded are also included in the result:

          result = [
             {"date" : Date(2010,8,1), "sessions" : [s1, s2, s3, ...]},
             {"date" : Date(2010,7,1), "sessions" : []},
             {"date" : Date(2010,6,1), "sessions" : [s4, s5, s6, ...]},
          ]

        """
        today = datetime.datetime.utcnow()
        this_month = datetime.datetime(today.year, today.month, 1)
        month_sessions = {}

        query = self.db.query(Session)\
            .options(orm.undefer('score'))\
            .options(orm.eagerload('zone'))\
            .options(orm.eagerload('activity'))\
            .options(orm.eagerload('patient'))\
            .join(Patient).filter(Patient.id == patient.id)

        if activityAlias != "*":
            activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
            query = query.join(Activity).filter(Session.activity == activity)

        if nmonths > 0:
            last_month = this_month
            for n in range(nmonths):
                month_sessions[last_month] = []
                year, month= last_month.year, last_month.month
                if month == 1:
                    year -= 1
                    month = 12
                else:
                    month -= 1
                last_month = datetime.datetime(year=year, month=month, day=1)
            query = query.filter(Session.timestamp >= last_month)

        query = query\
            .order_by(Session.timestamp)

        for row in query:
            date = datetime.datetime(row.timestamp.year, row.timestamp.month, 1)
            month_sessions.setdefault(date, []).append(row)

        result = []
        for date in sorted(month_sessions.keys()):
            result.append({"date":date, "sessions": month_sessions[date]})
        return result


    @transactional
    @remotemethod([], patient=Patient, activityAlias=str, nweeks=int)
    def groupSessionsByWeek(self, patient, activityAlias, nweeks):
        """
        Group all sessions for ``patient`` max ``nweeks`` old (passing 0 means
        all matching sessions) of activity type ``activityAlias`` (passing "*"
        means all types of activities). Returns an array of dicts which map
        dates to arrays of sessions which were recording during that week.  If
        ``nweeks`` is > 0 we'll "fill in the blanks" so that interleaving weeks
        where no sessions were recorded are also included in the result:

          result = [
             {"date" : Date(2010,8, 1), "sessions" : [s1, s2, s3, ...]},
             {"date" : Date(2010,8, 7), "sessions" : []},
             {"date" : Date(2010,8,14), "sessions" : [s4, s5, s6, ...]},
          ]

        """
        today = datetime.datetime.utcnow()
        week_sessions = {}

        query = self.db.query(Session)\
            .options(orm.undefer('score'))\
            .options(orm.eagerload('zone'))\
            .options(orm.eagerload('activity'))\
            .options(orm.eagerload('patient'))\
            .join(Patient).filter(Patient.id == patient.id)

        if activityAlias != "*":
            activity = self.db.query(Activity).filter(Activity.alias == activityAlias).one()
            query = query.join(Activity).filter(Session.activity == activity)

        if nweeks > 0:
            start_week = today - datetime.timedelta(days=today.weekday())
            start_week = datetime.datetime(start_week.year, start_week.month, start_week.day, 0, 0, 0)
            end_week = start_week + datetime.timedelta(6)
            end_week = datetime.datetime(end_week.year, end_week.month, end_week.day, 23, 59, 59)
            for n in range(nweeks):
                assert start_week.isocalendar()[1] == end_week.isocalendar()[1]
                week_sessions[start_week] = []
                start_week -= datetime.timedelta(7)
                end_week -= datetime.timedelta(7)
            query = query.filter(Session.timestamp >= start_week)

        query = query\
            .order_by(Session.timestamp)

        for row in query:
            start_week = row.timestamp - datetime.timedelta(days=row.timestamp.weekday())
            start_week = datetime.datetime(start_week.year, start_week.month, start_week.day, 0, 0, 0)
            week_sessions.setdefault(start_week, []).append(row)

        result = []
        for date in sorted(week_sessions.keys()):
            result.append({"date": date, "week": date.isocalendar()[1], "sessions": week_sessions[date]})
        return result


    @transactional
    @remotemethod(dict, session=Session)
    def getAssessmentData(self, session):
        """
        Load raw XML data for ``session`` log from local S3 cache. Preprocess
        and organize data straight into a dict (AS3 ObjectProxy) which can be
        easily transformed and processed on the Flex/AS3 side.

        The returned data will roughly contain the following:

        data = {
          duration  -> str   (parse as float secs)
          timestamp -> str   (parse as float unix timestamp)
          distance  -> float (total distance in meters between first and last event)
          vars      -> array of {'key':'value'}
          transform -> array of floats (16 values, 4x4 calibration matrix)
          f_max     -> float (max force)
          v_max     -> float (max velocity)
          v_avg     -> float (average velocity)
          v_std     -> float (standard deviation)
          v_cof     -> float (variance cooficient)
          a_max     -> float (max acceleration)
          a_min     -> float (min acceleration)
          events     -> array of {
                          description -> str
                          id          -> str
                          distance    -> float (in meters)
                          timestamp   -> float (unix timestamp)
                          x, y, z     -> float (in meters)
                        ]
          kinematics -> array of {
                          timestamp     -> float (unix timestamp)
                          a             -> float   (acceleration)
                          f             -> float   (force)
                          v             -> float   (velocity)
                          o_a           -> float (orientation angle)
                          o_x, o_y, o_z -> float (orientation components)
                          f_x, f_y, f_z -> float (force components)
                          p_x, p_y, p_z -> float (postition components)
                          v_x, v_y, v_z -> float (velocity components)
                        }
        }
        """
        filepath = os.path.join(os.environ["CUREGAME_TEMPPATH"], self.config.S3_UPLOAD_DIR, "session", session.zone.guid, session.guid + ".xml")
        if not os.path.exists(filepath):
            raise RuntimeError("Session log '%s' not found in local S3 cache" % session.guid)

        log = SessionLog.load(filepath, password=self.config.SESSION_SECRET, zip=False)

        result = {}
        result["duration"] = log.duration
        result["timestamp"] = log.timestamp
        result["events"] = []
        result["kinematics"] = []

        # Look for `assessment_vars`` in in the info event stream and merge
        # them with regular score key/value pairs if available.
        result["vars"] = [{"key":k, "value":v} for (k,v) in log.score.iteritems()]
        for e in iterfind(log.activitylog, "info"):
            if e.get("id", None) == "assessment_vars":
                for value in e.findall('value'):
                    result["vars"].append({"key":value.attrib["key"], "value":value.text})
                break
        else:
            _log.warning("Session log '%s' missing assessment vars" % (session.guid))


        # Turn activity event nodes into a single row { attr -> type(value) }
        #
        # <activity...>
        #  <event description="Pointtest initialized" distance="0.00530250" id="init" timestamp="0.37040234">
        #    <position x="0.10004823" y="-0.01913913" z="0.02860839" />
        #  </event>
        #  ...
        # </activity>
        #
        # {'distance': 0.0053025, 'description': 'Pointtest initialized', 'timestamp': 0.37040234,
        #  'y': -0.01913913, 'x': 0.10004823, 'z': 0.02860839, 'id': 'init'}

        for e in iterfind(log.activitylog, "event"):
            row = {}
            for (attr, klass) in [("description", str),
                                  ("id",          str),
                                  ("distance",    float),
                                  ("timestamp",   float)]:
                row[attr] = klass(e.attrib[attr])
            pos = e.find('position')
            for attr in ["x", "y", "z"]:
                row[attr] = float(pos.attrib[attr])
            result["events"].append(row)

        # Try to deduce overall distance travelled from last event logged (if availabe).
        if result["events"]:
            result["distance"] = result["events"][-1]["distance"]
        else:
            result["distance"] = 0

        # Determine time range between first and last recorded events. We'll
        # filter away all kinematics data which is timestamped outside of this
        # range in order to minimize noise in our visualizations

        if len(result["events"]) > 2:
            first_event_t = result["events"][0]["timestamp"]
            last_event_t = result["events"][-1]["timestamp"]
            assert first_event_t < last_event_t
        else:
            first_event_t = 0
            last_event_t  = 1000

        # Parse kinematics calibration matrix4x4 (including orientation):
        #
        # <calibration>
        #   <position>1.08196998,0.00554412,-0.03099590,0.00000000,0.01432350,0.70215201,0.83249998,0.00000000,0.04862210,-0.82620502,0.44848901,0.00000000,-0.00175221,-0.02326860,-0.00790408,1.00000000</position>
        #   ...
        # </calibration>

        calibration = log.kinematicslog.find("calibration")
        if calibration:
            transform = [float(e.strip()) for e in calibration.find("position").text.split(",")]
            assert len(transform) == 16
            result["transform"] = transform

        # Turn kinematics event nodes into a flattened single row { attr -> type(value) }
        #
        # <kinematics>
        #  <event timestamp="0.01753163">
        #    <position x="0.10358691" y="-0.01842573" z="0.02752774" />
        #    <orientation a="0.48969987" x="-0.98590605" y="0.09786149" z="0.13569226" />
        #    <force x="0.00000000" y="-0.00000000" z="0.00000000" />
        #    <velocity x="-0.01864182" y="-0.00931457" z="0.00975677" />
        #  </event>
        # ...
        # </kinematics>
        #
        # {'v_y': -0.00931457, 'v_x': -0.01864182, 'timestamp': '0.01753163', 'o_y': 0.09786149,
        #  'o_x': -0.98590605, 'v_z': 0.00975677, 'o_z': 0.13569226, 'p_z': 0.02752774, 'p_x': 0.10358691,
        #  'p_y': -0.01842573, 'o_a': 0.48969987, 'f_x': 0.0, 'f_y': -0.0, 'f_z': 0.0}


        forces, velocities, accelerations = [], [], []

        if float(log.duration) > 60:
            KINEMATICS_GRANULARITY_SEC = 0.066 # 15Hz
        else:
            KINEMATICS_GRANULARITY_SEC = 0.025 # 40Hz

        window = []
        for e in iterfind(log.kinematicslog, "event"):
            row = {}
            row["timestamp"] = float(e.attrib["timestamp"])
            if row["timestamp"] < first_event_t or row["timestamp"] > last_event_t:
                continue
            for (name, prefix, sub_attrs) in [("position",    "p_", ["x", "y", "z"     ]),
                                              ("orientation", "o_", ["x", "y", "z", "a"]),
                                              ("force",       "f_", ["x", "y", "z"     ]),
                                              ("velocity",    "v_", ["x", "y", "z"     ])]:
                node = e.find(name)
                for attr in sub_attrs:
                    row[prefix + attr] = float(node.attrib[attr])
            row["f"] = math.sqrt(row["f_x"]**2 + row["f_y"]**2 + row["f_z"]**2)
            row["v"] = math.sqrt(row["v_x"]**2 + row["v_y"]**2 + row["v_z"]**2)

            # We'll dynamically downsample on-the-go using a sliding window to
            # average out force/velocity components.
            if not window:
                window = [row]
            elif (row["timestamp"] - window[0]["timestamp"]) < KINEMATICS_GRANULARITY_SEC:
                window.append(row)
                continue

            last_row = window[-1]
            for prefix in ["f_", "v_"]:
                for axis in ["x", "y", "z"]:
                    key = prefix + axis
                    last_row[key] = sum([w[key] for w in window]) / len(window)
            last_row["f"] = sum([w["f"] for w in window]) / len(window)
            last_row["v"] = sum([w["v"] for w in window]) / len(window)

            if last_row:
                dt = row["timestamp"] - last_row["timestamp"]
                if dt > 0:
                    row["a"] = (row["v"] - last_row["v"]) / dt;
                else:
                    row["a"] = 0
            else:
                row["a"] = 0

            forces.append(row["f"])
            velocities.append(row["v"])
            accelerations.append(row["a"])
            result["kinematics"].append(row)
            window = [row]

        # Calculate handy global stats, specialized analysis needs to be
        # performed by clients since they most likely need to parse the event
        # stream anyway.

        v_avg = sum(velocities) / len(velocities)
        v_std = math.sqrt(sum([(v - v_avg) ** 2 for v in velocities]) / (len(velocities) - 1))

        result["f_max"] = max(forces)
        result["v_max"] = max(velocities)
        result["v_avg"] = v_avg
        result["v_std"] = v_std
        result["v_cof"] = v_std / abs(v_avg)
        result["a_max"] = max(accelerations)
        result["a_min"] = min(accelerations)

        return dict(result)


##############################################################################
# The End.
##############################################################################
