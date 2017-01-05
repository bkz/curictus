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

import gzip
import time
import xml.etree.cElementTree as ET
import uuid

from util import crypto

###########################################################################
# Utilities.
###########################################################################

def indent(elem, level=0):
    """
    Destructively modifies a ElementTree by adding whitespace, so that saving
    it as usual results in a prettyprinted tree.
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


###########################################################################
# SessionLog
###########################################################################

# The XML file format output by ``SessionLog`` is documented in SessionLog.xml
# which is located in the same directory as this file.

class SessionLog(object):
    def __init__(self, config, patient_alias, patient_guid, timestamp, duration):
        self.guid = str(uuid.uuid1())
        self.root = ET.Element("session")
        self.root.set("timestamp", str(timestamp))
        self.root.set("duration", str(duration))
        self.root.set("version", config.SYSTEM_VERSION)
        self.root.set("guid", self.guid)
        self.root.append(ET.Comment("Generated: %s" % time.asctime()))
        self.zone = ET.SubElement(self.root, "zone")
        self.zone.set("alias", "default")
        self.zone.set("guid", config.ZONE_GUID)
        self.station = ET.SubElement(self.root, "station")
        self.station.set("alias", "default");
        self.station.set("guid", config.STATION_GUID)
        self.patient = ET.SubElement(self.root, "patient")
        self.patient.set("alias", patient_alias)
        self.patient.set("guid", patient_guid)
        self.hardware = ET.SubElement(self.root, "hardware")

    def set_hardware(self, rawxml):
        for child in ET.fromstring("<root>" + rawxml + "</root>"):
            self.hardware.append(child)

    def set_activitylog(self, alias, kind, version, guid, rawxml=None):
        log = ET.SubElement(self.root, "activity")
        log.set("alias", alias)
        log.set("kind", kind)
        log.set("version", version)
        log.set("guid", guid)
        if rawxml:
            for child in ET.fromstring("<root>" + rawxml + "</root>"):
                log.append(child)

    def set_kinematicslog(self, rawxml):
        log = ET.SubElement(self.root, "kinematics")
        if rawxml:
            for child in ET.fromstring("<root>" + rawxml + "</root>"):
                log.append(child)

    def set_analysislog(self, rawxml=None):
        log = ET.SubElement(self.root, "analysis")
        if rawxml:
            for child in ET.fromstring("<root>" + rawxml + "</root>"):
                log.append(child)

    def toxml(self):
        indent(self.root)
        return ET.tostring(self.root, encoding='utf-8')

    def write(self, filename, password=None, zip=True):
        data = self.toxml()
        if password:
            data = crypto.encrypt(data, password)
        if zip:
            gzip.open(filename, "wb").write(data)
        else:
            open(filename, "wb").write(data)


###########################################################################
# Import existings session logs.
###########################################################################

class SessionLogRO(object):
    """
    Read-only wrapper around an ElementTree for the SessionLog XML format.
    """
    def __init__(self, root):
        self.root             = root
        self.zone             = self.root.find('zone')
        self.station          = self.root.find('station')
        self.patient          = self.root.find('patient')
        self.hardware         = self.root.find('hardware')
        self.activitylog      = self.root.find('activity')
        self.kinematicslog    = self.root.find('kinematics')
        self.analysislog      = self.root.find('analysis')
        self.score            = self._parse_score()
        self.timestamp        = self.root.get("timestamp")
        self.duration         = self.root.get("duration")
        self.version          = self.root.get("version")
        self.guid             = self.root.get("guid")
        self.zone_alias       = self.zone.get("alias")
        self.zone_guid        = self.zone.get("guid")
        self.station_alias    = self.station.get("alias")
        self.station_guid     = self.station.get("guid")
        self.patient_alias    = self.patient.get("alias")
        self.patient_guid     = self.patient.get("guid")
        self.activity_alias   = self.activitylog.get("alias")
        self.activity_kind    = self.activitylog.get("kind")
        self.activity_version = self.activitylog.get("version")
        self.activity_guid    = self.activitylog.get("guid")


    def get_activitylog_xml(self):
        return ET.tostring(self.activitylog)

    def get_kinematicslog_xml(self):
        return ET.tostring(self.kinematicslog)

    def get_analysislog_xml(self):
        return ET.tostring(self.analysislog)

    def get_hardware_xml(self):
        return ET.tostring(self.hardware)

    def _parse_score(self):
        result = {}
        try:
            for value in self.activitylog.find('score').findall('value'):
                result[value.get('key')] = value.text
        except AttributeError:
            pass
        return result

    def toxml(self):
        indent(self.root)
        return ET.tostring(self.root, encoding='utf-8')

    def write(self, filename, password=None, zip=True):
        data = self.toxml()
        if password:
            data = crypto.encrypt(data, password)
        if zip:
            gzip.open(filename, "wb").write(data)
        else:
            open(filename, "wb").write(data)


def load(filename, password=None, zip=True):
    """
    Load previously (compressed if ``zip``) SessionLog XML data from
    ``filename`` and return an SessionLogRO instance for it. A ``password`` can
    optionally be passed if data was written in an encrypted fashion. (For
    information about the XML structure see the documentation for the
    SeesionLog class).

    NOTE: parse errors will be reported back as ``IOError`` to keep error
    handling clean and simple, detailed errors are useless since manual
    inspection needed anyways to determine cause of corruption.
    """
    if zip:
        data = gzip.open(filename, "rb").read()
    else:
        data = open(filename, "rt").read()
    if password:
        data = crypto.decrypt(data, password)
    try:
        return SessionLogRO(ET.fromstring(data))
    except Exception, e:
        raise IOError("Corrupt session log")


###########################################################################
# Unit test.
###########################################################################

if __name__ == '__main__':
    log = load("SessionLog.xml", zip=False)
    assert log.score["time"] == "42.5"


###########################################################################
# The End.
###########################################################################
